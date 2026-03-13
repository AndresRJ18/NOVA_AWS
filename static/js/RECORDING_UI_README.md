# RecordingUI Component

## Overview

The RecordingUI component manages voice recording controls and visual feedback for the Nova Sonic Voice Integration. It coordinates between AudioCapture, AudioPlayback, and WebSocketClient modules to provide a complete voice interaction interface.

## Features

### Recording Controls (Task 3.3)

1. **Start Recording Button**
   - Visible when audio state is `idle`
   - Initiates microphone capture
   - Blue gradient styling with icon

2. **Stop Recording Button**
   - Visible when audio state is `recording`
   - Stops capture and sends audio to server
   - Red gradient styling with icon

3. **Animated Volume Indicator**
   - Visible when audio state is `recording`
   - Shows real-time microphone volume (0-100)
   - Animated pulsing rings for visual feedback
   - Color-coded volume bar (gray/blue/green)

4. **Processing Spinner**
   - Visible when audio state is `processing`
   - Animated spinner with "Procesando audio..." text
   - Indicates audio is being transcribed

5. **Playback Indicator**
   - Visible when audio state is `speaking`
   - Animated sound waves
   - Shows "Reproduciendo..." text

6. **Disabled Controls During Playback**
   - Recording controls are disabled when system is speaking
   - Prevents conflicting audio operations
   - Re-enabled automatically when playback completes

### Playback Controls (Task 3.6)

1. **Playback Progress Bar**
   - Visible when audio state is `speaking`
   - Shows real-time playback position (0-100%)
   - Smooth gradient animation
   - Updates every 100ms

2. **Pause Button**
   - Visible when audio state is `speaking`
   - Stops audio playback immediately
   - Circular button with pause icon
   - Returns to idle state

3. **Replay Button**
   - Visible when audio state is `speaking`
   - Replays the last audio output
   - Circular button with replay icon
   - Stores last audio for replay

4. **Auto-Enable Recording Controls**
   - Recording controls automatically enabled when playback completes
   - Smooth transition from `speaking` to `idle` state
   - Progress bar resets to 0%

## Audio States

The component manages four audio states:

- `idle`: Ready to record, shows Start Recording button
- `recording`: Actively recording, shows Stop button and volume indicator
- `processing`: Transcribing audio, shows processing spinner
- `speaking`: Playing audio output, shows playback indicator

## Usage

### Basic Setup

```javascript
// Create RecordingUI instance
const recordingUI = new RecordingUI('container-id');

// Create module instances
const audioCapture = new AudioCapture();
const audioPlayback = new AudioPlayback();
const websocketClient = new WebSocketClient();

// Set modules
recordingUI.setModules(audioCapture, audioPlayback, websocketClient);
```

### Event Callbacks

```javascript
// State change callback
recordingUI.onStateChange((newState, oldState) => {
    console.log(`State: ${oldState} -> ${newState}`);
});

// Recording complete callback
recordingUI.onRecordingComplete((audioData) => {
    console.log('Audio captured:', audioData.byteLength, 'bytes');
});

// Error callback
recordingUI.onError((error) => {
    console.error('Error:', error.message);
});
```

### Manual Control

```javascript
// Start recording
await recordingUI.startRecording();

// Stop recording
await recordingUI.stopRecording();

// Play audio output
await recordingUI.playAudio(audioData, 'mp3');

// Pause playback
recordingUI.pausePlayback();

// Replay last audio
await recordingUI.replayLastAudio();

// Set state manually (for external control)
recordingUI.setAudioState('speaking');

// Get current state
const state = recordingUI.getAudioState();

// Get volume level
const volume = recordingUI.getVolumeLevel();

// Get playback progress
const progress = recordingUI.getPlaybackProgress();

// Check if controls are enabled
const enabled = recordingUI.areControlsEnabled();
```

## Requirements Validated

This implementation validates the following requirements:

### Recording Controls (Task 3.3)
- **Requirement 1.2**: Visual indicator during recording
- **Requirement 5.1**: "Start Recording" button when idle
- **Requirement 5.2**: Animated indicator during recording
- **Requirement 5.3**: "Stop Recording" button during recording
- **Requirement 5.4**: Processing indicator while transcribing
- **Requirement 5.5**: Disabled controls while system is speaking
- **Requirement 6.1**: Playback indicator when speaking

### Playback Controls (Task 3.6)
- **Requirement 6.1**: Playback indicator with "Reproduciendo" text
- **Requirement 6.2**: Pause button to stop audio playback
- **Requirement 6.3**: Replay button to repeat last audio
- **Requirement 6.4**: Progress bar showing playback position
- **Requirement 6.5**: Auto-enable recording controls when playback completes

## Testing

Open `recording-ui-test.html` in a browser to test the component:

```bash
# Open in browser
open static/js/recording-ui-test.html
```

The test page provides:
- Manual state control buttons
- Real-time status display
- Simulated volume updates
- Console logging for debugging

## Styling

The component uses `recording-ui.css` which includes:

- Modern gradient buttons
- Smooth animations
- Dark theme support
- Responsive design
- Accessibility features (focus states, reduced motion)

## Browser Compatibility

- Chrome 89+
- Firefox 85+
- Safari 14.1+
- Edge 89+

## Dependencies

- `audio-capture.js`: Microphone capture
- `audio-playback.js`: Audio playback
- `websocket-client.js`: Server communication
- `recording-ui.css`: Component styles

## Architecture

```
RecordingUI
├── State Management
│   ├── audioState (idle/recording/processing/speaking)
│   ├── volumeLevel (0-100)
│   ├── playbackProgress (0-100)
│   ├── lastAudio (for replay)
│   └── lastError
├── UI Elements
│   ├── Start Recording Button
│   ├── Stop Recording Button
│   ├── Volume Indicator
│   ├── Processing Spinner
│   ├── Playback Indicator
│   ├── Progress Bar
│   ├── Pause Button
│   └── Replay Button
└── Module Integration
    ├── AudioCapture (microphone)
    ├── AudioPlayback (speaker)
    └── WebSocketClient (server)
```

## Next Steps

After implementing playback controls (Task 3.6), the next tasks are:

- **Task 3.7**: Write property test for playback control functionality
- **Task 3.8**: Write property test for playback progress indication
- **Task 3.9**: Write property test for automatic recording enablement
- **Task 3.10**: Enhance volume level indicator
- **Task 3.12**: Implement mode switching UI (voice ↔ text)

## Notes

- Volume updates occur every 100ms for smooth visualization
- Progress updates occur every 100ms for smooth progress bar
- Recording controls are automatically disabled during playback
- Recording controls are automatically re-enabled when playback completes
- Audio data is sent to server via WebSocket on stop
- Last audio is stored for replay functionality
- Component handles errors gracefully with callbacks
- All animations respect `prefers-reduced-motion` setting
