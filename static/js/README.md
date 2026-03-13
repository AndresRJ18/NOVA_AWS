# Nova Sonic Voice Integration - Frontend Modules

Browser-based audio modules for the Nova Sonic Voice Integration feature.

## Modules

- [AudioCapture](#audiocapture-module) - Microphone audio capture
- [AudioPlayback](#audioplayback-module) - Audio playback
- [WebSocketClient](#websocketclient-module) - Real-time communication

---

# AudioCapture Module

Browser-based audio capture module for the Nova Sonic Voice Integration feature.

## Overview

The `AudioCapture` class provides a simple interface for capturing audio from the user's microphone using the Web Audio API. It captures audio in 16kHz, 16-bit PCM format, which is compatible with Amazon Nova Sonic.

## Features

- ✅ Microphone permission handling
- ✅ Real-time audio capture at 16kHz, 16-bit PCM
- ✅ Real-time volume level calculation (0-100)
- ✅ Browser compatibility detection
- ✅ Automatic audio format conversion
- ✅ Chunk-based streaming support
- ✅ Clean resource management

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome  | 89+     | ✅ Supported |
| Firefox | 85+     | ✅ Supported |
| Safari  | 14.1+   | ✅ Supported |
| Edge    | 89+     | ✅ Supported |

## Usage

### Basic Example

```javascript
// Create instance
const audioCapture = new AudioCapture();

// Check browser support
if (!audioCapture.isSupported()) {
    console.error('Browser does not support audio capture');
    return;
}

// Request microphone permission
try {
    await audioCapture.requestPermission();
    console.log('Permission granted');
} catch (error) {
    console.error('Permission denied:', error.message);
    return;
}

// Start capturing with chunk callback
await audioCapture.startCapture((audioChunk) => {
    console.log('Received audio chunk:', audioChunk.byteLength, 'bytes');
    // Send chunk to server via WebSocket
    websocket.send(audioChunk);
});

// Get real-time volume level
setInterval(() => {
    const volume = audioCapture.getVolumeLevel();
    console.log('Volume:', volume, '%');
}, 100);

// Stop capture and get complete audio
const completeAudio = audioCapture.stopCapture();
console.log('Total audio size:', completeAudio.byteLength, 'bytes');

// Cleanup
audioCapture.release();
```

### Integration with WebSocket

```javascript
const audioCapture = new AudioCapture();
const websocket = new WebSocket('wss://your-server.com/ws');

// Start streaming to server
await audioCapture.startCapture((audioChunk) => {
    if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(audioChunk);
    }
});

// Stop and send final message
const finalAudio = audioCapture.stopCapture();
websocket.send(JSON.stringify({ type: 'audio_complete' }));
```

## API Reference

### Constructor

```javascript
new AudioCapture()
```

Creates a new AudioCapture instance with default settings:
- Sample rate: 16kHz
- Channels: 1 (mono)
- Bit depth: 16-bit
- Format: PCM

### Methods

#### `isSupported(): boolean`

Check if the browser supports required audio APIs.

**Returns:** `true` if supported, `false` otherwise

```javascript
if (audioCapture.isSupported()) {
    // Proceed with audio capture
}
```

#### `requestPermission(): Promise<boolean>`

Request microphone permission from the user.

**Returns:** Promise that resolves to `true` if permission granted

**Throws:**
- `MICROPHONE_PERMISSION_DENIED` - User denied permission
- `MICROPHONE_NOT_AVAILABLE` - No microphone device found
- `AUDIO_CAPTURE_FAILED` - Other capture errors

```javascript
try {
    await audioCapture.requestPermission();
} catch (error) {
    if (error.message.includes('PERMISSION_DENIED')) {
        // Show permission instructions
    }
}
```

#### `startCapture(onAudioChunk): Promise<void>`

Start capturing audio from the microphone.

**Parameters:**
- `onAudioChunk` (Function): Callback function called for each audio chunk
  - Receives: `ArrayBuffer` containing 16-bit PCM audio data

**Returns:** Promise that resolves when capture starts

```javascript
await audioCapture.startCapture((chunk) => {
    console.log('Chunk size:', chunk.byteLength);
});
```

#### `stopCapture(): ArrayBuffer`

Stop capturing audio and return the complete audio data.

**Returns:** `ArrayBuffer` containing all captured audio as 16-bit PCM

**Throws:** Error if not currently capturing

```javascript
const audioData = audioCapture.stopCapture();
console.log('Total size:', audioData.byteLength);
```

#### `getVolumeLevel(): number`

Get the current real-time volume level.

**Returns:** Volume level from 0 to 100

```javascript
const volume = audioCapture.getVolumeLevel();
// Update UI volume indicator
volumeBar.style.width = volume + '%';
```

#### `getAudioFormat(): Object`

Get information about the audio format.

**Returns:** Object with format details:
```javascript
{
    sampleRate: 16000,
    channels: 1,
    bitDepth: 16,
    format: 'pcm'
}
```

#### `release(): void`

Release all audio resources and stop the microphone.

```javascript
// Always call when done
audioCapture.release();
```

## Audio Format

The module captures audio in the following format:

- **Sample Rate:** 16,000 Hz (16kHz)
- **Bit Depth:** 16-bit signed integer
- **Channels:** 1 (mono)
- **Encoding:** PCM (Pulse Code Modulation)
- **Byte Order:** Little-endian

This format is compatible with Amazon Nova Sonic's audio input requirements.

## Error Handling

The module throws descriptive errors with error codes:

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `MICROPHONE_PERMISSION_DENIED` | User denied microphone access | Grant permission in browser settings |
| `MICROPHONE_NOT_AVAILABLE` | No microphone device found | Connect a microphone |
| `AUDIO_CAPTURE_FAILED` | General capture failure | Check browser console, try refresh |

Example error handling:

```javascript
try {
    await audioCapture.requestPermission();
} catch (error) {
    const errorCode = error.message.split(':')[0];
    
    switch (errorCode) {
        case 'MICROPHONE_PERMISSION_DENIED':
            showError('Please grant microphone permission');
            break;
        case 'MICROPHONE_NOT_AVAILABLE':
            showError('No microphone found. Please connect one.');
            break;
        default:
            showError('Audio capture failed. Please try again.');
    }
}
```

## Testing

A test page is provided at `audio-capture-test.html` to verify functionality:

1. Open `audio-capture-test.html` in a browser
2. Click "Request Permission" and grant microphone access
3. Click "Start Capture" to begin recording
4. Speak into your microphone (watch the volume meter)
5. Click "Stop Capture" to finish

The test page displays:
- Browser support status
- Audio format information
- Real-time volume level
- Capture duration and data size
- Number of chunks received

## Performance Considerations

- **Buffer Size:** Uses 4096 samples per chunk for good latency/performance balance
- **Memory:** Stores all chunks in memory until `stopCapture()` is called
- **CPU:** Minimal processing (volume calculation + format conversion)
- **Latency:** ~100ms typical latency from microphone to callback

## Best Practices

1. **Always check support first:**
   ```javascript
   if (!audioCapture.isSupported()) {
       // Fallback to text mode
   }
   ```

2. **Request permission early:**
   ```javascript
   // Request on user interaction (button click)
   button.onclick = async () => {
       await audioCapture.requestPermission();
   };
   ```

3. **Handle errors gracefully:**
   ```javascript
   try {
       await audioCapture.startCapture(onChunk);
   } catch (error) {
       // Show user-friendly error message
       // Offer text mode as fallback
   }
   ```

4. **Always cleanup:**
   ```javascript
   window.addEventListener('beforeunload', () => {
       audioCapture.release();
   });
   ```

5. **Monitor volume for user feedback:**
   ```javascript
   setInterval(() => {
       const volume = audioCapture.getVolumeLevel();
       updateVolumeIndicator(volume);
   }, 100);
   ```

## Requirements Validation

This module satisfies the following requirements:

- ✅ **Requirement 1.1:** Audio capture activation on user interaction
- ✅ **Requirement 1.4:** PCM 16-bit, 16kHz format compatible with Nova Sonic
- ✅ **Requirement 5.6:** Real-time volume level calculation
- ✅ **Requirement 11.1:** Microphone permission request handling
- ✅ **Requirement 11.2:** Web Audio API usage for capture

## Future Enhancements

Potential improvements for future versions:

- [ ] AudioWorklet support for better performance
- [ ] Configurable sample rate and bit depth
- [ ] Noise suppression and echo cancellation controls
- [ ] Audio quality pre-validation
- [ ] Automatic silence detection
- [ ] Support for stereo capture

## License

Part of the Mock Interview Coach - Nova Sonic Voice Integration feature.


---

# AudioPlayback Module

Browser-based audio playback module using HTML5 Audio API.

## Overview

The `AudioPlayback` class provides a simple interface for playing audio received from the server. It supports progressive playback (streaming) for MP3 and Opus formats with automatic format detection.

## Features

- ✅ MP3 and Opus format support
- ✅ Automatic format detection
- ✅ Progressive playback (streaming)
- ✅ Play, pause, resume, stop controls
- ✅ Real-time progress tracking (0-100%)
- ✅ Replay functionality
- ✅ Volume control
- ✅ Completion callbacks
- ✅ Clean resource management

## Browser Compatibility

| Browser | MP3 | Opus |
|---------|-----|------|
| Chrome  | ✅  | ✅   |
| Firefox | ✅  | ✅   |
| Safari  | ✅  | ❌   |
| Edge    | ✅  | ✅   |

**Note:** Safari does not support Opus. Use MP3 for maximum compatibility.

## Usage

### Basic Example

```javascript
// Create instance
const audioPlayback = new AudioPlayback();

// Check format support
const supported = audioPlayback.getSupportedFormats();
console.log('MP3:', supported.mp3, 'Opus:', supported.opus);

// Play audio from ArrayBuffer
const audioData = /* ArrayBuffer from server */;
await audioPlayback.play(audioData, 'mp3');

// Monitor progress
setInterval(() => {
    const progress = audioPlayback.getProgress();
    console.log('Progress:', progress, '%');
}, 100);

// Set completion callback
audioPlayback.onComplete(() => {
    console.log('Playback finished!');
    // Enable recording controls
});

// Control playback
audioPlayback.pause();
audioPlayback.resume();
audioPlayback.stop();

// Replay last audio
await audioPlayback.replay();

// Cleanup
audioPlayback.release();
```

### Integration with WebSocket

```javascript
const audioPlayback = new AudioPlayback();
const websocket = new WebSocket('wss://your-server.com/ws');

websocket.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'audio') {
        // Decode base64 audio
        const audioData = base64ToArrayBuffer(message.data);
        const format = message.format || 'mp3';
        
        // Play audio
        await audioPlayback.play(audioData, format);
    }
};

// Auto-enable recording when playback completes
audioPlayback.onComplete(() => {
    enableRecordingControls();
});
```

## API Reference

### Constructor

```javascript
new AudioPlayback()
```

Creates a new AudioPlayback instance.

### Methods

#### `getSupportedFormats(): Object`

Check which audio formats the browser supports.

**Returns:** Object with format support:
```javascript
{
    mp3: true,   // Browser supports MP3
    opus: false  // Browser does not support Opus
}
```

#### `play(audioData, format): Promise<void>`

Play audio from ArrayBuffer.

**Parameters:**
- `audioData` (ArrayBuffer): Audio data to play
- `format` (string, optional): Audio format ('mp3' or 'opus'). Auto-detected if not provided.

**Returns:** Promise that resolves when playback starts

**Throws:**
- `UNSUPPORTED_AUDIO_FORMAT` - Browser doesn't support the format
- `PLAYBACK_FAILED` - Playback failed to start
- `PLAYBACK_ERROR` - Error during playback

```javascript
await audioPlayback.play(audioData, 'mp3');
```

#### `pause(): void`

Pause current playback.

```javascript
audioPlayback.pause();
```

#### `resume(): void`

Resume paused playback.

```javascript
audioPlayback.resume();
```

#### `stop(): void`

Stop playback and cleanup resources.

```javascript
audioPlayback.stop();
```

#### `getProgress(): number`

Get current playback progress.

**Returns:** Progress percentage (0-100)

```javascript
const progress = audioPlayback.getProgress();
progressBar.style.width = progress + '%';
```

#### `getCurrentTime(): number`

Get current playback time in seconds.

**Returns:** Current time in seconds

```javascript
const time = audioPlayback.getCurrentTime();
console.log('Current time:', time, 's');
```

#### `getDuration(): number`

Get total audio duration in seconds.

**Returns:** Duration in seconds

```javascript
const duration = audioPlayback.getDuration();
console.log('Duration:', duration, 's');
```

#### `onComplete(callback): void`

Set callback for playback completion.

**Parameters:**
- `callback` (Function): Function to call when playback completes

```javascript
audioPlayback.onComplete(() => {
    console.log('Playback finished!');
    enableRecordingControls();
});
```

#### `isCurrentlyPlaying(): boolean`

Check if audio is currently playing.

**Returns:** `true` if playing, `false` otherwise

```javascript
if (audioPlayback.isCurrentlyPlaying()) {
    // Show pause button
}
```

#### `isCurrentlyPaused(): boolean`

Check if audio is paused.

**Returns:** `true` if paused, `false` otherwise

```javascript
if (audioPlayback.isCurrentlyPaused()) {
    // Show resume button
}
```

#### `replay(): Promise<void>`

Replay the last played audio.

**Returns:** Promise that resolves when replay starts

**Throws:** Error if no audio to replay

```javascript
await audioPlayback.replay();
```

#### `setVolume(volume): void`

Set playback volume.

**Parameters:**
- `volume` (number): Volume level (0.0 to 1.0)

```javascript
audioPlayback.setVolume(0.5); // 50% volume
```

#### `getVolume(): number`

Get current volume.

**Returns:** Volume level (0.0 to 1.0)

```javascript
const volume = audioPlayback.getVolume();
```

#### `release(): void`

Release all resources.

```javascript
audioPlayback.release();
```

## Audio Format Detection

The module automatically detects audio format from binary data:

- **MP3:** Checks for ID3 tag or MPEG frame sync
- **Opus:** Checks for OggS or EBML (WebM) header

If detection fails, defaults to MP3.

## Error Handling

| Error Code | Description | User Action |
|------------|-------------|-------------|
| `UNSUPPORTED_AUDIO_FORMAT` | Browser doesn't support format | Use different format or browser |
| `PLAYBACK_FAILED` | Playback failed to start | Check audio data, try again |
| `PLAYBACK_ERROR` | Error during playback | Check console, try again |

Example error handling:

```javascript
try {
    await audioPlayback.play(audioData, 'opus');
} catch (error) {
    if (error.message.includes('UNSUPPORTED')) {
        // Try MP3 fallback
        await audioPlayback.play(audioData, 'mp3');
    } else {
        showError('Playback failed. Please try again.');
    }
}
```

## Testing

A test page is provided at `audio-playback-test.html`:

1. Open `audio-playback-test.html` in a browser
2. Load an audio file (MP3 or Opus)
3. Click "Play" to start playback
4. Use pause/resume/stop controls
5. Monitor progress bar and time
6. Adjust volume slider
7. Click "Replay" to play again

## Requirements Validation

This module satisfies the following requirements:

- ✅ **Requirement 3.3:** Audio streaming to client for playback
- ✅ **Requirement 6.2:** Pause button for audio playback
- ✅ **Requirement 6.3:** Replay button for last audio
- ✅ **Requirement 6.4:** Progress bar during playback
- ✅ **Requirement 11.4:** HTML5 Audio API usage

---

# WebSocketClient Module

WebSocket client for bidirectional real-time communication.

## Overview

The `WebSocketClient` class manages WebSocket connections for streaming audio and text messages between client and server. It includes automatic reconnection, heartbeat monitoring, and comprehensive error handling.

## Features

- ✅ Bidirectional WebSocket communication
- ✅ Audio and text message support
- ✅ Automatic reconnection (up to 3 attempts)
- ✅ Heartbeat/ping-pong for connection health
- ✅ Connection state management
- ✅ Event callbacks for all message types
- ✅ Base64 encoding for binary data
- ✅ Clean resource management

## Usage

### Basic Example

```javascript
// Create instance
const wsClient = new WebSocketClient();

// Set up callbacks
wsClient.onConnect(() => {
    console.log('Connected!');
});

wsClient.onDisconnect((code, reason) => {
    console.log('Disconnected:', reason);
});

wsClient.onTranscript((text) => {
    console.log('Transcript:', text);
    displayTranscript(text);
});

wsClient.onAudio((audioData, format) => {
    console.log('Audio received:', audioData.byteLength, 'bytes');
    playAudio(audioData, format);
});

wsClient.onError((error) => {
    console.error('Error:', error.message);
    showError(error.message);
});

wsClient.onReconnecting((attempt, max) => {
    console.log(`Reconnecting... ${attempt}/${max}`);
});

// Connect to server
await wsClient.connect('session-123');

// Send text message
wsClient.sendText('Hello, server!');

// Send audio data
const audioData = /* ArrayBuffer from microphone */;
wsClient.sendAudio(audioData, 'pcm');

// Check connection
if (wsClient.isConnected()) {
    console.log('Connected to server');
}

// Disconnect
wsClient.disconnect();
```

### Complete Voice Integration

```javascript
const audioCapture = new AudioCapture();
const audioPlayback = new AudioPlayback();
const wsClient = new WebSocketClient();

// Connect WebSocket
await wsClient.connect('session-123');

// Handle incoming audio
wsClient.onAudio(async (audioData, format) => {
    await audioPlayback.play(audioData, format);
});

// Handle transcripts
wsClient.onTranscript((text) => {
    displayTranscript(text);
});

// Start recording and stream to server
await audioCapture.startCapture((audioChunk) => {
    if (wsClient.isConnected()) {
        wsClient.sendAudio(audioChunk, 'pcm');
    }
});

// Stop recording
const finalAudio = audioCapture.stopCapture();
wsClient.sendAudio(finalAudio, 'pcm');
```

## API Reference

### Constructor

```javascript
new WebSocketClient()
```

Creates a new WebSocketClient instance with default settings:
- Max reconnect attempts: 3
- Reconnect delay: 1 second
- Heartbeat interval: 30 seconds

### Methods

#### `connect(sessionId, wsUrl): Promise<void>`

Connect to WebSocket server.

**Parameters:**
- `sessionId` (string): Session identifier
- `wsUrl` (string, optional): WebSocket URL. Auto-detected if not provided.

**Returns:** Promise that resolves when connected

**Throws:** Error if connection fails

```javascript
await wsClient.connect('session-123');
// or with custom URL
await wsClient.connect('session-123', 'wss://example.com/ws/session-123');
```

#### `disconnect(): void`

Disconnect from server.

```javascript
wsClient.disconnect();
```

#### `sendAudio(audioData, format): void`

Send audio data to server.

**Parameters:**
- `audioData` (ArrayBuffer): Audio data
- `format` (string): Audio format ('pcm', 'opus', 'mp3')

**Throws:** Error if not connected

```javascript
wsClient.sendAudio(audioData, 'pcm');
```

#### `sendText(text): void`

Send text message to server.

**Parameters:**
- `text` (string): Text message

**Throws:** Error if not connected

```javascript
wsClient.sendText('Hello, server!');
```

#### `isConnected(): boolean`

Check if connected to server.

**Returns:** `true` if connected, `false` otherwise

```javascript
if (wsClient.isConnected()) {
    wsClient.sendText('Hello!');
}
```

#### `onTranscript(callback): void`

Set callback for transcript messages.

**Parameters:**
- `callback` (Function): Function(text: string)

```javascript
wsClient.onTranscript((text) => {
    console.log('Transcript:', text);
});
```

#### `onAudio(callback): void`

Set callback for audio messages.

**Parameters:**
- `callback` (Function): Function(audioData: ArrayBuffer, format: string)

```javascript
wsClient.onAudio((audioData, format) => {
    playAudio(audioData, format);
});
```

#### `onError(callback): void`

Set callback for error messages.

**Parameters:**
- `callback` (Function): Function(error: Error)

```javascript
wsClient.onError((error) => {
    console.error('Error:', error.message);
});
```

#### `onConnect(callback): void`

Set callback for connection established.

**Parameters:**
- `callback` (Function): Function()

```javascript
wsClient.onConnect(() => {
    console.log('Connected!');
});
```

#### `onDisconnect(callback): void`

Set callback for disconnection.

**Parameters:**
- `callback` (Function): Function(code: number, reason: string)

```javascript
wsClient.onDisconnect((code, reason) => {
    console.log('Disconnected:', reason);
});
```

#### `onReconnecting(callback): void`

Set callback for reconnection attempts.

**Parameters:**
- `callback` (Function): Function(attempt: number, maxAttempts: number)

```javascript
wsClient.onReconnecting((attempt, max) => {
    console.log(`Reconnecting... ${attempt}/${max}`);
});
```

#### `getConnectionState(): string`

Get current connection state.

**Returns:** State string ('connecting', 'open', 'closing', 'closed')

```javascript
const state = wsClient.getConnectionState();
console.log('State:', state);
```

#### `getReconnectAttempts(): number`

Get number of reconnection attempts.

**Returns:** Attempt count

```javascript
const attempts = wsClient.getReconnectAttempts();
```

#### `setMaxReconnectAttempts(max): void`

Set maximum reconnection attempts.

**Parameters:**
- `max` (number): Maximum attempts

```javascript
wsClient.setMaxReconnectAttempts(5);
```

## Message Protocol

### Client → Server Messages

```javascript
// Audio message
{
    type: 'audio',
    data: 'base64_encoded_audio',
    format: 'pcm',
    timestamp: 1234567890
}

// Text message
{
    type: 'text',
    text: 'Hello, server!',
    timestamp: 1234567890
}

// Ping message
{
    type: 'ping',
    timestamp: 1234567890
}
```

### Server → Client Messages

```javascript
// Transcript message
{
    type: 'transcript',
    text: 'Transcribed text',
    confidence: 0.95
}

// Audio message
{
    type: 'audio',
    data: 'base64_encoded_audio',
    format: 'mp3'
}

// Error message
{
    type: 'error',
    code: 'NOVA_SONIC_ERROR',
    message: 'Error description',
    recoverable: true
}

// Pong message
{
    type: 'pong',
    timestamp: 1234567890
}
```

## Connection Management

### Automatic Reconnection

The client automatically attempts to reconnect when the connection is lost:

1. First attempt: Immediate
2. Second attempt: 1 second delay
3. Third attempt: 2 seconds delay
4. After 3 failed attempts: Triggers error callback

### Heartbeat Monitoring

The client sends ping messages every 30 seconds to keep the connection alive:

- Ping sent every 30 seconds
- If no pong received for 60 seconds, connection is considered dead
- Automatic reconnection triggered

## Error Handling

| Error Code | Description | Recoverable |
|------------|-------------|-------------|
| `WEBSOCKET_ERROR` | Connection error | Yes (auto-reconnect) |
| `WEBSOCKET_CONNECTION_FAILED` | Initial connection failed | No |
| `WEBSOCKET_DISCONNECTED` | Not connected | Yes (reconnect) |
| `WEBSOCKET_RECONNECT_FAILED` | Max reconnect attempts reached | No |
| `MESSAGE_PARSE_ERROR` | Invalid message format | Yes |

Example error handling:

```javascript
wsClient.onError((error) => {
    if (error.message.includes('RECONNECT_FAILED')) {
        // Switch to text fallback mode
        enableTextMode();
        showError('Connection lost. Switched to text mode.');
    } else if (error.recoverable) {
        // Show temporary error, will auto-reconnect
        showWarning('Connection issue. Reconnecting...');
    } else {
        // Show permanent error
        showError('Connection failed. Please refresh the page.');
    }
});
```

## Testing

A test page is provided at `websocket-client-test.html`:

1. Open `websocket-client-test.html` in a browser
2. Enter session ID and WebSocket URL
3. Click "Connect"
4. Send text messages
5. Send audio files
6. Monitor message log
7. Test reconnection by disconnecting

**Note:** Requires a WebSocket server running.

## Requirements Validation

This module satisfies the following requirements:

- ✅ **Requirement 1.5:** WebSocket transmission with <500ms latency
- ✅ **Requirement 8.1:** WebSocket connection establishment
- ✅ **Requirement 8.2:** Connection maintained during session
- ✅ **Requirement 11.3:** WebSocket API usage for transmission

---

## Integration Example

Complete example integrating all three modules:

```javascript
// Initialize modules
const audioCapture = new AudioCapture();
const audioPlayback = new AudioPlayback();
const wsClient = new WebSocketClient();

// Connect WebSocket
await wsClient.connect('session-123');

// Handle incoming messages
wsClient.onTranscript((text) => {
    displayTranscript(text);
});

wsClient.onAudio(async (audioData, format) => {
    await audioPlayback.play(audioData, format);
});

wsClient.onError((error) => {
    console.error('WebSocket error:', error);
    if (!error.recoverable) {
        enableTextFallbackMode();
    }
});

// Auto-enable recording when playback completes
audioPlayback.onComplete(() => {
    enableRecordingButton();
});

// Start recording
async function startRecording() {
    await audioCapture.requestPermission();
    await audioCapture.startCapture((audioChunk) => {
        if (wsClient.isConnected()) {
            wsClient.sendAudio(audioChunk, 'pcm');
        }
    });
    
    // Update volume indicator
    setInterval(() => {
        const volume = audioCapture.getVolumeLevel();
        updateVolumeIndicator(volume);
    }, 100);
}

// Stop recording
function stopRecording() {
    const finalAudio = audioCapture.stopCapture();
    wsClient.sendAudio(finalAudio, 'pcm');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    audioCapture.release();
    audioPlayback.release();
    wsClient.disconnect();
});
```

## License

Part of the Mock Interview Coach - Nova Sonic Voice Integration feature.
