/**
 * VocalRehab Speech Recognition Module
 * =====================================
 * Handles browser-based speech recognition with special handling
 * for dysarthric speech patterns (longer timeouts, continuous mode,
 * multiple hypothesis capture).
 *
 * Key design decisions for dysarthria support:
 *   - maxAlternatives set to 5 to capture n-best hypotheses
 *   - Extended silence timeouts (default 10s vs typical 2-3s)
 *   - Auto-restart on unexpected recognition end
 *   - Continuous mode for longer utterance windows
 */

class SpeechHandler {
    /**
     * Initialize Web Speech API with configuration tuned for dysarthric speech.
     * @param {Object} options - Configuration options
     * @param {string}  options.language        - BCP-47 language tag (default 'en-US')
     * @param {boolean} options.continuous       - Keep listening after first result (default true)
     * @param {boolean} options.interimResults   - Emit partial hypotheses (default true)
     * @param {number}  options.maxAlternatives  - N-best list size (default 5)
     * @param {number}  options.timeoutMs        - Silence timeout in ms (default 10000)
     * @param {number}  options.maxRetries       - Auto-restart retry limit (default 3)
     */
    constructor(options = {}) {
        this.language       = options.language       || 'en-US';
        this.continuous     = options.continuous !== undefined ? options.continuous : true;
        this.interimResults = options.interimResults !== undefined ? options.interimResults : true;
        this.maxAlternatives = options.maxAlternatives || 5;
        this.timeoutMs      = options.timeoutMs      || 10000;
        this.maxRetries     = options.maxRetries     || 3;

        // Internal state
        this._recognition    = null;
        this._isListening    = false;
        this._retryCount     = 0;
        this._timeoutTimer   = null;
        this._lastAlternatives = [];
        this._lastInterimTranscript = '';
        this._state          = 'idle'; // 'idle' | 'listening' | 'processing' | 'error'
        this._intentionalStop = false;

        // Callbacks (set per-session via startListening)
        this._onResult = null;
        this._onError  = null;
        this._onEnd    = null;

        // Event listeners for UI state changes
        this._stateListeners = [];

        // Attempt to create recognition instance immediately
        this._initRecognition();
    }

    // ─── Browser support ────────────────────────────────────────────────

    /**
     * Check whether the current browser supports the Web Speech API.
     * @returns {{ supported: boolean, engine: string|null, message: string }}
     */
    checkSupport() {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            return {
                supported: false,
                engine: null,
                message:
                    'Speech recognition is not supported in this browser. ' +
                    'Please use Google Chrome (v33+) or Microsoft Edge (v79+).'
            };
        }

        const engine = window.SpeechRecognition ? 'native' : 'webkit';
        return {
            supported: true,
            engine,
            message: `Speech recognition available (${engine} engine).`
        };
    }

    // ─── Internal initialisation ────────────────────────────────────────

    /** @private */
    _initRecognition() {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) return;

        this._recognition = new SpeechRecognition();
        this._recognition.lang            = this.language;
        this._recognition.continuous      = this.continuous;
        this._recognition.interimResults  = this.interimResults;
        this._recognition.maxAlternatives = this.maxAlternatives;

        // ── Event wiring ────────────────────────────────────────────
        this._recognition.onresult    = (e) => this._handleResult(e);
        this._recognition.onerror     = (e) => this._handleError(e);
        this._recognition.onend       = ()  => this._handleEnd();
        this._recognition.onsoundstart = () => this._handleSoundStart();
        this._recognition.onsoundend   = () => this._handleSoundEnd();
        this._recognition.onnomatch    = () => this._handleNoMatch();
    }

    // ─── Public API ─────────────────────────────────────────────────────

    /**
     * Start listening for speech input.
     * @param {Function} onResult - Callback receiving { transcript, confidence, alternatives }
     * @param {Function} onError  - Callback receiving { error, message }
     * @param {Function} onEnd    - Callback invoked when recognition stops
     */
    startListening(onResult, onError, onEnd) {
        const support = this.checkSupport();
        if (!support.supported) {
            if (onError) onError({ error: 'not-supported', message: support.message });
            return;
        }

        // Re-init if needed (some browsers require a fresh instance)
        if (!this._recognition) {
            this._initRecognition();
        }

        this._onResult = onResult || null;
        this._onError  = onError  || null;
        this._onEnd    = onEnd    || null;

        this._intentionalStop = false;
        this._retryCount      = 0;
        this._lastAlternatives = [];

        try {
            this._recognition.start();
            this._isListening = true;
            this._setState('listening');
            this._startTimeout();
        } catch (err) {
            // Already started – stop first, then restart
            if (err.name === 'InvalidStateError') {
                this._recognition.stop();
                setTimeout(() => this.startListening(onResult, onError, onEnd), 200);
            } else {
                this._setState('error');
                if (this._onError) {
                    this._onError({ error: err.name, message: err.message });
                }
            }
        }
    }

    /**
     * Stop listening intentionally.
     * @param {boolean} [processPending=false] - Whether to deliver pending interim transcripts
     * @returns {boolean} - True if a pending transcript was immediately dispatched
     */
    stopListening(processPending = false) {
        this._intentionalStop = true;
        this._clearTimeout();

        const pendingText = this._lastInterimTranscript;
        const pendingAlts = this._lastAlternatives;

        if (this._recognition) {
            try {
                this._recognition.stop();
            } catch (_) {
                // already stopped – ignore
            }
        }
        this._isListening = false;
        this._setState('idle');

        // If requested or if we have pending interim text but no final result yet, deliver it!
        if (processPending && pendingText && this._onResult) {
            const finalAlts = pendingAlts.length > 0 ? pendingAlts : [{ transcript: pendingText, confidence: 0.8 }];
            this._lastInterimTranscript = '';
            this._lastAlternatives = [];
            this._onResult({
                transcript: pendingText,
                confidence: 0.8,
                alternatives: finalAlts
            });
            return true;
        }
        return false;
    }

    /**
     * Return all n-best hypotheses captured during the last recognition event.
     * @returns {Array<{ transcript: string, confidence: number }>}
     */
    getAlternatives() {
        return this._lastAlternatives.slice();
    }

    /**
     * Register a listener for state changes.
     * @param {Function} listener - Receives state string: 'listening'|'processing'|'idle'|'error'
     */
    onStateChange(listener) {
        if (typeof listener === 'function') {
            this._stateListeners.push(listener);
        }
    }

    /**
     * Remove a previously registered state-change listener.
     * @param {Function} listener
     */
    offStateChange(listener) {
        this._stateListeners = this._stateListeners.filter((l) => l !== listener);
    }

    /** @returns {boolean} */
    get isListening() {
        return this._isListening;
    }

    /** @returns {string} */
    get state() {
        return this._state;
    }

    // ─── Event handlers (private) ───────────────────────────────────────

    /** @private */
    _handleResult(event) {
        this._clearTimeout();
        this._setState('processing');

        const alternatives = [];
        let interimText = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];

            if (result.isFinal) {
                // Collect ALL alternatives from the n-best list
                for (let j = 0; j < result.length; j++) {
                    alternatives.push({
                        transcript: result[j].transcript.trim(),
                        confidence: result[j].confidence
                    });
                }
            } else if (result[0] && result[0].transcript) {
                interimText = result[0].transcript.trim();
            }
        }

        if (interimText) {
            this._lastInterimTranscript = interimText;
        }

        if (alternatives.length > 0) {
            this._lastAlternatives = alternatives;
            this._lastInterimTranscript = '';

            if (this._onResult) {
                this._onResult({
                    transcript: alternatives[0].transcript,
                    confidence: alternatives[0].confidence,
                    alternatives
                });
            }

            // After delivering a final result, stop to avoid duplicate processing
            this.stopListening(false);
        } else {
            // Interim result – user is still speaking or finishing
            this._startTimeout();
        }
    }

    /** @private */
    _handleError(event) {
        const errorMap = {
            'no-speech':        'No speech heard. Speak clearly or click the card directly!',
            'audio-capture':    'Microphone not found. Check your audio input device.',
            'not-allowed':      'Microphone blocked. Please allow microphone access in your browser bar.',
            'network':          'Network timeout with speech recognition service. You can also click the cards directly!',
            'aborted':          'Recognition stopped.',
            'service-not-available': 'Speech service is currently unavailable.'
        };

        const message = errorMap[event.error] || `Recognition notice: ${event.error}`;

        // If we have an interim transcript captured before the error, deliver that instead of failing!
        if (this._lastInterimTranscript && this._onResult) {
            const text = this._lastInterimTranscript;
            this._lastInterimTranscript = '';
            this.stopListening(false);
            this._onResult({
                transcript: text,
                confidence: 0.75,
                alternatives: [{ transcript: text, confidence: 0.75 }]
            });
            return;
        }

        // Fatal errors (e.g. microphone permission denied) must be displayed immediately
        if (event.error === 'not-allowed' || event.error === 'audio-capture') {
            this._setState('error');
            if (this._onError) {
                this._onError({ error: event.error, message });
            }
            return;
        }

        // Notify error listener cleanly without getting stuck
        this._setState('error');
        if (this._onError) {
            this._onError({ error: event.error, message });
        }
    }

    /** @private */
    _handleEnd() {
        this._clearTimeout();

        // If recognition ended but we had interim words, deliver them!
        if (this._lastInterimTranscript && this._onResult) {
            const text = this._lastInterimTranscript;
            this._lastInterimTranscript = '';
            this._isListening = false;
            this._setState('idle');
            this._onResult({
                transcript: text,
                confidence: 0.75,
                alternatives: [{ transcript: text, confidence: 0.75 }]
            });
            return;
        }

        if (!this._intentionalStop && this._isListening && this._retryCount < this.maxRetries) {
            this._retryCount++;
            try {
                this._recognition.start();
                this._startTimeout();
                return;
            } catch (_) {
                // Fall through to end
            }
        }

        this._isListening = false;
        this._setState('idle');
        if (this._onEnd) {
            this._onEnd();
        }
    }

    /** @private */
    _handleSoundStart() {
        // User has started producing sound – reset the timeout
        this._clearTimeout();
    }

    /** @private */
    _handleSoundEnd() {
        // Sound ended – give a short grace period (1.5s) then finalize
        this._startTimeout(1500);
    }

    /** @private */
    _handleNoMatch() {
        console.info('[SpeechHandler] No match detected.');
    }

    // ─── Timeout management ─────────────────────────────────────────────

    /** @private */
    _startTimeout(customMs = null) {
        this._clearTimeout();
        const duration = customMs || this.timeoutMs;
        this._timeoutTimer = setTimeout(() => {
            if (this._isListening) {
                // If we captured any interim text before silence, process it now!
                if (this._lastInterimTranscript && this._onResult) {
                    const text = this._lastInterimTranscript;
                    this._lastInterimTranscript = '';
                    this.stopListening(false);
                    this._onResult({
                        transcript: text,
                        confidence: 0.75,
                        alternatives: [{ transcript: text, confidence: 0.75 }]
                    });
                    return;
                }

                this.stopListening(false);
                if (this._onError) {
                    this._onError({
                        error: 'no-speech',
                        message: "I didn't hear anything. Tap the mic and try speaking, or click the card directly!"
                    });
                }
            }
        }, duration);
    }

    /** @private */
    _clearTimeout() {
        if (this._timeoutTimer) {
            clearTimeout(this._timeoutTimer);
            this._timeoutTimer = null;
        }
    }

    // ─── State management ───────────────────────────────────────────────

    /**
     * @private
     * @param {'listening'|'processing'|'idle'|'error'} newState
     */
    _setState(newState) {
        if (this._state === newState) return;
        const previousState = this._state;
        this._state = newState;
        for (const listener of this._stateListeners) {
            try {
                listener(newState, previousState);
            } catch (err) {
                console.error('[SpeechHandler] State listener error:', err);
            }
        }
    }
}

// Export for module bundlers; also attach to window for direct script usage.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpeechHandler;
}
window.SpeechHandler = SpeechHandler;
