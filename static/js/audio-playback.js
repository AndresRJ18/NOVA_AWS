/**
 * AudioPlayback Module
 * 
 * Handles browser audio playback using HTML5 Audio API.
 * Supports progressive playback (streaming) for MP3 and Opus formats.
 * 
 * Requirements: 3.3, 6.2, 6.3, 6.4, 11.4
 */

export class AudioPlayback {
    constructor() {
        this.audio = null;
        this.isPlaying = false;
        this.isPaused = false;
        this.currentAudioData = null;
        this.currentFormat = null;
        this.onCompleteCallback = null;
        this.progressUpdateInterval = null;
    }

    /**
     * Check if browser supports required audio formats
     * @returns {Object} Format support information
     */
    getSupportedFormats() {
        const audio = new Audio();
        return {
            mp3: audio.canPlayType('audio/mpeg') !== '',
            opus: audio.canPlayType('audio/ogg; codecs="opus"') !== '' ||
                  audio.canPlayType('audio/webm; codecs="opus"') !== ''
        };
    }

    /**
     * Detect audio format from data
     * @param {ArrayBuffer} audioData - Audio data
     * @returns {string} Detected format ('mp3' or 'opus')
     * @private
     */
    _detectFormat(audioData) {
        const view = new Uint8Array(audioData);
        
        // Check for MP3 signature (ID3 tag or MPEG frame sync)
        if (view.length >= 3) {
            // ID3v2 tag
            if (view[0] === 0x49 && view[1] === 0x44 && view[2] === 0x33) {
                return 'mp3';
            }
            // MPEG frame sync (11 bits set)
            if (view[0] === 0xFF && (view[1] & 0xE0) === 0xE0) {
                return 'mp3';
            }
        }
        
        // Check for Ogg/Opus signature
        if (view.length >= 4) {
            // OggS header
            if (view[0] === 0x4F && view[1] === 0x67 && 
                view[2] === 0x67 && view[3] === 0x53) {
                return 'opus';
            }
        }
        
        // Check for WebM signature
        if (view.length >= 4) {
            // EBML header
            if (view[0] === 0x1A && view[1] === 0x45 && 
                view[2] === 0xDF && view[3] === 0xA3) {
                return 'opus';
            }
        }
        
        // Default to mp3 if unknown
        return 'mp3';
    }

    /**
     * Play audio from ArrayBuffer
     * @param {ArrayBuffer} audioData - Audio data to play
     * @param {string} format - Audio format ('mp3' or 'opus'), auto-detected if not provided
     * @returns {Promise<void>}
     */
    async play(audioData, format = null) {
        // Stop any currently playing audio
        if (this.isPlaying) {
            this.stop();
        }

        // Detect format if not provided
        if (!format) {
            format = this._detectFormat(audioData);
        }

        this.currentAudioData = audioData;
        this.currentFormat = format;

        // Check format support
        const supported = this.getSupportedFormats();
        if (format === 'opus' && !supported.opus) {
            throw new Error('UNSUPPORTED_AUDIO_FORMAT: Browser does not support Opus format');
        }
        if (format === 'mp3' && !supported.mp3) {
            throw new Error('UNSUPPORTED_AUDIO_FORMAT: Browser does not support MP3 format');
        }

        // Create blob with appropriate MIME type
        const mimeType = format === 'opus' 
            ? 'audio/ogg; codecs="opus"' 
            : 'audio/mpeg';
        const blob = new Blob([audioData], { type: mimeType });
        const url = URL.createObjectURL(blob);

        // Create and configure audio element
        this.audio = new Audio(url);
        this.audio.preload = 'auto';

        // Set up event listeners
        return new Promise((resolve, reject) => {
            this.audio.addEventListener('canplay', () => {
                this.isPlaying = true;
                this.isPaused = false;
                
                // Start progress updates
                this._startProgressUpdates();
                
                // Start playback
                this.audio.play()
                    .then(() => resolve())
                    .catch(error => {
                        this.isPlaying = false;
                        reject(new Error(`PLAYBACK_FAILED: ${error.message}`));
                    });
            });

            this.audio.addEventListener('ended', () => {
                this._handlePlaybackComplete();
            });

            this.audio.addEventListener('error', (event) => {
                this.isPlaying = false;
                const error = this.audio.error;
                let errorMessage = 'Unknown playback error';
                
                if (error) {
                    switch (error.code) {
                        case error.MEDIA_ERR_ABORTED:
                            errorMessage = 'Playback aborted';
                            break;
                        case error.MEDIA_ERR_NETWORK:
                            errorMessage = 'Network error during playback';
                            break;
                        case error.MEDIA_ERR_DECODE:
                            errorMessage = 'Audio decoding failed';
                            break;
                        case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                            errorMessage = 'Audio format not supported';
                            break;
                    }
                }
                
                reject(new Error(`PLAYBACK_ERROR: ${errorMessage}`));
            });

            // Load the audio
            this.audio.load();
        });
    }

    /**
     * Pause current playback
     */
    pause() {
        if (!this.audio || !this.isPlaying || this.isPaused) {
            return;
        }

        this.audio.pause();
        this.isPaused = true;
        this._stopProgressUpdates();
    }

    /**
     * Resume paused playback
     */
    resume() {
        if (!this.audio || !this.isPaused) {
            return;
        }

        this.audio.play()
            .then(() => {
                this.isPaused = false;
                this._startProgressUpdates();
            })
            .catch(error => {
                console.error('Resume failed:', error);
            });
    }

    /**
     * Stop playback and cleanup
     */
    stop() {
        if (!this.audio) {
            return;
        }

        this._stopProgressUpdates();
        
        this.audio.pause();
        this.audio.currentTime = 0;
        
        // Cleanup
        if (this.audio.src) {
            URL.revokeObjectURL(this.audio.src);
        }
        
        this.audio = null;
        this.isPlaying = false;
        this.isPaused = false;
    }

    /**
     * Get current playback progress (0-100)
     * @returns {number} Progress percentage
     */
    getProgress() {
        if (!this.audio || !this.audio.duration) {
            return 0;
        }

        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        return Math.min(100, Math.max(0, progress));
    }

    /**
     * Get current playback time in seconds
     * @returns {number} Current time
     */
    getCurrentTime() {
        return this.audio ? this.audio.currentTime : 0;
    }

    /**
     * Get total duration in seconds
     * @returns {number} Duration
     */
    getDuration() {
        return this.audio ? this.audio.duration : 0;
    }

    /**
     * Set callback for playback completion
     * @param {Function} callback - Function to call when playback completes
     */
    onComplete(callback) {
        this.onCompleteCallback = callback;
    }

    /**
     * Check if audio is currently playing
     * @returns {boolean}
     */
    isCurrentlyPlaying() {
        return this.isPlaying && !this.isPaused;
    }

    /**
     * Check if audio is paused
     * @returns {boolean}
     */
    isCurrentlyPaused() {
        return this.isPaused;
    }

    /**
     * Start progress update interval
     * @private
     */
    _startProgressUpdates() {
        if (this.progressUpdateInterval) {
            return;
        }

        // Update progress every 100ms
        this.progressUpdateInterval = setInterval(() => {
            if (!this.isPlaying || this.isPaused) {
                this._stopProgressUpdates();
            }
        }, 100);
    }

    /**
     * Stop progress update interval
     * @private
     */
    _stopProgressUpdates() {
        if (this.progressUpdateInterval) {
            clearInterval(this.progressUpdateInterval);
            this.progressUpdateInterval = null;
        }
    }

    /**
     * Handle playback completion
     * @private
     */
    _handlePlaybackComplete() {
        this.isPlaying = false;
        this.isPaused = false;
        this._stopProgressUpdates();

        // Call completion callback if set
        if (this.onCompleteCallback) {
            this.onCompleteCallback();
        }
    }

    /**
     * Replay the last played audio
     * @returns {Promise<void>}
     */
    async replay() {
        if (!this.currentAudioData) {
            throw new Error('No audio to replay');
        }

        return this.play(this.currentAudioData, this.currentFormat);
    }

    /**
     * Set playback volume (0.0 to 1.0)
     * @param {number} volume - Volume level
     */
    setVolume(volume) {
        if (this.audio) {
            this.audio.volume = Math.min(1.0, Math.max(0.0, volume));
        }
    }

    /**
     * Get current volume (0.0 to 1.0)
     * @returns {number} Volume level
     */
    getVolume() {
        return this.audio ? this.audio.volume : 1.0;
    }

    /**
     * Release resources
     */
    release() {
        this.stop();
        this.currentAudioData = null;
        this.currentFormat = null;
        this.onCompleteCallback = null;
    }
}

// Export for use in other modules (CommonJS compatibility)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioPlayback;
}
