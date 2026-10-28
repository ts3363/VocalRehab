"""
VocalRehab — Main Flask Application
=====================================
Gamified Minimal-Pair Therapy with Speech-to-Intent
for Dysarthria Patients.

Routes:
  Page routes : /, /game, /progress, /settings
  API routes  : /api/user/*, /api/session/*, /api/pair/*, /api/process_speech, /api/progress/*
"""

import os
import time
import tempfile
from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for, flash
)

from config import Config
from models.nlp_engine import NLPEngine
from models.therapy_engine import TherapyEngine
from models.database import DatabaseManager

# Optional: server-side speech recognition for audio file uploads
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

# ------------------------------------------------------------------ #
#  App factory
# ------------------------------------------------------------------ #
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Initialize engines
nlp = NLPEngine()
therapy = TherapyEngine(data_path=Config.MINIMAL_PAIRS_PATH)
db = DatabaseManager(db_path=Config.DATABASE_PATH)

# In-memory session state (for lightweight demo; production would use Redis)
_active_sessions = {}   # session_id -> {streak, score, trials, difficulty, ...}


# ================================================================== #
#  PAGE ROUTES
# ================================================================== #

@app.route("/")
def index():
    """Landing page."""
    user_id = session.get("user_id")
    user = db.get_user(user_id) if user_id else None
    return render_template("index.html", user=user)


@app.route("/game")
def game():
    """Main game page."""
    user_id = session.get("user_id") or request.args.get("user_id", type=int)
    if not user_id:
        # Auto-create guest user so the user can jump straight into the game
        guest = db.get_user_by_username("guest_player")
        if guest:
            user_id = guest["id"]
        else:
            user_id = db.create_user("guest_player", "Adventurer", 20, "other")
        session["user_id"] = user_id

    session["user_id"] = user_id
    user = db.get_user(user_id)
    if user and "display_name" in user and "name" not in user:
        user["name"] = user["display_name"]
    categories = therapy.get_available_categories()
    return render_template("game.html", user=user, categories=categories)


@app.route("/create_profile", methods=["POST"])
def create_profile():
    """Handle profile creation form submission from index.html."""
    name = request.form.get("name", "").strip() or "Adventurer"
    age = request.form.get("age", type=int) or 20
    condition = request.form.get("condition_type", "other")
    username = name.lower().replace(" ", "_")

    # If username exists, append a short random number or timestamp
    existing = db.get_user_by_username(username)
    if existing:
        user_id = existing["id"]
        db.update_user(user_id, display_name=name, age=age, condition_type=condition)
    else:
        try:
            user_id = db.create_user(username, name, age, condition)
        except Exception:
            import random
            username = f"{username}_{random.randint(100, 999)}"
            user_id = db.create_user(username, name, age, condition)

    session["user_id"] = user_id
    flash(f"Welcome, {name}! Let's start playing! 🎮", "success")
    return redirect(url_for("game"))


@app.route("/settings/save", methods=["POST"])
def save_settings():
    """Handle settings form submission from settings.html."""
    user_id = session.get("user_id")
    if not user_id:
        guest = db.get_user_by_username("guest_player")
        user_id = guest["id"] if guest else db.create_user("guest_player", "Adventurer", 20, "other")
        session["user_id"] = user_id

    name = request.form.get("name") or request.form.get("display_name")
    age = request.form.get("age", type=int)
    condition = request.form.get("condition_type")

    updates = {}
    if name:
        updates["display_name"] = name.strip()
    if age:
        updates["age"] = age
    if condition:
        updates["condition_type"] = condition

    if updates:
        db.update_user(user_id, **updates)
        flash("Settings saved successfully! ⭐", "success")

    return redirect(url_for("settings"))


@app.route("/progress")
def progress():
    """Progress dashboard."""
    user_id = session.get("user_id") or request.args.get("user_id", type=int)
    if not user_id:
        flash("Please create a profile first!", "warning")
        return redirect(url_for("index"))
    user = db.get_user(user_id)
    stats = db.get_user_stats(user_id)
    daily = db.get_daily_progress(user_id, days=14)
    cat_perf = db.get_category_performance(user_id)
    weak = db.get_weak_phonemes(user_id)
    recent = db.get_recent_sessions(user_id, limit=10)
    return render_template(
        "progress.html",
        user=user, stats=stats, daily=daily,
        category_performance=cat_perf, weak_phonemes=weak,
        recent_sessions=recent,
    )


@app.route("/settings")
def settings():
    """Settings page."""
    user_id = session.get("user_id")
    user = db.get_user(user_id) if user_id else None
    return render_template("settings.html", user=user)


@app.route("/translate")
def translate():
    """Dysarthric voice translator page."""
    user_id = session.get("user_id")
    user = db.get_user(user_id) if user_id else None
    return render_template("translate.html", user=user)


# ================================================================== #
#  API — USER
# ================================================================== #

@app.route("/api/user/create", methods=["POST"])
def api_create_user():
    """Create a new user profile."""
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    username = name.lower().replace(" ", "_")
    age = data.get("age")
    condition = data.get("condition_type", "other")

    # Check if username exists
    existing = db.get_user_by_username(username)
    if existing:
        session["user_id"] = existing["id"]
        return jsonify({"user_id": existing["id"], "message": "Welcome back!"})

    try:
        user_id = db.create_user(username, name, age, condition)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    session["user_id"] = user_id
    return jsonify({"user_id": user_id, "message": "Profile created! Let's play! 🎮"})


@app.route("/api/user/<int:user_id>")
def api_get_user(user_id):
    """Get user info."""
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


# ================================================================== #
#  API — SESSION
# ================================================================== #

@app.route("/api/session/start", methods=["POST"])
def api_start_session():
    """Start a new therapy session."""
    data = request.get_json(force=True)
    user_id = data.get("user_id") or session.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    difficulty = data.get("difficulty", Config.DEFAULT_DIFFICULTY)
    session_id = db.start_session(user_id, difficulty)

    _active_sessions[session_id] = {
        "user_id": user_id,
        "streak": 0,
        "best_streak": 0,
        "score": 0,
        "trials": [],
        "difficulty": difficulty,
        "started_at": time.time(),
    }

    return jsonify({
        "session_id": session_id,
        "difficulty": difficulty,
        "message": "Session started! Let's practice! 🎯",
    })


@app.route("/api/session/end", methods=["POST"])
def api_end_session():
    """End a therapy session and get summary."""
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    # Finalize in database
    db_summary = db.end_session(session_id)

    # Get in-memory state
    state = _active_sessions.pop(session_id, {})
    trials = state.get("trials", [])

    # Generate therapy summary
    session_data = {
        "trials": trials,
        "duration_str": "",
    }
    if state.get("started_at"):
        elapsed = int(time.time() - state["started_at"])
        mins, secs = divmod(elapsed, 60)
        session_data["duration_str"] = f"{mins}m {secs}s"

    summary = therapy.generate_session_summary(session_data)
    summary["session_id"] = session_id
    summary["best_streak"] = state.get("best_streak", 0)

    return jsonify(summary)


# ================================================================== #
#  API — MINIMAL PAIRS
# ================================================================== #

@app.route("/api/pair/next")
def api_next_pair():
    """Get the next minimal pair for the game."""
    user_id = request.args.get("user_id", type=int) or session.get("user_id")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty", type=int)
    game_type = request.args.get("game_type", "direction")

    # Check for weak phonemes if no category specified
    weak_phonemes = None
    if not category and user_id:
        weak = db.get_weak_phonemes(user_id)
        if weak:
            weak_phonemes = [w["category"] for w in weak[:3]]

    pair = therapy.select_minimal_pair(
        category=category,
        difficulty=difficulty,
        weak_phonemes=weak_phonemes,
    )
    scenario = therapy.get_game_scenario(pair, game_type)

    return jsonify(scenario)


@app.route("/api/categories")
def api_categories():
    """Get available therapy categories."""
    return jsonify(therapy.get_available_categories())


# ================================================================== #
#  API — SPEECH PROCESSING  (the key endpoint)
# ================================================================== #

@app.route("/api/process_speech", methods=["POST"])
def api_process_speech():
    """
    Process speech input through the NLP engine.

    Expects JSON:
      {
        "asr_output": "...",
        "alternatives": ["...", "..."],
        "target_word": "ship",
        "pair": ["ship", "sheep"],
        "session_id": 1,
        "response_time_ms": 2500,
        "category": "fricatives"
      }

    Returns classification result with score and feedback.
    """
    data = request.get_json(force=True)

    asr_output = data.get("asr_output", "")
    if isinstance(asr_output, dict):
        asr_output = asr_output.get("transcript", "") or ""
    elif not isinstance(asr_output, str):
        asr_output = str(asr_output)

    raw_alternatives = data.get("alternatives", [])
    alternatives = []
    for alt in raw_alternatives:
        if isinstance(alt, dict):
            alternatives.append(alt.get("transcript", ""))
        elif isinstance(alt, str):
            alternatives.append(alt)

    target_word = data.get("target_word", "")
    pair = data.get("pair", [])
    session_id = data.get("session_id")
    response_time_ms = data.get("response_time_ms", 5000)
    category = data.get("category", "")

    if not asr_output or not target_word:
        return jsonify({"error": "asr_output and target_word required"}), 400

    # --- NLP Intent Classification ---
    result = nlp.classify_intent(
        asr_output=asr_output,
        target_words=pair if pair else [target_word],
        alternatives=alternatives,
    )

    predicted = result["predicted_word"]
    is_correct = predicted.lower() == target_word.lower()

    # --- Phoneme Error Analysis ---
    analysis = nlp.analyze_phoneme_errors(asr_output, target_word)

    # --- Feedback Generation ---
    feedback = nlp.generate_feedback(analysis, is_correct)

    # --- Scoring ---
    state = _active_sessions.get(session_id, {
        "streak": 0, "best_streak": 0, "score": 0,
        "trials": [], "difficulty": 1, "user_id": None,
    })

    if is_correct:
        state["streak"] += 1
        state["best_streak"] = max(state["best_streak"], state["streak"])
    else:
        state["streak"] = 0

    score_result = therapy.calculate_score(
        response_time_ms=response_time_ms,
        is_correct=is_correct,
        streak=state["streak"],
        difficulty=state.get("difficulty", 1),
    )

    state["score"] += score_result["total"]

    # Record trial in state
    trial_record = {
        "is_correct": is_correct,
        "target_word": target_word,
        "predicted_word": predicted,
        "category": category,
        "response_time_ms": response_time_ms,
        "score": score_result["total"],
        "confidence": result["confidence"],
    }
    state["trials"].append(trial_record)

    if session_id in _active_sessions:
        _active_sessions[session_id] = state

    # Record in database
    user_id = state.get("user_id") or session.get("user_id")
    if session_id and user_id:
        db.record_trial(
            session_id=session_id,
            user_id=user_id,
            category=category,
            target_word=target_word,
            spoken_word=predicted,
            asr_raw=asr_output,
            is_correct=is_correct,
            confidence=result["confidence"],
            response_time_ms=response_time_ms,
            score_earned=score_result["total"],
            phoneme_errors=analysis.get("error_types", {}),
            feedback=feedback,
            minimal_pair="/".join(pair),
        )

    # --- Adaptive difficulty check ---
    adapt = therapy.adapt_difficulty(
        state["trials"],
        state.get("difficulty", 1),
    )
    if adapt["changed"] and session_id in _active_sessions:
        _active_sessions[session_id]["difficulty"] = adapt["difficulty"]

    return jsonify({
        "is_correct": is_correct,
        "predicted_word": predicted,
        "confidence": result["confidence"],
        "score_earned": score_result["total"],
        "score_breakdown": score_result,
        "feedback": feedback,
        "encouragement": score_result["message"],
        "phoneme_analysis": {
            "accuracy": analysis.get("accuracy", 0),
            "error_count": analysis.get("error_count", 0),
            "error_types": analysis.get("error_types", {}),
        },
        "streak": state["streak"],
        "best_streak": state["best_streak"],
        "total_score": state["score"],
        "trials_completed": len(state["trials"]),
        "difficulty": state.get("difficulty", 1),
        "difficulty_changed": adapt["changed"],
        "difficulty_message": adapt["reason"] if adapt["changed"] else "",
    })


# ================================================================== #
#  API — PROGRESS
# ================================================================== #

@app.route("/api/progress/summary")
def api_progress_summary():
    """Get user progress summary."""
    user_id = request.args.get("user_id", type=int) or session.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    stats = db.get_user_stats(user_id)
    daily = db.get_daily_progress(user_id, days=14)
    cat_perf = db.get_category_performance(user_id)
    return jsonify({"stats": stats, "daily": daily, "category_performance": cat_perf})


@app.route("/api/progress/weak_phonemes")
def api_weak_phonemes():
    """Get user's weakest phoneme categories."""
    user_id = request.args.get("user_id", type=int) or session.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    return jsonify(db.get_weak_phonemes(user_id))


# ================================================================== #
#  API — VOICE TRANSLATION (Dysarthric → Clear Text)
# ================================================================== #

@app.route("/api/translate/live", methods=["POST"])
def api_translate_live():
    """
    Translate live dysarthric speech to clean text.

    Expects JSON:
      { "asr_output": "...", "alternatives": ["...", "..."] }

    Returns:
      { "raw_text": "...", "clean_text": "...", "confidence": 0.85,
        "corrections_made": 2, "clarity_label": "Good", "tips": "..." }
    """
    data = request.get_json(force=True)

    asr_output = data.get("asr_output", "")
    if isinstance(asr_output, dict):
        asr_output = asr_output.get("transcript", "") or ""
    elif not isinstance(asr_output, str):
        asr_output = str(asr_output)

    raw_alternatives = data.get("alternatives", [])
    alternatives = []
    for alt in raw_alternatives:
        if isinstance(alt, dict):
            alternatives.append(alt.get("transcript", ""))
        elif isinstance(alt, str):
            alternatives.append(alt)

    if not asr_output.strip():
        return jsonify({"error": "No speech detected"}), 400

    # Run through the dysarthric NLP translation pipeline
    result = nlp.translate_dysarthric(asr_output, alternatives)

    # Generate tips
    cleaned = nlp.preprocess_text(asr_output)
    analysis = nlp.analyze_phoneme_errors(cleaned, result["clean_text"].lower())
    tips = nlp.generate_feedback(analysis, result["corrections"] == 0)

    # Assess clarity
    confidence = result["confidence"]
    if confidence >= 0.85:
        clarity = "Clear"
    elif confidence >= 0.65:
        clarity = "Good"
    elif confidence >= 0.45:
        clarity = "Fair"
    else:
        clarity = "Needs Practice"

    return jsonify({
        "raw_text": asr_output,
        "clean_text": result["clean_text"],
        "confidence": result["confidence"],
        "corrections_made": result["corrections"],
        "clarity_label": clarity,
        "match_method": result["match_method"],
        "reliability": result["reliability"],
        "tips": tips,
        "word_count": len(result["clean_text"].split()),
    })


@app.route("/api/translate/upload", methods=["POST"])
def api_translate_upload():
    """
    Translate an uploaded audio file from dysarthric speech to clean text.

    Uses a multi-strategy approach:
    1. Try Google ASR with default settings
    2. If that fails, retry with adjusted energy/noise settings
    3. Pass whatever we get through the dysarthric NLP translator
    4. Phrase-bank matching finds the most likely intended sentence

    Expects: multipart/form-data with 'audio' file field.
    Supports: WAV, MP3, FLAC, OGG, WEBM
    """
    if not HAS_SR:
        return jsonify({
            "error": "Server-side speech recognition not available. "
                     "Please install: pip install SpeechRecognition"
        }), 500

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if not audio_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Check file size (25 MB max)
    audio_file.seek(0, 2)
    size = audio_file.tell()
    audio_file.seek(0)
    if size > 25 * 1024 * 1024:
        return jsonify({"error": "File too large. Maximum 25 MB."}), 400

    # Save to temp file
    ext = os.path.splitext(audio_file.filename)[1].lower() or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    wav_path = tmp.name
    try:
        audio_file.save(tmp.name)
        tmp.close()

        # Convert to WAV if needed using pydub
        if ext not in (".wav",):
            try:
                from pydub import AudioSegment
                sound = AudioSegment.from_file(tmp.name)
                wav_path = tmp.name + ".wav"
                sound.export(wav_path, format="wav")
            except Exception:
                wav_path = tmp.name

        # ---- Multi-strategy recognition for dysarthric speech ----
        transcript = ""
        alternatives = []

        recognizer = sr.Recognizer()

        # Strategy 1: Standard recognition with dysarthric-friendly settings
        strategies = [
            {"energy_threshold": 150, "pause_threshold": 2.0,
             "adjust_noise": True, "language": "en-US"},
            {"energy_threshold": 100, "pause_threshold": 2.5,
             "adjust_noise": True, "language": "en-US"},
            {"energy_threshold": 50, "pause_threshold": 3.0,
             "adjust_noise": False, "language": "en-US"},
        ]

        for strat in strategies:
            try:
                recognizer.energy_threshold = strat["energy_threshold"]
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = strat["pause_threshold"]

                with sr.AudioFile(wav_path) as source:
                    if strat["adjust_noise"]:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = recognizer.record(source)

                raw_text = recognizer.recognize_google(
                    audio_data, language=strat["language"], show_all=True
                )

                # Parse Google results
                if isinstance(raw_text, dict) and "alternative" in raw_text:
                    alts = raw_text["alternative"]
                    if alts:
                        transcript = alts[0].get("transcript", "")
                        alternatives = [a.get("transcript", "") for a in alts[1:5]]
                elif isinstance(raw_text, str):
                    transcript = raw_text
                elif isinstance(raw_text, list) and raw_text:
                    first = raw_text[0]
                    if isinstance(first, dict):
                        alts = first.get("alternative", [])
                        if alts:
                            transcript = alts[0].get("transcript", "")
                            alternatives = [
                                a.get("transcript", "") for a in alts[1:5]
                            ]
                    elif isinstance(first, str):
                        transcript = first
                        alternatives = [str(r) for r in raw_text[1:5]]

                if transcript:
                    break  # Got a result, stop trying strategies

            except sr.UnknownValueError:
                continue  # Try next strategy
            except sr.RequestError as e:
                return jsonify({
                    "error": f"Speech recognition service error: {e}"
                }), 503

        # If ALL strategies failed, still try to give a useful response
        if not transcript:
            # For dysarthric speech, even "no recognition" is useful info.
            # Try to enhance audio with pydub and retry one more time
            enhanced = False
            try:
                from pydub import AudioSegment
                from pydub.effects import normalize, compress_dynamic_range
                sound = AudioSegment.from_file(wav_path)
                # Enhance: normalize volume, slow down slightly
                sound = normalize(sound)
                # Increase volume
                sound = sound + 10  # +10 dB
                enhanced_path = wav_path + "_enhanced.wav"
                sound.export(enhanced_path, format="wav")

                recognizer.energy_threshold = 50
                with sr.AudioFile(enhanced_path) as source:
                    audio_data = recognizer.record(source)
                try:
                    raw_text = recognizer.recognize_google(
                        audio_data, language="en-US", show_all=True
                    )
                    if isinstance(raw_text, dict) and "alternative" in raw_text:
                        alts = raw_text["alternative"]
                        if alts:
                            transcript = alts[0].get("transcript", "")
                            alternatives = [
                                a.get("transcript", "") for a in alts[1:5]
                            ]
                    elif isinstance(raw_text, str):
                        transcript = raw_text
                    elif isinstance(raw_text, list) and raw_text:
                        first = raw_text[0]
                        if isinstance(first, dict):
                            alts = first.get("alternative", [])
                            if alts:
                                transcript = alts[0].get("transcript", "")
                                alternatives = [
                                    a.get("transcript", "") for a in alts[1:5]
                                ]
                    enhanced = True
                except sr.UnknownValueError:
                    pass
                finally:
                    try:
                        os.unlink(enhanced_path)
                    except OSError:
                        pass
            except Exception:
                pass

            if not transcript:
                return jsonify({
                    "error": "Could not understand the audio. The speech may be "
                             "too severely distorted for automated recognition. "
                             "Tips: Try recording in a quiet environment, speak "
                             "slowly, and hold the microphone closer."
                }), 422

        # ---- Run through the dysarthric NLP translation pipeline ----
        result = nlp.translate_dysarthric(transcript, alternatives)

        # Generate tips
        analysis = nlp.analyze_phoneme_errors(
            nlp.preprocess_text(transcript), result["clean_text"].lower()
        )
        tips = nlp.generate_feedback(analysis, result["corrections"] == 0)

        return jsonify({
            "raw_text": transcript,
            "clean_text": result["clean_text"],
            "confidence": result["confidence"],
            "corrections_made": result["corrections"],
            "match_method": result["match_method"],
            "repaired_text": result["repaired_text"],
            "reliability": result["reliability"],
            "tips": tips,
            "alternatives_found": len(alternatives),
        })

    finally:
        # Clean up temp files
        try:
            os.unlink(tmp.name)
            if wav_path != tmp.name and os.path.exists(wav_path):
                os.unlink(wav_path)
        except OSError:
            pass


# ================================================================== #
#  RUN
# ================================================================== #

if __name__ == "__main__":
    print("\n🎮 VocalRehab — Gamified Speech Therapy for Dysarthria")
    print("=" * 55)
    print("  Open http://127.0.0.1:5000 in your browser")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
