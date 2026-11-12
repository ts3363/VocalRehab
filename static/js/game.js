/**
 * VocalRehab Game Engine
 * ======================
 * Manages the gamified minimal-pair therapy experience.
 */

class VocalRehabGame {
    constructor() {
        this.score = 0;
        this.streak = 0;
        this.bestStreak = 0;
        this.trialsCompleted = 0;
        this.sessionId = null;
        this.userId = null;
        this.difficulty = 1;
        this.isListening = false;
        this.currentScenario = null;
        this.sessionLength = 15;
        this.gameType = 'direction';
        this.category = null;
        this.speech = null;
        this.startTime = null;

        this.encouragements = [
            "Amazing! 🎉", "You're on fire! 🔥", "Superstar! ⭐",
            "Fantastic! 💪", "Brilliant! 🌟", "Way to go! 🏆",
            "Perfect! 👏", "Outstanding! 🚀", "Incredible! 💯",
            "You rock! 🎸", "Wonderful! ✨", "So proud! 🥳",
            "Nailed it! 🎯", "Beautiful! 💖", "Champion! 🏅"
        ];
    }

    // -------------------------------------------------------- //
    //  INITIALIZATION
    // -------------------------------------------------------- //

    async init(userId, options = {}) {
        this.userId = userId;
        this.sessionLength = options.sessionLength || 15;
        this.gameType = options.gameType || 'direction';
        this.category = options.category || null;
        this.difficulty = options.difficulty || 1;

        // Initialize speech handler
        this.speech = new SpeechHandler({
            language: 'en-US',
            continuous: false,
            interimResults: true,
            maxAlternatives: 5,
            timeoutMs: 6000
        });

        const support = this.speech.checkSupport();
        if (!support.supported) {
            this.showStatus('⚠️ Speech recognition not supported in this browser. Please use Chrome.', 'error');
            return false;
        }

        // Start session via API
        try {
            const res = await fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    difficulty: this.difficulty
                })
            });
            const data = await res.json();
            this.sessionId = data.session_id;
            this.difficulty = data.difficulty;
        } catch (e) {
            console.error('Failed to start session:', e);
            this.showStatus('Failed to connect to server.', 'error');
            return false;
        }

        this.updateScoreboard();
        this.showStatus('🎮 Ready! Loading your first challenge...', 'info');

        // Spacebar listener for hands-free speech toggle
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.toggleListening();
            }
        });

        await this.loadNextPair();
        return true;
    }

    // -------------------------------------------------------- //
    //  SPEECH SYNTHESIS (HEAR WORD HELPER)
    // -------------------------------------------------------- //

    speakWord(word) {
        if (!word) return;
        if (!('speechSynthesis' in window)) {
            console.warn('SpeechSynthesis API not supported in this browser.');
            return;
        }
        try {
            window.speechSynthesis.cancel(); // Stop any pending speech
            const utter = new SpeechSynthesisUtterance(word);
            utter.lang = 'en-US';
            utter.rate = 0.85; // Slightly slower pacing for speech therapy
            utter.pitch = 1.0;
            window.speechSynthesis.speak(utter);
        } catch (e) {
            console.error('Speech synthesis error:', e);
        }
    }

    // -------------------------------------------------------- //
    //  LOAD NEXT PAIR
    // -------------------------------------------------------- //

    async loadNextPair() {
        if (this.trialsCompleted >= this.sessionLength) {
            await this.endSession();
            return;
        }

        try {
            let url = `/api/pair/next?game_type=${this.gameType}&difficulty=${this.difficulty}`;
            if (this.userId) url += `&user_id=${this.userId}`;
            if (this.category) url += `&category=${this.category}`;

            const res = await fetch(url);
            this.currentScenario = await res.json();
            this.renderScenario(this.currentScenario);
            this.showStatus(`🎯 Say "${this.currentScenario.target_word.toUpperCase()}" into the microphone!`, 'info');
        } catch (e) {
            console.error('Failed to load pair:', e);
            this.showStatus('Failed to load next challenge.', 'error');
        }
    }

    // -------------------------------------------------------- //
    //  RENDER GAME SCENARIO
    // -------------------------------------------------------- //

    renderScenario(scenario) {
        const arena = document.getElementById('game-arena');
        if (!arena) return;

        // Update character
        const character = document.getElementById('game-character');
        if (character) {
            character.textContent = scenario.character || '🧙‍♂️';
            character.classList.remove('celebrate', 'shake');
        }

        // Update Arena Header Prompt
        const promptTitle = document.getElementById('arena-prompt-title');
        const promptSubtitle = document.getElementById('arena-prompt-subtitle');
        if (promptTitle) {
            promptTitle.textContent = `Say the Target Word: "${scenario.target_word.toUpperCase()}"`;
        }
        if (promptSubtitle) {
            promptSubtitle.textContent = `Contrast /${scenario.word1}/ vs /${scenario.word2}/`;
        }

        // Update Left Option
        const leftOption = document.getElementById('option-left');
        const leftBadge = document.getElementById('option-left-badge');
        const btnListenLeft = document.getElementById('btn-listen-left');

        if (leftOption) {
            leftOption.querySelector('.option-hint').textContent = scenario.option_left.hint;
            leftOption.querySelector('.option-word').textContent = scenario.option_left.word;
            leftOption.classList.remove('correct-option', 'wrong-option', 'target-card', 'contrast-card');
            leftOption.style.cursor = 'pointer';
            leftOption.title = `Click or pronounce "${scenario.option_left.word}"`;
            leftOption.onclick = () => {
                this.showStatus(`👉 Card selected: "${scenario.option_left.word}". Analyzing...`, 'processing');
                this.processResult(scenario.option_left.word, [scenario.option_left.word]);
            };

            if (scenario.option_left.is_target) {
                leftOption.classList.add('target-card');
                leftOption.querySelector('.option-word').classList.add('target-highlight');
                if (leftBadge) {
                    leftBadge.textContent = '🎯 TARGET WORD';
                    leftBadge.className = 'option-role-badge';
                }
            } else {
                leftOption.classList.add('contrast-card');
                leftOption.querySelector('.option-word').classList.remove('target-highlight');
                if (leftBadge) {
                    leftBadge.textContent = 'CONTRAST';
                    leftBadge.className = 'option-role-badge';
                }
            }
        }

        if (btnListenLeft) {
            btnListenLeft.onclick = (e) => {
                e.stopPropagation();
                this.speakWord(scenario.option_left.word);
            };
        }

        // Update Right Option
        const rightOption = document.getElementById('option-right');
        const rightBadge = document.getElementById('option-right-badge');
        const btnListenRight = document.getElementById('btn-listen-right');

        if (rightOption) {
            rightOption.querySelector('.option-hint').textContent = scenario.option_right.hint;
            rightOption.querySelector('.option-word').textContent = scenario.option_right.word;
            rightOption.classList.remove('correct-option', 'wrong-option', 'target-card', 'contrast-card');
            rightOption.style.cursor = 'pointer';
            rightOption.title = `Click or pronounce "${scenario.option_right.word}"`;
            rightOption.onclick = () => {
                this.showStatus(`👉 Card selected: "${scenario.option_right.word}". Analyzing...`, 'processing');
                this.processResult(scenario.option_right.word, [scenario.option_right.word]);
            };

            if (scenario.option_right.is_target) {
                rightOption.classList.add('target-card');
                rightOption.querySelector('.option-word').classList.add('target-highlight');
                if (rightBadge) {
                    rightBadge.textContent = '🎯 TARGET WORD';
                    rightBadge.className = 'option-role-badge';
                }
            } else {
                rightOption.classList.add('contrast-card');
                rightOption.querySelector('.option-word').classList.remove('target-highlight');
                if (rightBadge) {
                    rightBadge.textContent = 'CONTRAST';
                    rightBadge.className = 'option-role-badge';
                }
            }
        }

        if (btnListenRight) {
            btnListenRight.onclick = (e) => {
                e.stopPropagation();
                this.speakWord(scenario.option_right.word);
            };
        }

        // Wire up top "Hear Target" button in mic console
        const btnHearTarget = document.getElementById('btn-hear-target');
        if (btnHearTarget) {
            btnHearTarget.onclick = () => {
                this.speakWord(scenario.target_word);
            };
        }

        // Update category badge
        const catBadge = document.getElementById('category-badge');
        if (catBadge) {
            const catName = scenario.category_name || scenario.category || 'Therapy';
            catBadge.innerHTML = `<i class="bi bi-tag-fill me-1"></i> ${catName}`;
        }

        // Update difficulty stars
        this.updateDifficultyStars(scenario.difficulty);

        // Update trial counter & progress bar
        const trialCurrent = this.trialsCompleted + 1;
        const trialCounter = document.getElementById('trial-counter');
        if (trialCounter) trialCounter.textContent = `${trialCurrent} / ${this.sessionLength}`;

        const pct = Math.min(100, Math.round((trialCurrent / this.sessionLength) * 100));
        const progressFill = document.getElementById('session-progress-bar');
        const progressPercent = document.getElementById('progress-percent');
        if (progressFill) progressFill.style.width = `${pct}%`;
        if (progressPercent) progressPercent.textContent = `${pct}% (${trialCurrent}/${this.sessionLength})`;

        // Enable mic button
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.disabled = false;
            micBtn.classList.remove('listening');
        }
    }

    // -------------------------------------------------------- //
    //  SPEECH RECOGNITION & INPUT
    // -------------------------------------------------------- //

    toggleListening() {
        if (this.isListening) {
            // User clicked while listening -> Stop and process whatever was heard!
            this.showStatus('⏳ Stopping and evaluating...', 'processing');
            if (this.speech) {
                this.speech.stopListening(true);
            }
            this.isListening = false;
            const micBtn = document.getElementById('mic-btn');
            if (micBtn) micBtn.classList.remove('listening');
            this.updateWaveform(false);
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (this.isListening || !this.currentScenario) return;
        this.isListening = true;
        this.startTime = Date.now();

        const micBtn = document.getElementById('mic-btn');
        if (micBtn) micBtn.classList.add('listening');

        this.updateWaveform(true);
        this.showStatus('🎤 Listening... Speak now! (Tap mic again to stop)', 'listening');

        this.speech.startListening(
            // onResult
            (data, maybeAlts) => {
                this.isListening = false;
                if (micBtn) micBtn.classList.remove('listening');
                this.updateWaveform(false);

                let transcript = '';
                let alternatives = [];

                if (typeof data === 'string') {
                    transcript = data;
                    alternatives = Array.isArray(maybeAlts) ? maybeAlts : [];
                } else if (data && typeof data === 'object') {
                    transcript = data.transcript || '';
                    if (Array.isArray(data.alternatives)) {
                        alternatives = data.alternatives.map(a => typeof a === 'string' ? a : (a.transcript || ''));
                    }
                }

                if (transcript && transcript.trim()) {
                    this.processResult(transcript.trim(), alternatives);
                } else {
                    this.showStatus("🤔 I didn't catch that. Tap the mic to try again, or click a card directly!", 'warning');
                }
            },
            // onError
            (error) => {
                this.isListening = false;
                if (micBtn) micBtn.classList.remove('listening');
                this.updateWaveform(false);

                const errCode = typeof error === 'object' && error.error ? error.error : error;
                const errMsg = typeof error === 'object' && error.message ? error.message : '';

                if (errCode === 'not-allowed') {
                    this.showStatus('🔒 Microphone blocked! Please allow microphone access in your browser bar, or click cards directly.', 'error');
                } else if (errCode === 'no-speech' || errCode === 'timeout') {
                    this.showStatus("🤔 I didn't hear anything. Tap the mic and speak, or click the card directly!", 'warning');
                } else {
                    this.showStatus(errMsg || '⚠️ Speech notice. You can also click the cards directly to play!', 'warning');
                }
            },
            // onEnd
            () => {
                this.isListening = false;
                if (micBtn) micBtn.classList.remove('listening');
                this.updateWaveform(false);
            }
        );
    }

    stopListening() {
        if (this.speech) this.speech.stopListening(false);
        this.isListening = false;
        const micBtn = document.getElementById('mic-btn');
        if (micBtn) micBtn.classList.remove('listening');
        this.updateWaveform(false);
    }

    submitManualInput() {
        const input = document.getElementById('manual-speech-input');
        if (!input) return;
        const text = input.value.trim();
        if (!text) {
            this.showStatus('Please type a word first!', 'warning');
            return;
        }
        input.value = '';
        this.showStatus(`Analyzing "${text}"...`, 'processing');
        this.processResult(text, [text]);
    }

    // -------------------------------------------------------- //
    //  PROCESS RESULT
    // -------------------------------------------------------- //

    async processResult(transcript, alternatives) {
        const responseTime = Date.now() - (this.startTime || Date.now());
        this.showStatus('🧠 Analyzing your speech...', 'processing');

        try {
            const res = await fetch('/api/process_speech', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    asr_output: transcript,
                    alternatives: alternatives || [],
                    target_word: this.currentScenario.target_word,
                    pair: [this.currentScenario.word1, this.currentScenario.word2],
                    session_id: this.sessionId,
                    response_time_ms: responseTime,
                    category: this.currentScenario.category
                })
            });
            const result = await res.json();
            this.trialsCompleted = result.trials_completed || this.trialsCompleted + 1;
            this.score = result.total_score || this.score;
            this.streak = result.streak || 0;
            this.bestStreak = result.best_streak || this.bestStreak;

            if (result.difficulty_changed) {
                this.difficulty = result.difficulty;
                this.showDifficultyChange(result.difficulty_message);
            }

            if (result.is_correct) {
                this.handleCorrect(result);
            } else {
                this.handleIncorrect(result);
            }

            this.updateScoreboard();
        } catch (e) {
            console.error('Processing error:', e);
            this.showStatus('⚠️ Error processing speech. Try again.', 'error');
        }
    }

    // -------------------------------------------------------- //
    //  CORRECT / INCORRECT HANDLERS
    // -------------------------------------------------------- //

    handleCorrect(result) {
        // Highlight correct option
        const targetIdx = this.currentScenario.target_index;
        const optionId = targetIdx === 0 ? 'option-left' : 'option-right';
        const option = document.getElementById(optionId);
        if (option) option.classList.add('correct-option');

        // Character celebration
        const character = document.getElementById('game-character');
        if (character) {
            character.classList.add('celebrate');
        }

        // Score popup
        this.showScorePopup(`+${result.score_earned}`);

        // Confetti!
        this.showConfetti();

        // Status and feedback
        this.showStatus(result.encouragement || '🎉 Correct!', 'success');

        // Auto-load next pair after delay
        setTimeout(() => {
            if (character) character.classList.remove('celebrate');
            this.loadNextPair();
        }, 2000);
    }

    handleIncorrect(result) {
        // Highlight options
        const targetIdx = this.currentScenario.target_index;
        const correctId = targetIdx === 0 ? 'option-left' : 'option-right';
        const wrongId = targetIdx === 0 ? 'option-right' : 'option-left';
        const correctOpt = document.getElementById(correctId);
        const wrongOpt = document.getElementById(wrongId);
        if (correctOpt) correctOpt.classList.add('correct-option');
        if (wrongOpt) wrongOpt.classList.add('wrong-option');

        // Character shake
        const character = document.getElementById('game-character');
        if (character) character.classList.add('shake');

        // Show feedback
        const feedbackText = result.feedback || "Almost! Let's try the next one. 💪";
        this.showStatus(feedbackText, 'incorrect');
        this.showFeedbackTip(feedbackText);

        // Auto-load next pair after longer delay
        setTimeout(() => {
            if (character) character.classList.remove('shake');
            this.hideFeedbackTip();
            this.loadNextPair();
        }, 3200);
    }

    // -------------------------------------------------------- //
    //  UI UPDATES
    // -------------------------------------------------------- //

    updateScoreboard() {
        const scoreEl = document.getElementById('score-value');
        const streakEl = document.getElementById('streak-value');
        const bestStreakEl = document.getElementById('best-streak-value');

        if (scoreEl) scoreEl.textContent = this.score;
        if (streakEl) streakEl.textContent = this.streak;
        if (bestStreakEl) bestStreakEl.textContent = this.bestStreak;
    }

    updateDifficultyStars(level) {
        const container = document.getElementById('difficulty-stars');
        if (!container) return;
        container.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const star = document.createElement('span');
            star.textContent = i < level ? '⭐' : '☆';
            star.className = 'difficulty-star';
            container.appendChild(star);
        }
    }

    showStatus(message, type) {
        const el = document.getElementById('game-status');
        if (!el) return;
        el.textContent = message;
        el.className = 'game-status status-' + (type || 'info');
    }

    showScorePopup(text) {
        const popup = document.createElement('div');
        popup.className = 'score-popup';
        popup.textContent = text;
        const arena = document.getElementById('game-arena');
        if (arena) {
            arena.appendChild(popup);
            setTimeout(() => popup.remove(), 1500);
        }
    }

    showConfetti() {
        const container = document.getElementById('confetti-container');
        if (!container) return;
        container.innerHTML = '';
        const emojis = ['🎉', '✨', '⭐', '🌟', '💫', '🎊', '🏆', '💪'];
        for (let i = 0; i < 20; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            piece.style.left = Math.random() * 100 + '%';
            piece.style.animationDelay = Math.random() * 0.5 + 's';
            piece.style.fontSize = (Math.random() * 16 + 14) + 'px';
            container.appendChild(piece);
        }
        setTimeout(() => { container.innerHTML = ''; }, 2000);
    }

    showFeedbackTip(tip) {
        const el = document.getElementById('feedback-tip');
        if (!el) return;
        el.querySelector('.feedback-text').textContent = tip;
        el.classList.add('visible');
    }

    hideFeedbackTip() {
        const el = document.getElementById('feedback-tip');
        if (el) el.classList.remove('visible');
    }

    showDifficultyChange(message) {
        const el = document.getElementById('difficulty-message');
        if (!el) return;
        el.textContent = message;
        el.classList.add('visible');
        setTimeout(() => el.classList.remove('visible'), 3000);
    }

    updateWaveform(active) {
        const bars = document.querySelectorAll('.waveform-bar');
        bars.forEach(bar => {
            bar.classList.toggle('active', active);
        });
    }

    // -------------------------------------------------------- //
    //  END SESSION
    // -------------------------------------------------------- //

    async endSession() {
        this.showStatus('📊 Session complete! Calculating your results...', 'info');

        try {
            const res = await fetch('/api/session/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            const summary = await res.json();
            this.showSessionSummary(summary);
        } catch (e) {
            console.error('End session error:', e);
            this.showSessionSummary({
                total_trials: this.trialsCompleted,
                total_score: this.score,
                best_streak: this.bestStreak,
                accuracy_pct: '0%'
            });
        }
    }

    showSessionSummary(summary) {
        const overlay = document.getElementById('session-summary-overlay');
        if (!overlay) return;

        document.getElementById('summary-trials').textContent = summary.total_trials || 0;
        document.getElementById('summary-correct').textContent = summary.correct_trials || 0;
        document.getElementById('summary-accuracy').textContent = summary.accuracy_pct || '0%';
        document.getElementById('summary-score').textContent = summary.total_score || 0;
        document.getElementById('summary-streak').textContent = summary.best_streak || 0;
        document.getElementById('summary-time').textContent = summary.duration_str || '-';

        const recList = document.getElementById('summary-recommendations');
        if (recList && summary.recommendations) {
            recList.innerHTML = '';
            summary.recommendations.forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                recList.appendChild(li);
            });
        }

        overlay.classList.add('visible');
    }
}

// Global instance
let game = null;

// Initialize when page loads
function startGame(userId, options) {
    game = new VocalRehabGame();
    game.init(userId, options);
}
