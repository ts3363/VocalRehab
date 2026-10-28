# 🎮 VocalRehab — Gamified Speech Therapy for Dysarthria

**An NLP-powered, gamified minimal-pair therapy system with speech-to-intent classification for individuals with dysarthria.**

VocalRehab helps young patients and stroke survivors practice speech through fun, engaging game-based exercises. The system uses Natural Language Processing (NLP) to understand dysarthric speech — even when up to 30% of syllables are dropped or distorted — and provides real-time feedback with adaptive difficulty.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎯 **NLP Intent Classification** | Understands dysarthric speech using phonetic encoding (Soundex, Metaphone, NYSIIS), edit distance, and a clinical confusion matrix |
| 🎮 **Gamified Therapy** | Wizard/Rocket/Animal-themed games with confetti, streaks, and score bonuses |
| 🧠 **Adaptive Difficulty** | Automatically adjusts difficulty based on patient performance (3 levels) |
| 📊 **Progress Dashboard** | Charts showing accuracy over time, category breakdown, achievements, and weak areas |
| 💬 **NLP Feedback** | Generates warm, actionable pronunciation tips (e.g., *"Try pressing your lips together more firmly for the /b/ sound"*) |
| 🔊 **Web Speech API** | Browser-based speech recognition with n-best hypothesis capture for better dysarthric coverage |
| 📱 **Responsive Design** | Works on desktop, tablet, and mobile |
| ♿ **Accessible** | High-contrast mode, reduced-motion support, large touch targets |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                     │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │ Web Speech    │→ │  Game.js   │→ │   Animations &   │ │
│  │ API (N-best)  │  │  Engine    │  │   Score UI       │ │
│  └──────────────┘  └──────┬─────┘  └──────────────────┘ │
│                           │ POST /api/process_speech      │
└───────────────────────────┼──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│                   FLASK SERVER (Backend)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  NLP Engine   │  │  Therapy     │  │  Database      │ │
│  │  - Phonetic   │  │  Engine      │  │  (SQLite)      │ │
│  │  - Confusion  │  │  - Pairs     │  │  - Users       │ │
│  │    Matrix     │  │  - Scoring   │  │  - Sessions    │ │
│  │  - Similarity │  │  - Adaptive  │  │  - Trials      │ │
│  │  - Feedback   │  │  - Summary   │  │  - Progress    │ │
│  └──────────────┘  └──────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
VocalRehab/
├── app.py                          # Flask application & API routes
├── config.py                       # Configuration constants
├── requirements.txt                # Python dependencies
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── nlp_engine.py               # NLP intent classifier & phoneme analysis
│   ├── therapy_engine.py           # Therapy session & adaptive difficulty
│   └── database.py                 # SQLite database manager
│
├── data/
│   └── minimal_pairs.json          # 190+ curated minimal pairs (8 categories × 3 levels)
│
├── static/
│   ├── css/
│   │   └── style.css               # Full responsive stylesheet
│   └── js/
│       ├── speech.js               # Web Speech API handler
│       └── game.js                 # Game engine & animations
│
└── templates/
    ├── base.html                   # Base Jinja2 template
    ├── index.html                  # Landing page with profile creation
    ├── game.html                   # Main game interface
    ├── progress.html               # Progress dashboard with charts
    └── settings.html               # User settings
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.9+**
- **Google Chrome** (required for Web Speech API)

### Steps

```bash
# 1. Navigate to the project
cd VocalRehab

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open **http://127.0.0.1:5000** in Google Chrome.

---

## 🎮 How to Play

1. **Create a profile** on the landing page (name, age, condition)
2. Click **"Start Playing"** to enter the game
3. A minimal pair appears (e.g., "ship" 🚢 vs "sheep" 🐑)
4. One word is **highlighted** as the target
5. Click the **🎤 microphone button** and say the target word
6. The NLP engine analyzes your speech and gives feedback
7. Earn **points, streaks, and achievements!**
8. Difficulty adapts automatically to your level

---

## 🧠 How the NLP Engine Works

The NLP engine is designed to handle the specific challenges of dysarthric speech:

### 1. Multi-Encoding Phonetic Matching
Each spoken word is encoded using **Soundex**, **Metaphone**, and **NYSIIS** algorithms. Even if the acoustic signal is degraded, the phonetic encoding often matches the intended word.

### 2. Dysarthric Confusion Matrix
A clinical confusion matrix captures common dysarthric substitution patterns:
- **Voiced ↔ Voiceless**: /b/↔/p/, /d/↔/t/, /g/↔/k/
- **Manner confusions**: stops ↔ fricatives
- **Final consonant deletion**: Common in moderate-severe dysarthria
- **Vowel tense/lax**: ship/sheep, bit/beat

These confusions get a **lower edit-distance cost**, so "pat" is recognized as likely meaning "bat" for a dysarthric speaker.

### 3. N-Best Hypothesis Re-ranking
The Web Speech API returns up to 5 alternative transcriptions. The NLP engine scores **all alternatives** against each target word and picks the best overall match — this dramatically improves accuracy.

### 4. Natural Language Feedback
Raw phoneme errors are translated into warm, actionable tips:
> *"Almost there! 💡 Try to press your lips together more firmly for the /b/ sound."*

---

## 📊 Therapy Categories

| # | Category | Phoneme Targets | Example Pairs |
|---|---|---|---|
| 1 | Voiced vs. Voiceless Stops | /b/-/p/, /d/-/t/, /g/-/k/ | bat/pat, dip/tip |
| 2 | Fricative Contrasts | /f/-/v/, /s/-/z/, /sh/-/ch/ | fan/van, ship/chip |
| 3 | Vowel Length | /iː/-/ɪ/, /uː/-/ʊ/ | sheep/ship, pool/pull |
| 4 | Initial Consonants | /m/-/n/, /w/-/r/, /s/-/th/ | map/nap, sing/thing |
| 5 | Final Consonants | final /d/-/t/, /b/-/p/, /g/-/k/ | bad/bat, cab/cap |
| 6 | Consonant Clusters | cluster vs. simplified | play/pay, stop/top |
| 7 | Liquids & Glides | /r/-/l/, /w/-/y/ | right/light, wet/yet |
| 8 | Nasal Contrasts | /m/-/n/, /n/-/ŋ/ | some/sun, win/wing |

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **NLP**: jellyfish (phonetic algorithms), difflib, custom confusion matrices
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Speech**: Web Speech API (browser-native)
- **Database**: SQLite3
- **Charts**: Chart.js
- **UI Framework**: Bootstrap 5

---

## 📝 License

MIT License — free for academic and personal use.

---

## 💖 Acknowledgements

- Minimal pair therapy methodology based on established Speech-Language Pathology (SLP) clinical practices
- Dysarthric confusion patterns informed by published clinical phonetics research
- Built with love for making speech therapy more accessible and fun 🌟
