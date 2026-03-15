/**
 * AudioWorklet processor for real-time PCM capture.
 * Runs in a dedicated audio rendering thread (no UI thread blocking).
 * Replaces the deprecated ScriptProcessorNode.
 */
class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this._bufferSize = 4096;
        this._buffer     = new Float32Array(this._bufferSize);
        this._offset     = 0;

        // Flush remaining samples when the main thread requests stop
        this.port.onmessage = (e) => {
            if (e.data === 'flush' && this._offset > 0) {
                this._sendBuffer(this._offset);
                this._offset = 0;
            }
        };
    }

    _sendBuffer(length) {
        let sum = 0;
        for (let j = 0; j < length; j++) sum += this._buffer[j] ** 2;
        const rms = Math.sqrt(sum / length);
        const pcm = new Int16Array(length);
        for (let j = 0; j < length; j++) {
            const s = Math.max(-1, Math.min(1, this._buffer[j]));
            pcm[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        this.port.postMessage({ pcm: pcm.buffer, rms }, [pcm.buffer]);
    }

    process(inputs) {
        const channel = inputs[0] && inputs[0][0];
        if (!channel) return true;

        for (let i = 0; i < channel.length; i++) {
            this._buffer[this._offset++] = channel[i];
            if (this._offset >= this._bufferSize) {
                this._sendBuffer(this._bufferSize);
                this._offset = 0;
            }
        }
        return true;
    }
}

registerProcessor('nova-pcm-processor', PCMProcessor);
