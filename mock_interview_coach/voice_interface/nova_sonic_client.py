"""Nova Sonic Client — real bidirectional streaming via aws-sdk-bedrock-runtime.

Uses the experimental AWS SDK (awslabs/aws-sdk-python) which is the ONLY Python SDK
that supports InvokeModelWithBidirectionalStream.  boto3 does NOT support this API.
"""

import os
import asyncio
import base64
import json
import logging
import uuid
from typing import Optional, Callable, Awaitable
from dotenv import load_dotenv

from mock_interview_coach.models import Language
from mock_interview_coach.voice_interface.mock_audio_generator import MockAudioGenerator

load_dotenv()
logger = logging.getLogger(__name__)


class NovaSonicClient:
    """Bidirectional streaming client for Amazon Nova Sonic.

    Wraps the aws-sdk-bedrock-runtime experimental SDK.
    Falls back to MockAudioGenerator when ENABLE_DEV_MODE=true.
    """

    MODEL_ID = "amazon.nova-sonic-v1:0"

    # System prompt tailored for mock interview coach
    SYSTEM_PROMPT_EN = (
        "You are Nova, an expert technical interviewer for cloud, DevOps, and ML engineer roles. "
        "You ask one focused technical question at a time, listen carefully to the candidate's answer, "
        "and give brief, constructive spoken feedback (2-3 sentences max). "
        "Be professional but encouraging. Speak naturally — this is a real-time voice interview."
    )

    SYSTEM_PROMPT_ES = (
        "Eres Nova, un entrevistador técnico experto para roles de Cloud, DevOps e ingeniería ML. "
        "Haces una pregunta técnica a la vez, escuchas con atención la respuesta del candidato "
        "y das retroalimentación breve y constructiva (máximo 2-3 oraciones). "
        "Sé profesional pero alentador. Habla con naturalidad — esto es una entrevista de voz en tiempo real."
    )

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.model_id = model_id or os.getenv("NOVA_SONIC_MODEL_ID", self.MODEL_ID)
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.dev_mode = os.getenv("ENABLE_DEV_MODE", "false").lower() == "true"

        self._bedrock_client = None   # lazy-init (requires credentials)
        self.mock_audio_generator = MockAudioGenerator() if self.dev_mode else None

    # ── Public helpers (used by app.py health check / startup) ────────────

    def get_model_id(self) -> str:
        return self.model_id

    def get_region(self) -> str:
        return self.region

    def validate_model_availability(self) -> bool:
        if self.dev_mode:
            return True
        try:
            import boto3
            # sts:GetCallerIdentity works with any valid credentials —
            # no explicit IAM permission required.
            boto3.client("sts", region_name=self.region).get_caller_identity()
            return bool(self.model_id)
        except Exception as e:
            logger.warning(f"validate_model_availability failed: {e}")
            return False

    async def health_check(self) -> bool:
        return self.validate_model_availability()

    # ── SDK client (lazy) ─────────────────────────────────────────────────

    def _get_bedrock_client(self):
        if self._bedrock_client is not None:
            return self._bedrock_client

        from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient
        from aws_sdk_bedrock_runtime.config import Config
        from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
        )
        self._bedrock_client = BedrockRuntimeClient(config=config)
        return self._bedrock_client

    # ── Session (one per interview question exchange) ─────────────────────

    def create_session(self, language: str = "en") -> "NovaSonicSession":
        """Create a new streaming session for one interview exchange."""
        system_prompt = (
            self.SYSTEM_PROMPT_ES if language == "es" else self.SYSTEM_PROMPT_EN
        )
        return NovaSonicSession(
            client=self._get_bedrock_client(),
            model_id=self.model_id,
            system_prompt=system_prompt,
            language=language,
        )

    # ── TTS via Amazon Polly (Nova Sonic is speech→speech, not text→speech) ─

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en",
        session_id: Optional[str] = None,
    ) -> Optional[bytes]:
        """Synthesize speech using Amazon Polly.

        Nova Sonic requires audio input to produce audio output (speech-to-speech
        model). For TTS of interview questions we use Polly instead — same AWS
        region, no extra credentials needed.

        Returns MP3 bytes, or None on failure.
        """
        if self.dev_mode:
            return self.mock_audio_generator.get_mock_audio(text, Language.ENGLISH)

        try:
            import boto3
            # Polly voice: English → Matthew, Spanish → Lucia
            voice_id = "Lucia" if language == "es" else "Matthew"
            polly = boto3.client("polly", region_name=self.region)
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=voice_id,
                Engine="neural",
            )
            audio_bytes = response["AudioStream"].read()
            return audio_bytes if audio_bytes else None

        except Exception as e:
            logger.warning(f"synthesize_speech (Polly) failed: {e}")
            return None

    # ── Simple one-shot STT (legacy path, not used in streaming mode) ─────

    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "pcm",
        session_id: Optional[str] = None,
    ) -> str:
        """Transcribe audio (non-streaming fallback).

        In real deployment the frontend streams via WebSocket + NovaSonicSession.
        This method is kept for compatibility with tests.
        """
        if self.dev_mode:
            return self.mock_audio_generator.get_mock_transcription(audio_data)

        try:
            session = self.create_session()
            result = await session.run_stt(audio_data=audio_data)
            return result or ""
        except Exception as e:
            logger.warning(f"transcribe_audio failed: {e}")
            return ""


# ── NovaSonicSession ──────────────────────────────────────────────────────────

class NovaSonicSession:
    """One bidirectional streaming session with Nova Sonic.

    Lifecycle:
        session = client.create_session(language)
        await session.open()
        await session.send_audio_chunk(pcm_bytes)   # repeat
        await session.close()
        # session.transcript  → str
        # session.audio_out   → bytes (LPCM 24kHz)
    """

    VOICE_EN = "matthew"
    VOICE_ES = "pedro"

    def __init__(
        self,
        client,
        model_id: str,
        system_prompt: str,
        language: str = "en",
    ):
        self._client = client
        self._model_id = model_id
        self._system_prompt = system_prompt
        self._language = language

        self._stream = None
        self._response_task: Optional[asyncio.Task] = None
        self.is_active = False

        self._prompt_name = str(uuid.uuid4())
        self._content_name = str(uuid.uuid4())
        self._audio_content_name = str(uuid.uuid4())

        # Output collectors
        self.transcript: str = ""          # USER transcript
        self.assistant_text: str = ""      # ASSISTANT text
        self.audio_out: bytes = b""        # LPCM 24 kHz audio

        # Callbacks (optional)
        self.on_transcript: Optional[Callable[[str], None]] = None
        self.on_assistant_text: Optional[Callable[[str], None]] = None
        self.on_audio_chunk: Optional[Callable[[bytes], None]] = None

        # Internal state
        self._role: str = ""
        self._display_assistant_text = False
        self._audio_output_queue: asyncio.Queue = asyncio.Queue()

    # ── Event helpers ──────────────────────────────────────────────────────

    async def _send(self, payload: str):
        from aws_sdk_bedrock_runtime.models import (
            InvokeModelWithBidirectionalStreamInputChunk,
            BidirectionalInputPayloadPart,
        )
        chunk = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=payload.encode("utf-8"))
        )
        await self._stream.input_stream.send(chunk)

    # ── Open / close ──────────────────────────────────────────────────────

    async def open(self):
        """Open bidirectional stream and send session/prompt/system events."""
        from aws_sdk_bedrock_runtime.client import (
            InvokeModelWithBidirectionalStreamOperationInput,
        )

        self._stream = await self._client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(model_id=self._model_id)
        )
        self.is_active = True

        # Start consuming responses in background
        self._response_task = asyncio.create_task(self._consume_responses())

        # 1 — sessionStart
        await self._send(json.dumps({
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": 1024,
                        "topP": 0.9,
                        "temperature": 0.7,
                    }
                }
            }
        }))

        # 2 — promptStart
        voice = self.VOICE_ES if self._language == "es" else self.VOICE_EN
        await self._send(json.dumps({
            "event": {
                "promptStart": {
                    "promptName": self._prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 24000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "voiceId": voice,
                        "encoding": "base64",
                        "audioType": "SPEECH",
                    },
                }
            }
        }))

        # 3 — system prompt (TEXT content)
        await self._send(json.dumps({
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": self._content_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "SYSTEM",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        }))

        await self._send(json.dumps({
            "event": {
                "textInput": {
                    "promptName": self._prompt_name,
                    "contentName": self._content_name,
                    "content": self._system_prompt,
                }
            }
        }))

        await self._send(json.dumps({
            "event": {
                "contentEnd": {
                    "promptName": self._prompt_name,
                    "contentName": self._content_name,
                }
            }
        }))

    async def start_audio_input(self):
        """Signal that audio chunks will follow."""
        await self._send(json.dumps({
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": self._audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64",
                    },
                }
            }
        }))

    async def send_audio_chunk(self, pcm_bytes: bytes):
        """Send one PCM chunk (16 kHz, 16-bit, mono)."""
        if not self.is_active:
            return
        await self._send(json.dumps({
            "event": {
                "audioInput": {
                    "promptName": self._prompt_name,
                    "contentName": self._audio_content_name,
                    "content": base64.b64encode(pcm_bytes).decode("utf-8"),
                }
            }
        }))

    async def end_audio_input(self):
        await self._send(json.dumps({
            "event": {
                "contentEnd": {
                    "promptName": self._prompt_name,
                    "contentName": self._audio_content_name,
                }
            }
        }))

    async def close(self):
        """End session and close stream."""
        if not self.is_active:
            return
        try:
            await self._send(json.dumps({
                "event": {"promptEnd": {"promptName": self._prompt_name}}
            }))
            await self._send(json.dumps({"event": {"sessionEnd": {}}}))
            await self._stream.input_stream.close()
        except Exception as e:
            logger.warning(f"Error closing Nova Sonic session: {e}")
        finally:
            self.is_active = False
            if self._response_task and not self._response_task.done():
                self._response_task.cancel()

    # ── Response consumer ──────────────────────────────────────────────────

    async def _consume_responses(self):
        try:
            from aws_sdk_bedrock_runtime.models import (
                InvokeModelWithBidirectionalStreamOutputChunk,
            )

            # await_output() MUST be called once to get the output stream
            _, output_stream = await self._stream.await_output()

            async for event in output_stream:
                try:
                    if not isinstance(event, InvokeModelWithBidirectionalStreamOutputChunk):
                        if hasattr(event, "message"):
                            logger.error(f"Nova Sonic stream error: {event.message}")
                        continue

                    if not (event.value and event.value.bytes_):
                        continue

                    data = json.loads(event.value.bytes_.decode("utf-8"))
                    ev = data.get("event", {})

                    if "contentStart" in ev:
                        self._role = ev["contentStart"].get("role", "")
                        add = ev["contentStart"].get("additionalModelFields", "")
                        if add:
                            try:
                                self._display_assistant_text = (
                                    json.loads(add).get("generationStage") == "SPECULATIVE"
                                )
                            except Exception:
                                pass

                    elif "textOutput" in ev:
                        text = ev["textOutput"].get("content", "")
                        role = ev["textOutput"].get("role", self._role)
                        if role == "USER":
                            self.transcript += text
                            if self.on_transcript:
                                self.on_transcript(text)
                        elif role == "ASSISTANT" and self._display_assistant_text:
                            self.assistant_text += text
                            if self.on_assistant_text:
                                self.on_assistant_text(text)

                    elif "audioOutput" in ev:
                        chunk = base64.b64decode(ev["audioOutput"]["content"])
                        self.audio_out += chunk
                        await self._audio_output_queue.put(chunk)
                        if self.on_audio_chunk:
                            self.on_audio_chunk(chunk)

                    elif "completionEnd" in ev:
                        break

                except Exception as e:
                    if "ValidationException" in str(e):
                        logger.error(f"Nova Sonic validation error: {e}")
                    else:
                        logger.warning(f"Nova Sonic response error: {e}")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Nova Sonic consume_responses fatal error: {e}")
        finally:
            self.is_active = False

    # ── Convenience one-shot methods ───────────────────────────────────────

    async def run_tts(self, text: str, on_audio_chunk: Callable[[bytes], None]):
        """Open session, send a text message as USER, collect audio response, close."""
        self.on_audio_chunk = on_audio_chunk
        await self.open()

        # Send text as USER message
        text_name = str(uuid.uuid4())
        await self._send(json.dumps({
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": text_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "USER",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        }))
        await self._send(json.dumps({
            "event": {
                "textInput": {
                    "promptName": self._prompt_name,
                    "contentName": text_name,
                    "content": text,
                }
            }
        }))
        await self._send(json.dumps({
            "event": {
                "contentEnd": {
                    "promptName": self._prompt_name,
                    "contentName": text_name,
                }
            }
        }))

        # Wait for audio to finish (completionEnd or timeout)
        try:
            await asyncio.wait_for(
                self._wait_for_completion(),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.warning("run_tts: timeout waiting for audio")

        await self.close()

    async def run_stt(self, audio_data: bytes) -> str:
        """Open session, stream audio, return transcript."""
        await self.open()
        await self.start_audio_input()

        # Send in 3200-byte chunks (100ms @ 16kHz 16-bit mono)
        chunk_size = 3200
        for i in range(0, len(audio_data), chunk_size):
            await self.send_audio_chunk(audio_data[i:i + chunk_size])
            await asyncio.sleep(0.01)

        await self.end_audio_input()

        try:
            await asyncio.wait_for(self._wait_for_completion(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning("run_stt: timeout waiting for transcript")

        await self.close()
        return self.transcript

    async def _wait_for_completion(self):
        """Wait until the response task finishes."""
        if self._response_task:
            try:
                await self._response_task
            except asyncio.CancelledError:
                pass
