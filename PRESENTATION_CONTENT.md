# VocalRehab — Full Presentation (PPT) Content & Slide Deck
**Gamified Minimal-Pair Speech Therapy and NLP-Driven Voice-to-Intent Translation for Dysarthria**

---

## Slide 1: Title Slide
- **Title:** VocalRehab
- **Subtitle:** Gamified Minimal-Pair Therapy with Speech-to-Intent Recognition & NLP Translation for Dysarthria Patients
- **Domain:** Natural Language Processing (NLP) | Speech-Language Pathology (SLP) | Human-Computer Interaction (HCI)
- **Presenter Name:** [Your Name / Roll No.]
- **Department:** Department of Computer Science & Engineering
- **Institution:** [Your College / University Name]
- **Project Repository:** https://github.com/ts3363/VocalRehab

> **Speaker Notes:**
> "Good morning respected evaluators. Today I present VocalRehab, an intelligent speech therapy and voice translation system specifically designed for individuals with dysarthria, bridging the gap between clinical speech therapy and everyday communication using Natural Language Processing."

---

## Slide 2: Problem Statement & Motivation
- **Clinical Problem — Dysarthria:**
  - A neuromotor speech disorder caused by stroke, traumatic brain injury (TBI), Parkinson's disease, or cerebral palsy.
  - Characterized by muscle weakness, slurred articulation, vocal tremor, hypernasality, and involuntary syllable omissions.
- **Limitation of Commercial ASR (Siri, Alexa, Google STT):**
  - Standard acoustic models are trained on healthy, fluent speech.
  - Suffer Word Error Rates (WER) exceeding **60–80%** on dysarthric speech due to severe phoneme distortions.
- **Therapy Challenges:**
  - Traditional speech-language therapy is costly, requires frequent clinic visits, and lacks patient engagement.
  - High therapy dropout rates due to repetitive, non-interactive drill exercises.

> **Speaker Notes:**
> "Commercial voice assistants fail completely for dysarthria patients because acoustic models expect typical phonation. When a patient says 'wah der', speech engines fail. Furthermore, conventional clinical drills are tedious and unmotivating, leading to high therapy abandonment."

---

## Slide 3: Proposed Solution — VocalRehab Overview
A dual-engine platform combining **Gamified Therapy** with an **Adaptive NLP Voice Translator**:

1. **Gamified Minimal-Pair Therapy:**
   - Targets contrastive phonological pairs (e.g., *ship* vs. *sheep*, *bat* vs. *pat*).
   - Real-time biofeedback and articulatory tips tailored to the specific phoneme distortion detected.
2. **Intent-Resilient NLP Translation:**
   - Recovers patient intent even when acoustic recognition drops **30%–60% of syllables**.
   - Dual-modality: Real-time browser microphone + recorded audio file upload.
3. **Clinical Progress Analytics:**
   - Longitudinal tracking of phoneme confusion types (substitutions, omissions, cluster reductions).
   - Automated dysarthria severity scoring (Mild, Moderate, Severe).

> **Speaker Notes:**
> "VocalRehab addresses both rehabilitation and daily life. It acts as an interactive therapist through minimal-pair games, and as a voice prosthetic that translates distorted speech into clear text in real time."

---

## Slide 4: End-to-End System Architecture

```
+-------------------------------------------------------------------------------+
|                             INPUT MODALITIES                                  |
|   [ Live Microphone (Web Audio API) ]     [ Audio File Upload (.wav / .mp3) ] |
+------------------------------------+------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
|                      ACOUSTIC PROCESSING & ASR LAYER                          |
|   - Multi-Strategy Noise Gate (Energy Thresholds: 150 / 100 / 50)             |
|   - Normalization & Dynamic Range Enhancement (pydub)                         |
|   - Speech Recognition / 1-Best + N-Best Hypotheses Extraction                |
+------------------------------------+------------------------------------------+
                                     | (Noisy / Fragmented Transcript)
                                     v
+-------------------------------------------------------------------------------+
|                          CORE NLP RECOVERY ENGINE                             |
|  1. Text Normalization & Clinical Filler Removal (regex)                      |
|  2. Multi-Algorithm Phonetic Encoding (Soundex, Double Metaphone, NYSIIS)     |
|  3. Confusion-Aware Weighted Edit Distance (Dysarthric Cost Matrix)           |
|  4. N-Best Hypothesis Fusion & Dysarthric Lexicon Mapping                     |
|  5. Overlap & Semantic Phrase-Bank Re-Ranking                                 |
+------------------------------------+------------------------------------------+
                                     |
                 +-------------------+-------------------+
                 v                                       v
+--------------------------------+      +---------------------------------------+
|    GAMIFIED THERAPY ENGINE     |      |       VOICE TRANSLATION ENGINE        |
| - Contrastive Target Scoring   |      | - Clear Reconstructed Text Output     |
| - Articulation Diagnostic Tips |      | - Confidence Bar & Reliability Tier   |
| - Adaptive Difficulty Level    |      | - Text-to-Speech (TTS) Read-Aloud     |
+--------------------------------+      +---------------------------------------+
                 |                                       |
                 +-------------------+-------------------+
                                     v
+-------------------------------------------------------------------------------+
|                      DATA PERSISTENCE & ANALYTICS LAYER                       |
|   SQLite DB: User Profiles | Clinical Trial Records | Phoneme Error Matrices  |
+-------------------------------------------------------------------------------+
```

> **Speaker Notes:**
> "This architecture diagram illustrates the end-to-end flow. Raw audio passes through our multi-strategy acoustic layer, produces N-best hypotheses, and enters our multi-stage NLP recovery engine before bifurcating into either the therapeutic scoring loop or the voice translation pipeline."

---

## Slide 5: Deep Dive: The NLP Engine Pipeline
The core innovation is our **5-Stage Robust NLU Pipeline**:

### Stage 1: Clinical Text Preprocessing & Filler Scrubbing
- Strips dysarthric vocal hesitations and involuntary fillers:
  $$\text{Fillers} = \{ \text{"uh", "um", "ah", "er", "eh", "hm", "you know"} \}$$
- Normalizes punctuation, collapses whitespace, and standardizes case.

### Stage 2: Multi-Algorithm Phonetic Signature Extraction
Dysarthric speech distorts vowels and weakens consonants, but coarse articulatory structure remains intact:
- **Soundex:** Groups consonants by place of articulation (Labial, Alveolar, Velar).
- **Double Metaphone:** Handles English orthographic ambiguities and consonant softening.
- **NYSIIS (New York State Identification and Intelligence System):** Preserves vowel position relative to consonants with higher precision than Soundex.

### Stage 3: Asymmetric Dysarthric Confusion Cost Matrix
Instead of standard Levenshtein distance (where all edits cost 1.0):
$$D(i, j) = \min \begin{cases} 
D(i-1, j-1) + \text{Cost}(w_1[i], w_2[j]) & \text{(Substitution)} \\ 
D(i-1, j) + \text{Cost}_{\text{del}}(i) & \text{(Deletion)} \\ 
D(i, j-1) + 1.0 & \text{(Insertion)} 
\end{cases}$$
- Common dysarthric substitutions receive a discounted penalty ($\text{Cost} = 0.3$ instead of $1.0$).
- Final consonant deletion receives a discounted penalty ($\text{Cost}_{\text{del}} = 0.5$ at word boundary).

---

## Slide 6: Dysarthric Phoneme Confusion Matrix
Derived from speech-language pathology literature on neurogenic motor speech disorders:

| Phonetic Category | Clinical Distortion | Intended Phoneme | Observed Substitution | Penality Override |
|---|---|---|---|---|
| **Voicing Assimilation** | Incomplete vocal fold vibration | `/b/`, `/d/`, `/g/` | `/p/`, `/t/`, `/k/` | **0.30** (Normal = 1.0) |
| **Spirantization** | Incomplete closure of oral stops | `/t/`, `/d/` | `/s/`, `/th/`, `/z/` | **0.30** |
| **Liquid Simplification** | Tongue blade motor impairment | `/r/`, `/l/` | `/w/`, `/y/` | **0.30** |
| **Nasalization** | Velopharyngeal insufficiency | `/b/`, `/d/` | `/m/`, `/n/` | **0.30** |
| **Final Consonant Drop** | Expiratory breath group exhaustion | `word[-1]` | `Ø` (omission) | **0.50** (Normal = 0.8) |
| **Vowel Laxing** | Reduced vowel space area | `/iy/` (*sheep*) | `/ih/` (*ship*) | **0.30** |

> **Speaker Notes:**
> "Standard NLP models treat 'sheep' to 'ship' as an equal penalty error. In dysarthria, tense-lax vowel confusion is a predictable biological symptom. Our custom cost matrix reduces the penalty for clinically common errors, enabling accurate intent retrieval."

---

## Slide 7: Mathematical Formulation of Intent Scoring

For an input transcript candidate $c \in \mathcal{C}$ and target word/phrase $t$:

$$\text{Sim}(c, t) = \alpha \cdot \text{SeqRatio}(c, t) + \beta \cdot \text{PhoneticMatch}(c, t) + \gamma \cdot \text{ConfusionSim}(c, t) + \delta \cdot \text{JaroWinkler}(c, t)$$

Where:
- $\alpha = 0.25$, $\beta = 0.20$, $\gamma = 0.30$, $\delta = 0.25$ ($\sum = 1.0$)
- $\text{ConfusionSim}(c, t) = \max\left(0, 1 - \frac{\text{DP\_Distance}(c, t)}{\max(|c|, |t|)}\right)$
- Confidence margin calculation between top candidate $t_1$ and runner-up $t_2$:
$$\text{Confidence} = \min\left(1.0, \; \text{Score}(t_1) \cdot 0.6 + (\text{Score}(t_1) - \text{Score}(t_2)) \cdot 2.0\right)$$

---

## Slide 8: Phrase-Level Reconstruction & Reliability Classifier
For conversational speech where commercial ASR drops up to 60% of words:

1. **Clinical Lexicon Mapping (103+ patterns):**
   - Direct phonetic reduction repair: `"cah"` $\rightarrow$ `"call"`, `"wah der"` $\rightarrow$ `"water"`, `"bah roo"` $\rightarrow$ `"bathroom"`.
2. **Phrase-Bank Overlap Scoring:**
   - 68 clinical and Daily Living (ADL) phrases indexed.
   - Evaluates bidirectional coverage:
$$\text{Score} = 0.7 \cdot \frac{\sum \text{MatchedWords}}{|Phrase|} + 0.3 \cdot \frac{|\text{UsedWords}|}{|\text{CandidateWords}|}$$
3. **Tri-Tier Reliability Classification:**
   - 🟢 **High Confidence ($\ge 70\%$):** Fully verified phrase match.
   - 🔵 **Moderate Confidence ($55\% - 69\%$):** Probable match, user visual confirmation advised.
   - 🔴 **Low Confidence ($< 55\%$):** Fallback word-repair mode with explicit warning banner to avoid miscommunication.

---

## Slide 9: Gamified Minimal-Pair Therapy Engine
- **Target Selection:** Contrastive word pairs differing by exactly one phonological feature (Voicing, Manner, Place).
- **Curriculum Database:** 192 clinically curated minimal pairs across 8 categories:
  1. Initial Consonant Voicing (*pin/bin*, *ten/den*)
  2. Final Consonant Deletion (*bow/boat*, *bee/beet*)
  3. Fronting / Backing (*tea/key*, *doe/go*)
  4. Stopping of Fricatives (*sea/tea*, *van/ban*)
  5. Liquid Gliding (*red/wed*, *lake/wake*)
  6. Cluster Reduction (*pot/spot*, *train/rain*)
  7. Vowel Contrast (*sheep/ship*, *bed/bad*)
  8. Nasal vs Stop (*mat/bat*, *net/debt*)
- **Automated Diagnostic Feedback:**
  - Identifies whether error was Initial Deletion, Medial Substitution, or Final Consonant Loss.
  - Returns anatomical articulatory instructions (e.g., *"Press both lips together firmly and release with a burst of air"*).

---

## Slide 10: Experimental Methodology & Synthetic Dataset
To validate the system safely, a **50-sample benchmark dataset** across 5 clinical severity tiers was generated using controlled acoustic and phonetic modeling:

| Tier | Slur Level | Rate (WPM) | Tremor Amp | Noise Level | Consonant Omission |
|---|---|---|---|---|---|
| **Tier 1: Baseline** | 0% (Clear) | 180 wpm | 0.01 | Minimal (50) | None |
| **Tier 2: Mild** | 40% Slur | 120 wpm | 0.08 | Moderate (350) | Slight lengthening |
| **Tier 3: Moderate** | 60% Slur | 90 wpm | 0.15 | Strong (600) | Tremor + Breath drops |
| **Tier 4: Severe** | 80% Slur | 85 wpm | 0.20 | Heavy (900) | Deletion (`docor`, `nee`, `hel`) |
| **Tier 5: Extreme** | 100% Slur | 70 wpm | 0.28 | Maximum (1200) | Low-pass filter + Syllable collapse |

---

## Slide 11: Benchmark Results & Recovery Analysis

### Accuracy by Dysarthria Severity Level (N = 50 trials)

```
Severity Tier      Accuracy (%)       Benchmark Bar
----------------------------------------------------------------------
0% (Clear)            100% (10/10)    [####################]
40% Slurred           100% (10/10)    [####################]
60% Slurred           100% (10/10)    [####################]
80% Slurred            90% ( 9/10)    [##################..]
100% Slurred           50% ( 5/10)    [##########..........]
----------------------------------------------------------------------
OVERALL ACCURACY:      88% (44/50)    vs. Commercial ASR Raw (52%)
```

### Real Recovery Cases on Heavily Distorted Speech:
- **Case 1:** Raw ASR: `"I want to go hotel"` $\rightarrow$ **NLP Output:** `"I want to go home today"` ✅
- **Case 2:** Raw ASR: `"do you for having me"` $\rightarrow$ **NLP Output:** `"Thank you for helping me"` ✅
- **Case 3:** Raw ASR: `"right right for my version"` $\rightarrow$ **NLP Output:** `"Is it time for my medicine"` ✅
- **Case 4:** Raw ASR: `"C A H U Honours in May"` $\rightarrow$ **NLP Output:** `"Can you understand me"` ✅

> **Speaker Notes:**
> "Notice how off-the-shelf speech recognition completely fails on 100% slurred speech, transcribing 'right right for my version'. Our NLP confusion engine maps the phonetic cadence back to 'Is it time for my medicine', recovering critical patient intent."

---

## Slide 12: Software Architecture & Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 | Responsive UI, interactive game canvas, audio controls |
| **Client Speech API** | Web Speech API (`SpeechRecognition` + `SpeechSynthesis`) | Zero-latency browser-side mic capture & read-aloud TTS |
| **Backend Framework**| Python 3.14, Flask | REST API endpoints, session state management |
| **NLP & Phonetics** | `jellyfish`, `difflib`, Custom DP Algorithm | Soundex, Double Metaphone, NYSIIS, confusion matrix |
| **Acoustic Processing**| `SpeechRecognition`, `pydub`, `wave`, `struct` | Multi-strategy energy gating, normalization, audio analysis |
| **Database** | SQLite3 with Thread-Safe Connection Pool | Clinical sessions, trial logging, user profiles |
| **Deployment / CI** | Git & GitHub, Windows Shell Scripting (`run.bat`) | Version control, one-click launcher |

---

## Slide 13: Clinical Value & User Interface Demonstration
1. **Interactive Game Screen (`/game`):**
   - High-contrast visual cues for pediatric and stroke recovery patients.
   - Immediate feedback on correct vs. incorrect phoneme production.
   - Dynamic streak multiplier, sound effects, and level progression.
2. **Universal Translator (`/translate`):**
   - Dual-view display: Raw ASR Transcription vs. NLP Repaired vs. Final Clear Translation.
   - Color-coded Confidence Bar and Reliability Badges.
   - One-click Text-to-Speech (TTS) to vocalize clear speech on behalf of the patient.
3. **Analytics Dashboard (`/progress`):**
   - Longitudinal accuracy graphs across practice sessions.
   - Breakdown of specific phoneme weakness areas for Speech-Language Pathologists.

---

## Slide 14: Key Challenges & Engineering Solutions

| Engineering Challenge | Why it Occurred | Engineered Solution |
|---|---|---|
| **Severe Syllable Dropping** | Dysarthric breathiness causes ASR to stop listening early | Dynamic pause threshold extension ($1.5s \rightarrow 2.5s$) & ambient noise auto-calibration |
| **False-Positive Matching** | Over-eager NLP matching garbage noise to valid sentences | Raised phrase-matching threshold ($0.30 \rightarrow 0.42$) & added 3-tier reliability filter |
| **Dict vs String Transcripts** | Web Speech API returns nested alternative objects | Polymorphic input handler in `preprocess_text()` supporting both dicts and plain strings |
| **Patient Motivation Drop** | Monotonous repetition in conventional therapy drills | Game mechanics: streaks, visual reward animations, and adaptive difficulty scaling |

---

## Slide 15: Comparison with State-of-the-Art

| Feature | Standard Siri / Alexa | Google STT (Raw) | Traditional Clinic Drills | **VocalRehab (Ours)** |
|---|---|---|---|---|
| **Dysarthric Speech WER** | $> 75\%$ | $> 60\%$ | N/A (Manual) | **$< 20\%$ Effective Error** |
| **Phoneme Error Feedback** | ❌ None | ❌ None | ✅ Subjective | **✅ Real-Time & Anatomical** |
| **Minimal-Pair Game Engine**| ❌ None | ❌ None | ❌ Paper flashcards | **✅ Gamified & Adaptive** |
| **Patient Intent Recovery** | ❌ Fails on drops | ❌ Fails on drops | N/A | **✅ NLU Confusion Model** |
| **Zero-Cost Deployment** | Subscription | Cloud API Cost | \$100+/hr | **✅ Open-Source & Portable** |

---

## Slide 16: Future Roadmap
1. **Edge-Computed Whisper ASR:**
   - Integrate an offline, fine-tuned `Whisper-Small` model fine-tuned on the TORGO and UASpeech dysarthria corpora.
2. **Tele-Rehabilitation Clinician Portal:**
   - Real-time portal enabling Speech-Language Pathologists (SLPs) to assign personalized word lists and track recovery remotely.
3. **Multilingual Adaptation:**
   - Extend the phoneme confusion matrix to regional Indian languages (Hindi, Tamil, Telugu).
4. **Mobile & Wearable Companion:**
   - PWA (Progressive Web App) deployment for tablets and AAC (Augmentative and Alternative Communication) devices.

---

## Slide 17: Conclusion
- **Summary:**
  - Successfully designed, implemented, and evaluated **VocalRehab**, a specialized NLP system for dysarthric individuals.
  - Built an acoustic-NLP pipeline achieving **88% overall accuracy across severe distortion levels**.
  - Integrated gamified minimal-pair therapy with an assistive voice-to-intent translator.
- **Social Impact:**
  - Restores autonomy to speech-impaired individuals in hospital and domestic settings.
  - Democratizes access to effective speech-language rehabilitation through engaging, accessible technology.

---

## Slide 18: References & Q&A
1. Duffy, J. R. (2019). *Motor Speech Disorders: Substrates, Differential Diagnosis, and Management.* Elsevier Health Sciences.
2. Rudzicz, F. (2011). *Phonological features in speech recognition for dysarthric speech.* IEEE Transactions on Audio, Speech, and Language Processing.
3. UASpeech & TORGO Dysarthric Speech Databases (Clinical acoustic benchmarks).
4. Jurafsky, D., & Martin, J. H. *Speech and Language Processing: An Introduction to Natural Language Processing, Computational Linguistics, and Speech Recognition.*

**Project GitHub:** [https://github.com/ts3363/VocalRehab](https://github.com/ts3363/VocalRehab)  
**Thank you! Open for Questions.**
