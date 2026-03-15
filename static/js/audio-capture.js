/**
 * AudioCapture Module
 * 
 * Handles browser audio capture from microphone using Web Audio API.
 * Captures audio at 16kHz, 16-bit PCM format compatible with Nova Sonic.
 * 
 * Requirements: 1.1, 1.4, 5.6, 11.1, 11.2
 */

export class AudioCapture {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.sourceNode = null;
        this.processorNode = null;
        this.audioChunks = [];
        this.isCapturing = false;
        this.volumeLevel = 0;
        this.onAudioChunkCallback = null;
        
        // Target audio format for Nova Sonic
        this.targetSampleRate = 16000; // 16kHz
        this.targetChannels = 1; // Mono
        this.targetBitDepth = 16; // 16-bit
    }

    /**
     * Check if browser supports required audio APIs
     * @returns {boolean} True if supported
     */
    isSupported() {
        return !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            (window.AudioContext || window.webkitAudioContext)
        );
    }

    /**
     * Request microphone permission from user
     * @returns {Promise<boolean>} True if permission granted
     * @throws {Error} If permission denied or not available
     */
    async requestPermission() {
        if (!this.isSupported()) {
            throw new Error('MICROPHONE_NOT_AVAILABLE: Your browser does not support audio capture');
        }

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: this.targetChannels,
                    sampleRate: this.targetSampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Store stream for later use
            this.mediaStream = stream;
            
            return true;
        } catch (error) {
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                throw new Error('MICROPHONE_PERMISSION_DENIED: Microphone permission was denied');
            } else if (error.name === 'NotFoundError') {
                throw new Error('MICROPHONE_NOT_AVAILABLE: No microphone device found');
            } else {
                throw new Error(`AUDIO_CAPTURE_FAILED: ${error.message}`);
            }
        }
    }

    /**
     * Start capturing audio from microphone
     * @param {Function} onAudioChunk - Callback for each audio chunk (ArrayBuffer)
     * @returns {Promise<void>}
     */
    async startCapture(onAudioChunk) {
        if (this.isCapturing) {
            throw new Error('Already capturing audio');
        }

        if (!this.mediaStream) {
            await this.requestPermission();
        }

        this.onAudioChunkCallback = onAudioChunk;
        this.audioChunks = [];
        this.isCapturing = true;

        // Create AudioContext with target sample rate
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioContextClass({
            sampleRate: this.targetSampleRate
        });

        // Create source node from media stream
        this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

        // Use AudioWorklet if available (modern), otherwise ScriptProcessorNode (legacy)
        if (this.audioContext.audioWorklet) {
            await this._setupAudioWorklet();
        } else {
            this._setupScriptProcessor();
        }
    }

    /**
     * Setup AudioWorklet for audio processing (modern, non-deprecated).
     * Falls back to ScriptProcessorNode only if module load fails.
     * @private
     */
    async _setupAudioWorklet() {
        try {
            await this.audioContext.audioWorklet.addModule(
                '/static/js/audio-worklet-processor.js'
            );
            this.processorNode = new AudioWorkletNode(
                this.audioContext,
                'nova-pcm-processor'
            );
            this.processorNode.port.onmessage = (event) => {
                if (!this.isCapturing) return;
                const { pcm, rms } = event.data;
                this.volumeLevel = Math.min(100, Math.floor(rms * 300));
                const chunk = new Int16Array(pcm);
                this.audioChunks.push(chunk);
                if (this.onAudioChunkCallback) {
                    this.onAudioChunkCallback(chunk.buffer);
                }
            };
            this.sourceNode.connect(this.processorNode);
            this.processorNode.connect(this.audioContext.destination);
        } catch (e) {
            console.warn('[audio] AudioWorklet unavailable, using ScriptProcessor:', e.message);
            this._setupScriptProcessor();
        }
    }

    /**
     * Setup legacy ScriptProcessorNode for audio processing
     * @private
     */
    _setupScriptProcessor() {
        // Buffer size: 4096 samples provides good balance between latency and performance
        const bufferSize = 4096;
        
        // Create ScriptProcessorNode (deprecated but widely supported)
        this.processorNode = this.audioContext.createScriptProcessor(
            bufferSize,
            this.targetChannels,
            this.targetChannels
        );

        // Process audio data
        this.processorNode.onaudioprocess = (event) => {
            if (!this.isCapturing) return;

            const inputBuffer = event.inputBuffer;
            const channelData = inputBuffer.getChannelData(0); // Get mono channel

            // Calculate volume level
            this._calculateVolumeLevel(channelData);

            // Convert Float32Array to Int16Array (16-bit PCM)
            const pcmData = this._floatTo16BitPCM(channelData);

            // Store chunk
            this.audioChunks.push(pcmData);

            // Call callback with chunk if provided
            if (this.onAudioChunkCallback) {
                this.onAudioChunkCallback(pcmData.buffer);
            }
        };

        // Connect nodes: source -> processor -> destination
        this.sourceNode.connect(this.processorNode);
        this.processorNode.connect(this.audioContext.destination);
    }

    /**
     * Calculate real-time volume level from audio samples
     * @param {Float32Array} samples - Audio samples
     * @private
     */
    _calculateVolumeLevel(samples) {
        let sum = 0;
        for (let i = 0; i < samples.length; i++) {
            sum += samples[i] * samples[i];
        }
        
        // Calculate RMS (Root Mean Square)
        const rms = Math.sqrt(sum / samples.length);
        
        // Convert to 0-100 scale (with some amplification for better visualization)
        this.volumeLevel = Math.min(100, Math.floor(rms * 300));
    }

    /**
     * Convert Float32Array to 16-bit PCM Int16Array
     * @param {Float32Array} float32Array - Input audio samples (-1.0 to 1.0)
     * @returns {Int16Array} 16-bit PCM samples
     * @private
     */
    _floatTo16BitPCM(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Clamp to [-1.0, 1.0] range
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            
            // Convert to 16-bit integer (-32768 to 32767)
            int16Array[i] = sample < 0 
                ? sample * 0x8000  // -32768
                : sample * 0x7FFF; // 32767
        }
        
        return int16Array;
    }

    /**
     * Stop capturing audio and return complete audio data
     * @returns {ArrayBuffer} Complete audio data as 16-bit PCM
     */
    async stopCapture() {
        if (!this.isCapturing) {
            throw new Error('Not currently capturing audio');
        }

        this.isCapturing = false;

        // Flush any partial buffer from AudioWorklet before disconnecting
        if (this.processorNode && this.processorNode.port) {
            this.processorNode.port.postMessage('flush');
            // Give the worklet one event-loop tick to deliver the flush message
            await new Promise(r => setTimeout(r, 50));
        }

        // Disconnect and cleanup audio nodes
        if (this.processorNode) {
            this.processorNode.disconnect();
            this.processorNode.onaudioprocess = null;
            this.processorNode = null;
        }

        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        // Combine all chunks into single ArrayBuffer
        const totalLength = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const completeAudio = new Int16Array(totalLength);
        
        let offset = 0;
        for (const chunk of this.audioChunks) {
            completeAudio.set(chunk, offset);
            offset += chunk.length;
        }

        // Clear chunks
        this.audioChunks = [];

        return completeAudio.buffer;
    }

    /**
     * Get current volume level (0-100)
     * @returns {number} Volume level
     */
    getVolumeLevel() {
        return this.volumeLevel;
    }

    /**
     * Release microphone resources
     */
    release() {
        if (this.isCapturing) {
            this.stopCapture();
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
    }

    /**
     * Get audio format information
     * @returns {Object} Audio format details
     */
    getAudioFormat() {
        return {
            sampleRate: this.targetSampleRate,
            channels: this.targetChannels,
            bitDepth: this.targetBitDepth,
            format: 'pcm'
        };
    }
}

// Export for use in other modules (CommonJS compatibility)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioCapture;
}
