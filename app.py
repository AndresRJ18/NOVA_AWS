"""FastAPI application for Mock Interview Coach."""

import os
import sys
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import json

from mock_interview_coach.session_manager import SessionManager
from mock_interview_coach.models import Role, Level, Language
from mock_interview_coach.auth.cognito import (
    is_cognito_configured,
    validate_token,
    exchange_code_for_tokens,
)
from mock_interview_coach.auth.dynamo_store import upsert_user, save_session_record, get_user_sessions as _get_user_sessions


async def validate_nova_sonic_on_startup():
    """Validate Nova Sonic connectivity on application startup.
    
    In production mode: Logs error if Nova Sonic is unavailable.
    In dev mode: Skips validation and uses mock audio.
    
    Note: For Vercel deployments, this runs when the serverless function
    initializes. The server will start regardless, but the health endpoint
    will report degraded status if Nova Sonic is unavailable.
    """
    from mock_interview_coach.voice_interface import NovaSonicClient
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if dev mode is enabled
    dev_mode = os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true'
    
    if dev_mode:
        logger.info("🔧 Development mode enabled - using mock audio")
        logger.info("   Nova Sonic validation skipped")
        return
    
    logger.info("🔍 Validating Nova Sonic connectivity...")
    
    try:
        client = NovaSonicClient()
        is_available = client.validate_model_availability()
        
        if is_available:
            logger.info("✅ Nova Sonic is available")
            logger.info(f"   Model: {client.get_model_id()}")
            logger.info(f"   Region: {client.get_region()}")
        else:
            logger.error("❌ Nova Sonic is not available")
            logger.error("   Voice features will be degraded")
            logger.error("   Check AWS region, credentials, and model availability")
            
    except Exception as e:
        logger.error(f"❌ Failed to validate Nova Sonic connectivity: {str(e)}")
        logger.error("   Voice features may not work correctly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: Validate Nova Sonic connectivity
    await validate_nova_sonic_on_startup()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="Mock Interview Coach", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Session manager instance with adaptive mode enabled
session_manager = SessionManager(use_adaptive_mode=True)

# Store active sessions
active_sessions = {}


class SessionConfig(BaseModel):
    """Session configuration."""
    role: str
    level: str
    language: str
    demo_mode: bool = False
    user_id: Optional[str] = None


# ── Auth dependency ──────────────────────────────────────────────────────────

async def optional_current_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Non-breaking auth dependency — returns None when Cognito is absent."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    if not is_cognito_configured():
        return None
    try:
        return validate_token(authorization.split(" ", 1)[1])
    except ValueError:
        return None


# ── Auth routes ─────────────────────────────────────────────────────────────

@app.get("/auth/config")
async def auth_config():
    """Return Cognito configuration for the frontend."""
    if not is_cognito_configured():
        return {"enabled": False}

    redirect_uri = os.getenv(
        "COGNITO_REDIRECT_URI", "http://localhost:8000/auth/callback"
    )
    return {
        "enabled": True,
        "client_id": os.getenv("COGNITO_CLIENT_ID"),
        "domain": os.getenv("COGNITO_DOMAIN", "").rstrip("/"),
        "redirect_uri": redirect_uri,
    }


@app.get("/auth/callback")
async def auth_callback_redirect():
    """Serve index.html so the frontend JS can pick up ?code= from the URL."""
    return FileResponse("static/index.html")


@app.post("/auth/callback")
async def auth_callback(body: dict):
    """Exchange authorization code for tokens, upsert user in DynamoDB."""
    if not is_cognito_configured():
        return {"error": "Auth not configured"}, 400

    code = body.get("code")
    redirect_uri = body.get("redirect_uri")
    code_verifier = body.get("code_verifier")

    if not code or not redirect_uri or not code_verifier:
        return {"error": "Missing required fields"}, 400

    try:
        tokens = await exchange_code_for_tokens(code, redirect_uri, code_verifier)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    id_token = tokens.get("id_token")
    if not id_token:
        return {"error": "No id_token in response"}, 400

    try:
        claims = validate_token(id_token, access_token=tokens.get("access_token"))
    except ValueError as exc:
        return {"error": str(exc)}, 401

    user = {
        "user_id": claims.get("sub"),
        "email": claims.get("email", ""),
        "name": claims.get("given_name") or claims.get("name") or claims.get("cognito:username", ""),
        "picture": claims.get("picture", ""),
    }

    upsert_user(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        picture=user["picture"],
    )

    return {"id_token": id_token, "user": user}


@app.get("/auth/user")
async def auth_user(current_user: Optional[dict] = Depends(optional_current_user)):
    """Return the currently authenticated user from the Bearer token."""
    if not current_user:
        return {"error": "Unauthorized"}, 401

    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email", ""),
        "name": current_user.get("name", current_user.get("cognito:username", "")),
        "picture": current_user.get("picture", ""),
    }


@app.get("/api/user/{user_id}/sessions")
async def get_user_sessions_endpoint(
    user_id: str,
    current_user: Optional[dict] = Depends(optional_current_user),
):
    """Return the session history for a user.

    When Cognito is configured the caller must be the owner (sub == user_id).
    In demo/unconfigured mode this returns an empty list.
    """
    from fastapi import HTTPException
    if is_cognito_configured():
        if current_user is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if current_user.get("sub") != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    sessions = _get_user_sessions(user_id)
    return {"sessions": sessions}


@app.get("/auth/logout")
async def auth_logout():
    """Return the Cognito logout URL."""
    if not is_cognito_configured():
        return {"logout_url": "/"}

    domain = os.getenv("COGNITO_DOMAIN", "").rstrip("/")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    redirect_uri = os.getenv("COGNITO_REDIRECT_URI", "http://localhost:8000")

    # Strip path from redirect_uri to get just the origin
    from urllib.parse import urlparse
    parsed = urlparse(redirect_uri)
    logout_redirect = f"{parsed.scheme}://{parsed.netloc}"

    logout_url = (
        f"{domain}/logout"
        f"?client_id={client_id}"
        f"&logout_uri={logout_redirect}"
    )
    return {"logout_url": logout_url}


# ── Main routes ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main application page."""
    return FileResponse("static/index.html")


@app.post("/api/session/start")
async def start_session(config: SessionConfig):
    """Start a new interview session."""
    try:
        role = Role(config.role)
        level = Level(config.level)
        language = Language(config.language)
        
        session_id = session_manager.start_session(
            role, level, language, config.demo_mode
        )
        
        active_sessions[session_id] = {
            "role": config.role,
            "level": config.level,
            "language": config.language,
            "user_id": config.user_id,
            "demo_mode": config.demo_mode,
        }
        
        return {
            "session_id": session_id,
            "status": "started"
        }
    except Exception as e:
        return {"error": str(e)}, 400


@app.get("/api/session/{session_id}/question")
async def get_question(session_id: str):
    """Get the next question."""
    try:
        question = session_manager.get_next_question(session_id)
        
        if question is None:
            return {"question": None, "message": "No more questions"}
        
        # Cache current question text for the /question/audio endpoint
        if session_id in active_sessions:
            active_sessions[session_id]["current_question_text"] = question.text

        return {
            "question_id": question.id,
            "text": question.text,
            "technical_area": question.technical_area.value
        }
    except Exception as e:
        return {"error": str(e)}, 400


@app.post("/api/session/{session_id}/response")
async def submit_response(session_id: str, response: dict):
    """Submit a response."""
    try:
        evaluation = session_manager.submit_response(
            session_id,
            response.get("text", "")
        )
        
        return {
            "score": evaluation.score,
            "feedback": evaluation.feedback_text,
            "correct_concepts": evaluation.correct_concepts,
            "missing_concepts": evaluation.missing_concepts,
            "strengths": evaluation.strengths,
            "improvements": evaluation.weaknesses,  # Map weaknesses to improvements for frontend
            "recommended_topics": evaluation.recommended_topics
        }
    except Exception as e:
        return {"error": str(e)}, 400


@app.get("/api/session/{session_id}/performance")
async def get_performance(session_id: str):
    """Get performance analysis."""
    try:
        analysis = session_manager.get_performance_analysis(session_id)
        
        if analysis is None:
            return {"error": "No performance data available"}, 404
        
        # Convert Level enum to string for JSON serialization
        if 'recommended_level' in analysis:
            analysis['recommended_level'] = analysis['recommended_level'].value
        
        # Convert TechnicalArea enums to strings
        if 'weak_areas' in analysis:
            analysis['weak_areas'] = [area.value for area in analysis['weak_areas']]
        if 'strong_areas' in analysis:
            analysis['strong_areas'] = [area.value for area in analysis['strong_areas']]
        
        return analysis
    except Exception as e:
        return {"error": str(e)}, 400


@app.post("/api/session/{session_id}/end")
async def end_session(session_id: str):
    """End the session and get report."""
    try:
        report = session_manager.end_session(session_id)
        
        # Generate PDF
        pdf_bytes = session_manager._report_generator.export_pdf(report)
        
        # Save PDF temporarily
        pdf_path = f"reports/{session_id}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Count questions answered
        questions_answered = len(report.questions_and_responses)

        area_scores_serialized = {k.value: v for k, v in report.area_scores.items()}

        # Persist session record to DynamoDB (silent no-op when unconfigured)
        session_meta = active_sessions.get(session_id, {})
        try:
            save_session_record(
                user_id=session_meta.get("user_id") or "anonymous",
                session_id=session_id,
                role=session_meta.get("role", ""),
                level=session_meta.get("level", ""),
                language=session_meta.get("language", ""),
                overall_score=report.overall_score,
                area_scores=area_scores_serialized,
                demo=session_meta.get("demo_mode", False),
            )
        except Exception:
            pass  # DynamoDB errors must never break the response

        return {
            "overall_score": report.overall_score,
            "final_score": report.overall_score,  # Add explicit final_score field
            "questions_answered": questions_answered,
            "area_scores": area_scores_serialized,
            "pdf_url": f"/api/report/{session_id}"
        }
    except Exception as e:
        return {"error": str(e)}, 400


@app.get("/api/report/{session_id}")
async def get_report(session_id: str):
    """Download PDF report."""
    try:
        pdf_path = f"reports/{session_id}.pdf"
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"interview_report_{session_id}.pdf"
        )
    except Exception as e:
        return {"error": str(e)}, 404


@app.get("/api/metrics/global")
async def get_global_metrics():
    """Get global metrics."""
    try:
        metrics = session_manager.get_global_metrics()
        return metrics
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/metrics/areas")
async def get_area_metrics():
    """Get area-specific metrics."""
    try:
        metrics = session_manager.get_area_metrics()
        return metrics
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/health")
async def health_check():
    """Health check endpoint that monitors Nova Sonic availability.
    
    Returns:
        - status: "healthy" if Nova Sonic is available
                 "degraded" if Nova Sonic is unavailable but app is running
                 "unhealthy" if there's a critical error
        - nova_sonic_status: "available" or "unavailable"
        - timestamp: ISO format timestamp
        - status_code: 200 for healthy/degraded, 503 for unhealthy
    """
    from datetime import datetime, timezone
    from mock_interview_coach.voice_interface import NovaSonicClient
    
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    try:
        # Create Nova Sonic client and check health
        client = NovaSonicClient()
        is_available = await client.health_check()
        
        if is_available:
            return {
                "status": "healthy",
                "nova_sonic_status": "available",
                "timestamp": timestamp
            }
        else:
            return {
                "status": "degraded",
                "nova_sonic_status": "unavailable",
                "timestamp": timestamp
            }
    except Exception as e:
        # Critical error - return 503
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "nova_sonic_status": "error",
                "error": str(e),
                "timestamp": timestamp
            }
        )


@app.post("/api/tts")
async def text_to_speech(body: dict):
    """Generic TTS endpoint — converts arbitrary text to MP3 via Amazon Polly.

    Used by the frontend to read feedback aloud after each evaluation.
    Returns 204 in dev mode (silent fallback).
    """
    from fastapi.responses import Response

    if os.getenv("ENABLE_DEV_MODE", "false").lower() == "true":
        return Response(status_code=204)

    text = body.get("text", "").strip()
    language = body.get("language", "en")
    if not text:
        return Response(status_code=204)

    try:
        from mock_interview_coach.voice_interface import NovaSonicClient
        client = NovaSonicClient()
        audio_data = await client.synthesize_speech(text=text, language=language)
        if not audio_data:
            return Response(status_code=204)
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        return Response(status_code=204)  # Non-fatal — client shows text regardless


@app.get("/api/session/{session_id}/question/audio")
async def get_question_audio(session_id: str):
    """Synthesize TTS audio for the current question.

    Returns an MP3 audio file of the current question being spoken.
    Falls back to 404 when TTS is unavailable (dev mode / no AWS).
    """
    from fastapi.responses import Response

    # In dev mode there is no real TTS — return 204 so the frontend skips playback
    if os.getenv("ENABLE_DEV_MODE", "false").lower() == "true":
        return Response(status_code=204)

    try:
        session_info = active_sessions.get(session_id, {})
        language = session_info.get("language", "en")
        question_text = session_info.get("current_question_text")
        if not question_text:
            return Response(status_code=204)

        from mock_interview_coach.voice_interface import NovaSonicClient
        client = NovaSonicClient()
        audio_data = await client.synthesize_speech(
            text=question_text,
            language=language,
            session_id=session_id
        )

        if not audio_data:
            return Response(status_code=204)

        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}, 500


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming."""
    from mock_interview_coach.voice_interface import WebSocketHandler

    # Create WebSocket handler
    handler = WebSocketHandler(websocket, session_id)

    # Handle connection lifecycle
    await handler.handle_connection()


if __name__ == "__main__":
    import uvicorn
    
    # Validate Nova Sonic on startup when running directly
    def validate_nova_sonic_sync():
        """Validate Nova Sonic connectivity on server startup (synchronous version)."""
        from mock_interview_coach.voice_interface import NovaSonicClient
        
        # Check if dev mode is enabled
        dev_mode = os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true'
        
        if dev_mode:
            print("🔧 Development mode enabled - using mock audio")
            return True
        
        print("🔍 Validating Nova Sonic connectivity...")
        
        try:
            client = NovaSonicClient()
            is_available = client.validate_model_availability()
            
            if is_available:
                print("✅ Nova Sonic is available")
                return True
            else:
                print("❌ ERROR: Nova Sonic is not available")
                print("   Enable dev mode or fix AWS configuration")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Failed to validate Nova Sonic: {str(e)}")
            return False
    
    # Run validation
    if not validate_nova_sonic_sync():
        print("\n❌ Server startup aborted")
        sys.exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
