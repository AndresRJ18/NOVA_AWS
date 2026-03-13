/**
 * WebSocketClient Module
 * 
 * Manages WebSocket connection for bidirectional real-time communication.
 * Handles audio streaming, text messages, and connection health monitoring.
 * 
 * Requirements: 1.5, 8.1, 8.2, 11.3
 */

export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 1000; // 1 second
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000; // 30 seconds
        this.lastPongTime = null;
        
        // Callbacks
        this.onTranscriptCallback = null;
        this.onAudioCallback = null;
        this.onErrorCallback = null;
        this.onConnectCallback = null;
        this.onDisconnectCallback = null;
        this.onReconnectingCallback = null;
    }

    /**
     * Connect to WebSocket server
     * @param {string} sessionId - Session identifier
     * @param {string} wsUrl - WebSocket URL (optional, defaults to current host)
     * @returns {Promise<void>}
     */
    async connect(sessionId, wsUrl = null) {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            throw new Error('Already connected or connecting');
        }

        this.sessionId = sessionId;
        this.isConnecting = true;

        // Construct WebSocket URL
        if (!wsUrl) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            wsUrl = `${protocol}//${host}/ws/${sessionId}`;
        }

        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(wsUrl);

                // Connection opened
                this.ws.addEventListener('open', () => {
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                    this.lastPongTime = Date.now();
                    
                    // Start heartbeat
                    this._startHeartbeat();
                    
                    if (this.onConnectCallback) {
                        this.onConnectCallback();
                    }
                    
                    resolve();
                });

                // Message received
                this.ws.addEventListener('message', (event) => {
                    this._handleMessage(event);
                });

                // Connection closed
                this.ws.addEventListener('close', (event) => {
                    this.isConnecting = false;
                    this._stopHeartbeat();
                    
                    if (this.onDisconnectCallback) {
                        this.onDisconnectCallback(event.code, event.reason);
                    }
                    
                    // Attempt reconnection if not a clean close
                    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this._attemptReconnect();
                    }
                });

                // Connection error
                this.ws.addEventListener('error', (event) => {
                    this.isConnecting = false;
                    
                    const error = new Error('WEBSOCKET_ERROR: Connection error occurred');
                    
                    if (this.onErrorCallback) {
                        this.onErrorCallback(error);
                    }
                    
                    reject(error);
                });

            } catch (error) {
                this.isConnecting = false;
                reject(new Error(`WEBSOCKET_CONNECTION_FAILED: ${error.message}`));
            }
        });
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this._stopHeartbeat();
        
        if (this.ws) {
            // Close with normal closure code
            this.ws.close(1000, 'Client disconnecting');
            this.ws = null;
        }
        
        this.sessionId = null;
        this.reconnectAttempts = 0;
    }

    /**
     * Send audio data to server
     * @param {ArrayBuffer} audioData - Audio data to send
     * @param {string} format - Audio format ('pcm', 'opus', 'mp3')
     */
    sendAudio(audioData, format = 'pcm') {
        if (!this.isConnected()) {
            throw new Error('WEBSOCKET_DISCONNECTED: Not connected to server');
        }

        // Create message object
        const message = {
            type: 'audio',
            format: format,
            timestamp: Date.now()
        };

        // Send message header as JSON
        const messageJson = JSON.stringify(message);
        
        // For binary data, we'll send JSON first, then binary
        // In a real implementation, you might use a binary protocol
        // For simplicity, we'll base64 encode the audio data
        const base64Audio = this._arrayBufferToBase64(audioData);
        message.data = base64Audio;
        
        this.ws.send(JSON.stringify(message));
    }

    /**
     * Send text message to server
     * @param {string} text - Text message to send
     */
    sendText(text) {
        if (!this.isConnected()) {
            throw new Error('WEBSOCKET_DISCONNECTED: Not connected to server');
        }

        const message = {
            type: 'text',
            text: text,
            timestamp: Date.now()
        };

        this.ws.send(JSON.stringify(message));
    }

    /**
     * Send ping to keep connection alive
     * @private
     */
    _sendPing() {
        if (!this.isConnected()) {
            return;
        }

        const message = {
            type: 'ping',
            timestamp: Date.now()
        };

        this.ws.send(JSON.stringify(message));
    }

    /**
     * Check if connected to server
     * @returns {boolean}
     */
    isConnected() {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Set callback for transcript messages
     * @param {Function} callback - Function(text: string)
     */
    onTranscript(callback) {
        this.onTranscriptCallback = callback;
    }

    /**
     * Set callback for audio messages
     * @param {Function} callback - Function(audioData: ArrayBuffer, format: string)
     */
    onAudio(callback) {
        this.onAudioCallback = callback;
    }

    /**
     * Set callback for error messages
     * @param {Function} callback - Function(error: Error)
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Set callback for connection established
     * @param {Function} callback - Function()
     */
    onConnect(callback) {
        this.onConnectCallback = callback;
    }

    /**
     * Set callback for disconnection
     * @param {Function} callback - Function(code: number, reason: string)
     */
    onDisconnect(callback) {
        this.onDisconnectCallback = callback;
    }

    /**
     * Set callback for reconnection attempts
     * @param {Function} callback - Function(attempt: number, maxAttempts: number)
     */
    onReconnecting(callback) {
        this.onReconnectingCallback = callback;
    }

    /**
     * Handle incoming WebSocket message
     * @param {MessageEvent} event - WebSocket message event
     * @private
     */
    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'transcript':
                    if (this.onTranscriptCallback && message.text) {
                        this.onTranscriptCallback(message.text);
                    }
                    break;

                case 'audio':
                    if (this.onAudioCallback && message.data) {
                        // Decode base64 audio data
                        const audioData = this._base64ToArrayBuffer(message.data);
                        const format = message.format || 'mp3';
                        this.onAudioCallback(audioData, format);
                    }
                    break;

                case 'error':
                    if (this.onErrorCallback) {
                        const error = new Error(message.message || 'Unknown error');
                        error.code = message.code;
                        error.recoverable = message.recoverable !== false;
                        this.onErrorCallback(error);
                    }
                    break;

                case 'pong':
                    // Update last pong time for heartbeat monitoring
                    this.lastPongTime = Date.now();
                    break;

                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
            if (this.onErrorCallback) {
                this.onErrorCallback(new Error('MESSAGE_PARSE_ERROR: Invalid message format'));
            }
        }
    }

    /**
     * Start heartbeat to keep connection alive
     * @private
     */
    _startHeartbeat() {
        if (this.heartbeatInterval) {
            return;
        }

        // Send ping every 30 seconds
        this.heartbeatInterval = setInterval(() => {
            // Check if we received a pong recently
            const timeSinceLastPong = Date.now() - this.lastPongTime;
            
            if (timeSinceLastPong > this.heartbeatTimeout * 2) {
                // No pong received for too long, connection might be dead
                console.warn('Heartbeat timeout, closing connection');
                this.disconnect();
                this._attemptReconnect();
            } else {
                // Send ping
                this._sendPing();
            }
        }, this.heartbeatTimeout);
    }

    /**
     * Stop heartbeat
     * @private
     */
    _stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Attempt to reconnect to server
     * @private
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            // All reconnection attempts failed - trigger fallback
            const error = new Error('websocket_reconnect_failed: Maximum reconnection attempts reached');
            error.code = 'websocket_reconnect_failed';
            error.recoverable = false;
            
            if (this.onErrorCallback) {
                this.onErrorCallback(error);
            }
            return;
        }

        this.reconnectAttempts++;
        
        if (this.onReconnectingCallback) {
            this.onReconnectingCallback(this.reconnectAttempts, this.maxReconnectAttempts);
        }

        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        // Wait 1 second before reconnecting (fixed delay as per requirements 8.3, 8.4)
        setTimeout(() => {
            if (this.sessionId) {
                this.connect(this.sessionId).catch(error => {
                    console.error('Reconnection failed:', error);
                    // Will trigger another reconnect attempt via close event
                });
            }
        }, this.reconnectDelay);
    }

    /**
     * Convert ArrayBuffer to base64 string
     * @param {ArrayBuffer} buffer - Buffer to convert
     * @returns {string} Base64 encoded string
     * @private
     */
    _arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Convert base64 string to ArrayBuffer
     * @param {string} base64 - Base64 encoded string
     * @returns {ArrayBuffer} Decoded buffer
     * @private
     */
    _base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    /**
     * Get connection state
     * @returns {string} Connection state ('connecting', 'open', 'closing', 'closed')
     */
    getConnectionState() {
        if (!this.ws) {
            return 'closed';
        }

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'open';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'closed';
            default:
                return 'unknown';
        }
    }

    /**
     * Get reconnection attempts count
     * @returns {number}
     */
    getReconnectAttempts() {
        return this.reconnectAttempts;
    }

    /**
     * Get maximum reconnection attempts
     * @returns {number}
     */
    getMaxReconnectAttempts() {
        return this.maxReconnectAttempts;
    }

    /**
     * Set maximum reconnection attempts
     * @param {number} max - Maximum attempts
     */
    setMaxReconnectAttempts(max) {
        this.maxReconnectAttempts = Math.max(0, max);
    }
}

// Export for use in other modules (CommonJS compatibility)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
