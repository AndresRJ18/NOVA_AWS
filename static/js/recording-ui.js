/**
 * RecordingUI Component
 * 
 * Manages voice recording controls and visual feedback for audio state.
 * Coordinates between AudioCapture, AudioPlayback, and WebSocketClient modules.
 * 
 * Requirements: 1.2, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1
 */

// Add CSS animations for notifications
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                transform: translateX(-50%) translateY(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
        }
        
        @keyframes slideUp {
            from {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
            to {
                transform: translateX(-50%) translateY(-100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

export class RecordingUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element with id "${containerId}" not found`);
        }

        // Audio state management
        this.state = {
            audioState: 'idle', // 'idle' | 'recording' | 'processing' | 'speaking'
            volumeLevel: 0, // 0-100
            playbackProgress: 0, // 0-100
            isTextMode: false,
            lastError: null,
            lastAudio: null // Store last audio for replay
        };

        // Module instances (to be injected)
        this.audioCapture = null;
        this.audioPlayback = null;
        this.websocketClient = null;

        // UI update intervals
        this.volumeUpdateInterval = null;
        this.progressUpdateInterval = null;

        // Callbacks
        this.onStateChangeCallback = null;
        this.onRecordingCompleteCallback = null;
        this.onErrorCallback = null;

        // UI elements (will be created)
        this.elements = {};

        // Initialize UI
        this._createUI();
    }

    /**
     * Set module instances
     * @param {AudioCapture} audioCapture - AudioCapture instance
     * @param {AudioPlayback} audioPlayback - AudioPlayback instance
     * @param {WebSocketClient} websocketClient - WebSocketClient instance
     */
    setModules(audioCapture, audioPlayback, websocketClient) {
        this.audioCapture = audioCapture;
        this.audioPlayback = audioPlayback;
        this.websocketClient = websocketClient;
    }

    /**
     * Create UI elements
     * @private
     */
    _createUI() {
        this.container.innerHTML = `
            <div class="recording-ui">
                <!-- Mode Switching Buttons (always visible) -->
                <div class="mode-switch-container" style="margin-bottom: var(--space-4); display: flex; gap: var(--space-2); justify-content: center;">
                    <button id="btn-switch-to-text" class="btn-mode-switch" style="display: none;">
                        <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                        </svg>
                        <span>Cambiar a Texto</span>
                    </button>
                    <button id="btn-switch-to-voice" class="btn-mode-switch" style="display: none;">
                        <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                            <line x1="12" x2="12" y1="19" y2="22"/>
                        </svg>
                        <span>Cambiar a Voz</span>
                    </button>
                </div>

                <!-- Start Recording Button (visible when idle) -->
                <button id="btn-start-recording" class="btn-recording" style="display: none;">
                    <svg class="icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M12 1v6m0 6v6m6-9h-6m-6 0h6"></path>
                    </svg>
                    <span>Iniciar Grabación</span>
                </button>

                <!-- Stop Recording Button (visible when recording) -->
                <button id="btn-stop-recording" class="btn-recording btn-stop" style="display: none;">
                    <svg class="icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                    </svg>
                    <span>Detener Grabación</span>
                </button>

                <!-- Volume Indicator (visible when recording) -->
                <div id="volume-indicator" class="volume-indicator" style="display: none;">
                    <div class="volume-label">Volumen</div>
                    <div class="volume-bar-container">
                        <div id="volume-bar" class="volume-bar"></div>
                    </div>
                    <div class="volume-animation">
                        <div class="pulse-ring"></div>
                        <div class="pulse-ring pulse-ring-delay"></div>
                    </div>
                </div>

                <!-- Processing Spinner (visible when processing) -->
                <div id="processing-spinner" class="processing-spinner" style="display: none;">
                    <div class="spinner"></div>
                    <div class="processing-text">Procesando audio...</div>
                </div>

                <!-- Playback Indicator (visible when speaking) -->
                <div id="playback-indicator" class="playback-indicator" style="display: none;">
                    <div class="playback-animation">
                        <div class="sound-wave"></div>
                        <div class="sound-wave"></div>
                        <div class="sound-wave"></div>
                        <div class="sound-wave"></div>
                    </div>
                    <div class="playback-text">Reproduciendo...</div>
                    
                    <!-- Progress Bar -->
                    <div class="progress-bar-container">
                        <div id="progress-bar" class="progress-bar"></div>
                    </div>
                    
                    <!-- Playback Controls -->
                    <div class="playback-controls">
                        <button id="btn-pause-playback" class="btn-playback-control" title="Pausar">
                            <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <rect x="6" y="4" width="4" height="16"></rect>
                                <rect x="14" y="4" width="4" height="16"></rect>
                            </svg>
                        </button>
                        <button id="btn-replay-audio" class="btn-playback-control" title="Repetir">
                            <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                                <path d="M21 3v5h-5"></path>
                                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                                <path d="M3 21v-5h5"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Store references to UI elements
        this.elements = {
            switchToTextButton: document.getElementById('btn-switch-to-text'),
            switchToVoiceButton: document.getElementById('btn-switch-to-voice'),
            startButton: document.getElementById('btn-start-recording'),
            stopButton: document.getElementById('btn-stop-recording'),
            volumeIndicator: document.getElementById('volume-indicator'),
            volumeBar: document.getElementById('volume-bar'),
            processingSpinner: document.getElementById('processing-spinner'),
            playbackIndicator: document.getElementById('playback-indicator'),
            progressBar: document.getElementById('progress-bar'),
            pauseButton: document.getElementById('btn-pause-playback'),
            replayButton: document.getElementById('btn-replay-audio')
        };

        // Attach event listeners
        this._attachEventListeners();

        // Load saved mode preference from localStorage
        this._loadModePreference();

        // Initial UI update
        this._updateUI();
    }

    /**
     * Attach event listeners to UI elements
     * @private
     */
    _attachEventListeners() {
        // Mode switch buttons
        this.elements.switchToTextButton.addEventListener('click', () => {
            this.switchToTextMode();
        });

        this.elements.switchToVoiceButton.addEventListener('click', () => {
            this.switchToVoiceMode();
        });

        // Start recording button
        this.elements.startButton.addEventListener('click', () => {
            this.startRecording();
        });

        // Stop recording button
        this.elements.stopButton.addEventListener('click', () => {
            this.stopRecording();
        });

        // Pause playback button
        this.elements.pauseButton.addEventListener('click', () => {
            this.pausePlayback();
        });

        // Replay audio button
        this.elements.replayButton.addEventListener('click', () => {
            this.replayLastAudio();
        });
    }

    /**
     * Start recording audio
     * @returns {Promise<void>}
     */
    async startRecording() {
        if (this.state.audioState !== 'idle') {
            console.warn('Cannot start recording: not in idle state');
            return;
        }

        if (!this.audioCapture) {
            this._handleError(new Error('AudioCapture module not initialized'));
            return;
        }

        try {
            // Transition to recording state
            this._setAudioState('recording');

            // Start audio capture
            await this.audioCapture.startCapture((audioChunk) => {
                // Optional: stream audio chunks to server in real-time
                // For now, we'll collect all chunks and send on stop
            });

            // Start volume level updates
            this._startVolumeUpdates();

        } catch (error) {
            this._handleError(error);
            this._setAudioState('idle');
        }
    }

    /**
     * Stop recording audio
     * @returns {Promise<void>}
     */
    async stopRecording() {
        if (this.state.audioState !== 'recording') {
            console.warn('Cannot stop recording: not in recording state');
            return;
        }

        try {
            // Stop volume updates
            this._stopVolumeUpdates();

            // Stop audio capture and get complete audio
            const audioData = this.audioCapture.stopCapture();

            // Transition to processing state
            this._setAudioState('processing');

            // Notify callback if set
            if (this.onRecordingCompleteCallback) {
                this.onRecordingCompleteCallback(audioData);
            }

            // Send audio to server via WebSocket
            if (this.websocketClient && this.websocketClient.isConnected()) {
                const format = this.audioCapture.getAudioFormat().format;
                this.websocketClient.sendAudio(audioData, format);
            }

        } catch (error) {
            this._handleError(error);
            this._setAudioState('idle');
        }
    }

    /**
     * Set audio state and update UI
     * @param {string} newState - New audio state
     * @private
     */
    _setAudioState(newState) {
        const oldState = this.state.audioState;
        this.state.audioState = newState;

        // Update UI based on new state
        this._updateUI();

        // Notify callback if set
        if (this.onStateChangeCallback) {
            this.onStateChangeCallback(newState, oldState);
        }
    }

    /**
     * Update UI based on current state
     * @private
     */
    _updateUI() {
        const { audioState, isTextMode } = this.state;

        // Update mode switch buttons visibility
        if (isTextMode) {
            this.elements.switchToTextButton.style.display = 'none';
            this.elements.switchToVoiceButton.style.display = 'inline-flex';
        } else {
            this.elements.switchToTextButton.style.display = 'inline-flex';
            this.elements.switchToVoiceButton.style.display = 'none';
        }

        // Hide all audio control elements first
        this.elements.startButton.style.display = 'none';
        this.elements.stopButton.style.display = 'none';
        this.elements.volumeIndicator.style.display = 'none';
        this.elements.processingSpinner.style.display = 'none';
        this.elements.playbackIndicator.style.display = 'none';

        // Only show audio controls if not in text mode
        if (!isTextMode) {
            // Show elements based on state
            switch (audioState) {
                case 'idle':
                    this.elements.startButton.style.display = 'flex';
                    break;

                case 'recording':
                    this.elements.stopButton.style.display = 'flex';
                    this.elements.volumeIndicator.style.display = 'flex';
                    break;

                case 'processing':
                    this.elements.processingSpinner.style.display = 'flex';
                    break;

                case 'speaking':
                    this.elements.playbackIndicator.style.display = 'flex';
                    // Disable recording controls while speaking
                    this.elements.startButton.disabled = true;
                    break;

                default:
                    console.warn('Unknown audio state:', audioState);
            }

            // Re-enable start button when not speaking
            if (audioState !== 'speaking') {
                this.elements.startButton.disabled = false;
            }
        }
    }

    /**
     * Start volume level updates
     * @private
     */
    _startVolumeUpdates() {
        if (this.volumeUpdateInterval) {
            return;
        }

        // Update volume every 100ms
        this.volumeUpdateInterval = setInterval(() => {
            if (this.audioCapture && this.state.audioState === 'recording') {
                const volumeLevel = this.audioCapture.getVolumeLevel();
                this._updateVolumeDisplay(volumeLevel);
            }
        }, 100);
    }

    /**
     * Stop volume level updates
     * @private
     */
    _stopVolumeUpdates() {
        if (this.volumeUpdateInterval) {
            clearInterval(this.volumeUpdateInterval);
            this.volumeUpdateInterval = null;
        }
    }

    /**
     * Update volume display
     * @param {number} volumeLevel - Volume level (0-100)
     * @private
     */
    _updateVolumeDisplay(volumeLevel) {
        this.state.volumeLevel = volumeLevel;
        
        // Update volume bar width
        if (this.elements.volumeBar) {
            this.elements.volumeBar.style.width = `${volumeLevel}%`;
            
            // Change color based on volume level
            if (volumeLevel < 20) {
                this.elements.volumeBar.style.backgroundColor = '#6b7280'; // gray
            } else if (volumeLevel < 60) {
                this.elements.volumeBar.style.backgroundColor = '#3b82f6'; // blue
            } else {
                this.elements.volumeBar.style.backgroundColor = '#10b981'; // green
            }
        }
    }

    /**
     * Play audio output
     * @param {ArrayBuffer} audioData - Audio data to play
     * @param {string} format - Audio format ('mp3' or 'opus')
     * @returns {Promise<void>}
     */
    async playAudio(audioData, format = 'mp3') {
        if (!this.audioPlayback) {
            this._handleError(new Error('AudioPlayback module not initialized'));
            return;
        }

        try {
            // Store audio for replay
            this.state.lastAudio = { data: audioData, format: format };

            // Transition to speaking state
            this._setAudioState('speaking');

            // Start progress updates
            this._startProgressUpdates();

            // Set up completion callback
            this.audioPlayback.onComplete(() => {
                this._onPlaybackComplete();
            });

            // Play audio
            await this.audioPlayback.play(audioData, format);

        } catch (error) {
            this._handleError(error);
            this._setAudioState('idle');
        }
    }

    /**
     * Pause audio playback
     */
    pausePlayback() {
        if (this.state.audioState !== 'speaking') {
            console.warn('Cannot pause: not in speaking state');
            return;
        }

        if (!this.audioPlayback) {
            this._handleError(new Error('AudioPlayback module not initialized'));
            return;
        }

        try {
            // Stop playback
            this.audioPlayback.stop();

            // Stop progress updates
            this._stopProgressUpdates();

            // Transition to idle state
            this._setAudioState('idle');

        } catch (error) {
            this._handleError(error);
        }
    }

    /**
     * Replay last audio
     * @returns {Promise<void>}
     */
    async replayLastAudio() {
        if (!this.state.lastAudio) {
            console.warn('No audio to replay');
            return;
        }

        const { data, format } = this.state.lastAudio;
        await this.playAudio(data, format);
    }

    /**
     * Handle playback completion
     * @private
     */
    _onPlaybackComplete() {
        // Stop progress updates
        this._stopProgressUpdates();

        // Reset progress
        this.state.playbackProgress = 0;
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = '0%';
        }

        // Transition to idle state (auto-enables recording controls)
        this._setAudioState('idle');
    }

    /**
     * Start playback progress updates
     * @private
     */
    _startProgressUpdates() {
        if (this.progressUpdateInterval) {
            return;
        }

        // Update progress every 100ms
        this.progressUpdateInterval = setInterval(() => {
            if (this.audioPlayback && this.state.audioState === 'speaking') {
                const progress = this.audioPlayback.getProgress();
                this._updateProgressDisplay(progress);
            }
        }, 100);
    }

    /**
     * Stop playback progress updates
     * @private
     */
    _stopProgressUpdates() {
        if (this.progressUpdateInterval) {
            clearInterval(this.progressUpdateInterval);
            this.progressUpdateInterval = null;
        }
    }

    /**
     * Update progress display
     * @param {number} progress - Progress (0-100)
     * @private
     */
    _updateProgressDisplay(progress) {
        this.state.playbackProgress = progress;
        
        // Update progress bar width
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = `${progress}%`;
        }
    }

    /**
     * Handle errors
     * @param {Error} error - Error object
     * @private
     */
    _handleError(error) {
        console.error('RecordingUI error:', error);
        this.state.lastError = error.message;

        // Check if this is an audio-related error that should trigger fallback
        const shouldFallback = this._shouldActivateTextFallback(error);

        if (shouldFallback) {
            this._activateTextFallback(error);
        }

        if (this.onErrorCallback) {
            this.onErrorCallback(error);
        }
    }

    /**
     * Check if error should trigger automatic text fallback
     * @param {Error} error - Error object
     * @returns {boolean} True if should activate text fallback
     * @private
     */
    _shouldActivateTextFallback(error) {
        const errorMessage = error.message || '';
        
        // Audio capture errors
        if (errorMessage.includes('MICROPHONE_PERMISSION_DENIED')) return true;
        if (errorMessage.includes('MICROPHONE_NOT_AVAILABLE')) return true;
        if (errorMessage.includes('AUDIO_CAPTURE_FAILED')) return true;
        
        // API errors (from WebSocket)
        if (errorMessage.includes('transcription_failed')) return true;
        if (errorMessage.includes('nova_sonic_unavailable')) return true;
        if (errorMessage.includes('websocket_reconnect_failed')) return true;
        
        return false;
    }

    /**
     * Activate text fallback mode with error notification
     * @param {Error} error - Error that triggered fallback
     * @private
     */
    _activateTextFallback(error) {
        // Switch to text mode
        this.switchToTextMode();

        // Show notification to user
        this._showFallbackNotification(error);

        console.log('Automatic text fallback activated due to:', error.message);
    }

    /**
     * Show notification that text mode has been activated
     * @param {Error} error - Error that triggered fallback
     * @private
     */
    _showFallbackNotification(error) {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('fallback-notification');
        
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'fallback-notification';
            notification.className = 'fallback-notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                max-width: 500px;
                animation: slideDown 0.3s ease-out;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            `;
            document.body.appendChild(notification);
        }

        // Get user-friendly error message
        const { title, message, suggestion } = this._getErrorDetails(error);

        // Set notification content
        notification.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink: 0; margin-top: 2px;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">${title}</div>
                    <div style="font-size: 14px; opacity: 0.95; margin-bottom: 8px;">${message}</div>
                    <div style="font-size: 13px; opacity: 0.85; background: rgba(255, 255, 255, 0.15); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;">
                        ${suggestion}
                    </div>
                    <div style="font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        Modo de texto activado
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; padding: 4px; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (notification && notification.parentElement) {
                notification.style.animation = 'slideUp 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, 10000);
    }

    /**
     * Get user-friendly error details
     * @param {Error} error - Error object
     * @returns {Object} Error details with title, message, and suggestion
     * @private
     */
    _getErrorDetails(error) {
        const errorMessage = error.message || '';

        // Microphone permission denied
        if (errorMessage.includes('MICROPHONE_PERMISSION_DENIED')) {
            return {
                title: 'Permiso de micrófono denegado',
                message: 'Necesitamos acceso al micrófono para grabar tu voz.',
                suggestion: 'Haz clic en el ícono 🔒 en la barra de direcciones de tu navegador para otorgar permiso.'
            };
        }

        // Microphone not available
        if (errorMessage.includes('MICROPHONE_NOT_AVAILABLE')) {
            return {
                title: 'Micrófono no disponible',
                message: 'No se encontró ningún dispositivo de micrófono.',
                suggestion: 'Conecta un micrófono o usa el modo de texto para continuar.'
            };
        }

        // Audio capture failed
        if (errorMessage.includes('AUDIO_CAPTURE_FAILED')) {
            return {
                title: 'Error al capturar audio',
                message: 'Hubo un problema al acceder a tu micrófono.',
                suggestion: 'Intenta recargar la página o usa el modo de texto.'
            };
        }

        // Transcription failed
        if (errorMessage.includes('transcription_failed')) {
            return {
                title: 'Error de transcripción',
                message: 'No pudimos transcribir tu audio.',
                suggestion: 'Puedes continuar en modo de texto mientras resolvemos el problema.'
            };
        }

        // Nova Sonic unavailable
        if (errorMessage.includes('nova_sonic_unavailable')) {
            return {
                title: 'Servicio de voz no disponible',
                message: 'El servicio de voz está temporalmente no disponible.',
                suggestion: 'Puedes continuar en modo de texto. Intenta el modo de voz más tarde.'
            };
        }

        // WebSocket reconnect failed
        if (errorMessage.includes('websocket_reconnect_failed')) {
            return {
                title: 'Conexión perdida',
                message: 'Se perdió la conexión con el servidor y no pudimos reconectar.',
                suggestion: 'Puedes continuar en modo de texto o recargar la página.'
            };
        }

        // Generic error
        return {
            title: 'Error de audio',
            message: 'Hubo un problema con el sistema de voz.',
            suggestion: 'Puedes continuar en modo de texto mientras resolvemos el problema.'
        };
    }

    /**
     * Get current audio state
     * @returns {string} Current audio state
     */
    getAudioState() {
        return this.state.audioState;
    }

    /**
     * Get current volume level
     * @returns {number} Volume level (0-100)
     */
    getVolumeLevel() {
        return this.state.volumeLevel;
    }

    /**
     * Set audio state (for external control)
     * @param {string} state - Audio state to set
     */
    setAudioState(state) {
        this._setAudioState(state);
    }

    /**
     * Set callback for state changes
     * @param {Function} callback - Function(newState, oldState)
     */
    onStateChange(callback) {
        this.onStateChangeCallback = callback;
    }

    /**
     * Set callback for recording completion
     * @param {Function} callback - Function(audioData)
     */
    onRecordingComplete(callback) {
        this.onRecordingCompleteCallback = callback;
    }

    /**
     * Set callback for errors
     * @param {Function} callback - Function(error)
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Check if recording controls are enabled
     * @returns {boolean}
     */
    areControlsEnabled() {
        return this.state.audioState !== 'speaking';
    }

    /**
     * Release resources and cleanup
     */
    release() {
        this._stopVolumeUpdates();
        this._stopProgressUpdates();
        
        if (this.audioCapture && this.state.audioState === 'recording') {
            this.audioCapture.stopCapture();
        }

        if (this.audioPlayback && this.state.audioState === 'speaking') {
            this.audioPlayback.stop();
        }

        this.state.audioState = 'idle';
        this._updateUI();
    }

    /**
     * Get current playback progress
     * @returns {number} Playback progress (0-100)
     */
    getPlaybackProgress() {
        return this.state.playbackProgress;
    }

    /**
     * Switch to text mode
     * Disables audio capture and playback, shows text input
     */
    switchToTextMode() {
        // Stop any ongoing audio operations
        if (this.state.audioState === 'recording' && this.audioCapture) {
            this.audioCapture.stopCapture();
            this._stopVolumeUpdates();
        }

        if (this.state.audioState === 'speaking' && this.audioPlayback) {
            this.audioPlayback.stop();
            this._stopProgressUpdates();
        }

        // Update state
        this.state.isTextMode = true;
        this.state.audioState = 'idle';

        // Save preference to localStorage
        this._saveModePreference('text');

        // Update UI
        this._updateUI();

        // Show text input area (if exists in parent page)
        const textArea = document.getElementById('responseText');
        if (textArea) {
            textArea.style.display = 'block';
            textArea.focus();
        }

        // Notify callback if set
        if (this.onStateChangeCallback) {
            this.onStateChangeCallback('text_mode', this.state.audioState);
        }

        console.log('Switched to text mode');
    }

    /**
     * Switch to voice mode
     * Re-enables audio capture and playback controls
     */
    switchToVoiceMode() {
        // Update state
        this.state.isTextMode = false;
        this.state.audioState = 'idle';

        // Save preference to localStorage
        this._saveModePreference('voice');

        // Update UI
        this._updateUI();

        // Notify callback if set
        if (this.onStateChangeCallback) {
            this.onStateChangeCallback('voice_mode', 'idle');
        }

        console.log('Switched to voice mode');
    }

    /**
     * Save mode preference to localStorage
     * @param {string} mode - 'voice' or 'text'
     * @private
     */
    _saveModePreference(mode) {
        try {
            localStorage.setItem('interview_mode_preference', mode);
        } catch (error) {
            console.warn('Failed to save mode preference to localStorage:', error);
        }
    }

    /**
     * Load mode preference from localStorage
     * @private
     */
    _loadModePreference() {
        try {
            const savedMode = localStorage.getItem('interview_mode_preference');
            if (savedMode === 'text') {
                this.state.isTextMode = true;
            } else {
                // Default to voice mode
                this.state.isTextMode = false;
            }
        } catch (error) {
            console.warn('Failed to load mode preference from localStorage:', error);
            // Default to voice mode on error
            this.state.isTextMode = false;
        }
    }

    /**
     * Check if currently in text mode
     * @returns {boolean} True if in text mode
     */
    isTextMode() {
        return this.state.isTextMode;
    }
}

// Export for use in other modules (CommonJS compatibility)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RecordingUI;
}
