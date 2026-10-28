"""
Generate a professional 10-slide PowerPoint (.pptx) presentation for VocalRehab.
Uses modern design: clean typography, elegant color cards, and structured layouts.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette
    BG_DARK = RGBColor(15, 23, 42)        # Deep slate/navy
    PRIMARY_TEAL = RGBColor(13, 148, 136) # Teal / Medical Cyan
    ACCENT_CYAN = RGBColor(6, 182, 212)   # Vibrant Cyan
    TEXT_LIGHT = RGBColor(248, 250, 252)  # White/Off-white
    TEXT_MUTED = RGBColor(148, 163, 184)  # Muted slate
    CARD_BG = RGBColor(30, 41, 59)        # Card background
    CARD_BORDER = RGBColor(51, 65, 85)    # Card border
    TEXT_DARK = RGBColor(30, 41, 59)
    LIGHT_BG = RGBColor(241, 245, 249)
    WHITE = RGBColor(255, 255, 255)
    GREEN = RGBColor(34, 197, 94)
    AMBER = RGBColor(245, 158, 11)
    PURPLE = RGBColor(168, 85, 247)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category_text="VOCALREHAB // SYSTEM ARCHITECTURE & NLP"):
        # Category / breadcrumb
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_CYAN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
        return shape

    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, BG_DARK)

    # Accent pill tag
    pill = add_card(s1, Inches(0.8), Inches(1.2), Inches(3.8), Inches(0.45), CARD_BG, ACCENT_CYAN)
    tf_p = pill.text_frame
    p_p = tf_p.paragraphs[0]
    p_p.text = "HEALTHCARE NLP & ASSISTIVE COMPUTING"
    p_p.font.size = Pt(11)
    p_p.font.bold = True
    p_p.font.color.rgb = ACCENT_CYAN
    p_p.alignment = PP_ALIGN.CENTER

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.5), Inches(1.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "VocalRehab"
    p1.font.size = Pt(48)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT

    p2 = tf_t.add_paragraph()
    p2.text = "Gamified Minimal-Pair Speech Therapy & Intent-Resilient NLP Translation for Dysarthria"
    p2.font.size = Pt(20)
    p2.font.color.rgb = PRIMARY_TEAL
    p2.space_before = Pt(8)

    # Info Card
    info_card = add_card(s1, Inches(0.8), Inches(4.2), Inches(11.7), Inches(2.3), CARD_BG, CARD_BORDER)
    tf_i = info_card.text_frame
    tf_i.word_wrap = True
    
    p = tf_i.paragraphs[0]
    p.text = "PROJECT METADATA & ARCHITECTURE OVERVIEW"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    
    items = [
        ("Core Focus", "Contrastive Phonological Therapy + Syllable-Drop Resilient Voice Translation"),
        ("Key Tech Stack", "Python 3.14 | Flask | Web Speech API | Multi-Phonetic Embeddings (Soundex, Metaphone, NYSIIS)"),
        ("Benchmark Result", "88% Intent Classification Accuracy across 5 Clinical Severity Tiers (0% - 100% Slurred Speech)"),
        ("Project Repository", "https://github.com/ts3363/VocalRehab")
    ]
    for label, val in items:
        pi = tf_i.add_paragraph()
        pi.text = f"- {label}: {val}"
        pi.font.size = Pt(14)
        pi.font.color.rgb = TEXT_LIGHT
        pi.space_before = Pt(5)

    # =========================================================================
    # SLIDE 2: Problem Statement & Clinical Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, BG_DARK)
    add_header(s2, "Problem Statement: The Speech Recognition & Therapy Gap")

    # 3 Columns
    col_w = Inches(3.65)
    gap = Inches(0.38)
    start_x = Inches(0.8)
    top_y = Inches(1.6)
    col_h = Inches(5.2)

    c1 = add_card(s2, start_x, top_y, col_w, col_h)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "1. Clinical Dysarthria"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    pts1 = [
        "Neuromotor speech disorder resulting from stroke, TBI, Parkinson's, or Cerebral Palsy.",
        "Articulatory muscle weakness causes slurred speech, imprecise consonants, and hypernasality.",
        "Expiratory exhaustion leads to involuntary syllable and final-consonant drops."
    ]
    for pt in pts1:
        p = tf1.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    c2 = add_card(s2, start_x + col_w + gap, top_y, col_w, col_h)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "2. ASR System Failure"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = AMBER
    pts2 = [
        "Commercial ASR (Siri, Alexa, Google) models assume healthy, fluent phonation.",
        "Word Error Rates (WER) exceed 60% - 80% on dysarthric speech input.",
        "Inability to distinguish contrastive minimal pairs (e.g. ship vs. sheep) or recognize truncated phrases."
    ]
    for pt in pts2:
        p = tf2.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    c3 = add_card(s2, start_x + (col_w + gap)*2, top_y, col_w, col_h)
    tf3 = c3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "3. Therapy Discontinuity"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GREEN
    pts3 = [
        "Traditional speech therapy is expensive ($100+/hr) and requires travel to physical clinics.",
        "Repetitive paper drill cards cause high patient boredom and therapy abandonment.",
        "Lack of objective, longitudinal tracking between weekly speech-pathologist visits."
    ]
    for pt in pts3:
        p = tf3.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    # =========================================================================
    # SLIDE 3: Proposed Solution - VocalRehab Overview
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, BG_DARK)
    add_header(s3, "Proposed Solution: Dual-Action Therapeutic & Assistive Platform")

    card_left = add_card(s3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    tf_l = card_left.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "🎮 PILLAR 1: Gamified Therapy Engine"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    pts_l = [
        "Minimal-Pair Contrast Tasks: Targets precision between easily confused phonemes (e.g. bat vs. pat).",
        "Adaptive Difficulty Staging: Dynamically scales from High-Contrast pairs (Level 1) to Consonant Clusters (Level 3).",
        "Instant Anatomical Biofeedback: Automatically diagnoses articulatory error types (initial drop, spirantization) and suggests lip/tongue placements.",
        "Engagement Mechanics: Real-time streak multipliers, visual score progression, and celebratory particle animations."
    ]
    for pt in pts_l:
        p = tf_l.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    card_right = add_card(s3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tf_r = card_right.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "🗣️ PILLAR 2: Intent-Resilient Translator"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEAL
    pts_r = [
        "Dual Audio Ingestion: Real-time microphone listening via Web Audio API + Recorded audio file uploads (.wav, .mp3).",
        "Syllable-Drop Reconstruction: Recovers full intended sentence even when 30%-60% of syllables are dropped.",
        "Tri-Tier Reliability Guardrails: Color-coded reliability banner (High, Medium, Low) prevents medical miscommunication.",
        "Voice Output (TTS): Reconstructed clean text is vocalized aloud on behalf of the speech-impaired individual."
    ]
    for pt in pts_r:
        p = tf_r.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    # =========================================================================
    # SLIDE 4: End-to-End System Architecture
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, BG_DARK)
    add_header(s4, "System Architecture: End-to-End Processing Pipeline")

    steps = [
        ("1. Input Layer", "Live Mic (Web Speech API) or Audio Upload (.wav, .mp3)", ACCENT_CYAN),
        ("2. Acoustic Gating", "Dynamic Energy Gating (150/100/50), Noise Calibration & Normalization", PRIMARY_TEAL),
        ("3. ASR Extraction", "Multi-hypothesis transcription generating 1-Best + N-Best candidates", PURPLE),
        ("4. NLP Intent Engine", "Filler removal, multi-phonetic encoding & confusion matrix scoring", GREEN),
        ("5. Dual Application", "Dispatches to Minimal-Pair Game Engine OR Voice Translator", AMBER),
        ("6. Persistence", "Session logs, trial accuracy & error matrices saved in SQLite", TEXT_LIGHT),
    ]

    card_y = Inches(1.6)
    card_h = Inches(0.78)
    card_gap = Inches(0.12)
    for i, (title, desc, color) in enumerate(steps):
        c = add_card(s4, Inches(0.8), card_y + (card_h + card_gap)*i, Inches(11.7), card_h)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{title.upper()}  —  {desc}"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = color

    # =========================================================================
    # SLIDE 5: Deep Dive: The NLP Intent Engine Pipeline
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, BG_DARK)
    add_header(s5, "Model Architecture: 5-Stage Robust NLU Pipeline")

    nlp_stages = [
        ("Stage 1: Clinical Text Preprocessing", "Regex-based scrubbing of involuntary fillers ('um', 'uh', 'ah', 'er', 'eh') and punctuation normalization to isolate phonetic tokens."),
        ("Stage 2: Multi-Phonetic Signatures", "Computes tri-algorithmic phonetic codes simultaneously: Soundex (articulatory place), Double Metaphone (softening/fricatives), and NYSIIS (vowel position)."),
        ("Stage 3: Dysarthric Confusion Matrix", "Asymmetric cost overrides for clinically documented motor speech errors (e.g. voicing assimilation & final consonant drops get 70% penalty reduction)."),
        ("Stage 4: N-Best Hypothesis Fusion", "Recombines tokens across top-5 ASR alternatives using 103 clinical word repair rules (e.g. 'cah' -> 'call', 'wah der' -> 'water')."),
        ("Stage 5: Phrase-Bank Overlap Re-ranking", "Bidirectional coverage matching against 68 essential Activities of Daily Living (ADL) phrases with confidence margin thresholding.")
    ]

    for i, (stitle, sdesc) in enumerate(nlp_stages):
        box = add_card(s5, Inches(0.8), Inches(1.55) + Inches(1.05)*i, Inches(11.7), Inches(0.95))
        tf = box.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = stitle
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_CYAN
        p2 = tf.add_paragraph()
        p2.text = sdesc
        p2.font.size = Pt(12.5)
        p2.font.color.rgb = TEXT_LIGHT
        p2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 6: Dysarthric Phoneme Confusion Matrix & Scoring Math
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, BG_DARK)
    add_header(s6, "Mathematical Formulation & Asymmetric Cost Matrix")

    # Left: Mathematical equations
    c_math = add_card(s6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    tf_m = c_math.text_frame
    tf_m.word_wrap = True
    p = tf_m.paragraphs[0]
    p.text = "Mathematical Intent Scoring"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    math_pts = [
        "Combined Similarity Function:\nSim(c, t) = 0.25*SeqRatio + 0.20*PhoneticMatch + 0.30*ConfusionSim + 0.25*JaroWinkler",
        "Confusion-Aware Distance:\nCost(w1, w2) = 0.3 for dysarthric pair substitutions (default = 1.0).\nCost_del = 0.5 for final consonant drops (default = 0.8).",
        "Confidence & Margin Separation:\nConfidence = min(1.0, Score(t1)*0.6 + (Score(t1) - Score(t2))*2.0)",
        "Phrase Overlap Metric:\nScore = 0.7 * Coverage(Phrase) + 0.3 * MatchRatio(Candidate)"
    ]
    for pt in math_pts:
        p = tf_m.add_paragraph()
        p.text = pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(10)

    # Right: Clinical Confusion Table
    c_tbl = add_card(s6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tf_t = c_tbl.text_frame
    tf_t.word_wrap = True
    p = tf_t.paragraphs[0]
    p.text = "Clinical Dysarthric Substitutions"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEAL

    tbl_pts = [
        "Voicing Assimilation (/b/ <-> /p/, /d/ <-> /t/):\nVocal cord timing lag causes voiced stops to unvoice.",
        "Spirantization (/t/ -> /s/, /d/ -> /z/):\nIncomplete tongue closure produces fricatives instead of stops.",
        "Liquid Gliding (/r/ -> /w/, /l/ -> /y/):\nTongue blade motor weakness replaces liquids with glides.",
        "Final Consonant Deletion (cat -> ca):\nExpiratory airflow runs out at end of syllables.",
        "Vowel Laxing (/iy/ -> /ih/):\nReduced articulatory range collapses tense vowels (sheep -> ship)."
    ]
    for pt in tbl_pts:
        p = tf_t.add_paragraph()
        p.text = pt
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(10)

    # =========================================================================
    # SLIDE 7: Gamified Minimal-Pair Therapy Engine
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, BG_DARK)
    add_header(s7, "Therapy Engine: Minimal-Pair Curriculum & Biofeedback")

    # 4 Cards Layout
    card_data = [
        ("192 Minimal Pairs", "Categorized across 8 clinical contrast categories: Voicing, Final Deletion, Fronting, Stopping, Gliding, Clusters, Vowels, and Nasals.", ACCENT_CYAN),
        ("Adaptive Difficulty", "Automatically adapts difficulty levels 1 through 3 based on user accuracy over moving 5-trial windows.", GREEN),
        ("Anatomical Biofeedback", "Generates natural language placement tips (e.g. 'Press lips firmly together', 'Bite lower lip gently') to guide motor recovery.", AMBER),
        ("Longitudinal Tracking", "Tracks specific phoneme confusion trends across sessions, giving speech therapists detailed error diagnostics.", PURPLE)
    ]

    for i, (title, desc, color) in enumerate(card_data):
        row = i // 2
        col = i % 2
        x = Inches(0.8) + col * Inches(5.95)
        y = Inches(1.6) + row * Inches(2.6)
        c = add_card(s7, x, y, Inches(5.7), Inches(2.4))
        tf = c.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(20)
        p1.font.bold = True
        p1.font.color.rgb = color
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(14)
        p2.font.color.rgb = TEXT_LIGHT
        p2.space_before = Pt(10)

    # =========================================================================
    # SLIDE 8: Voice Translation Engine & Reliability Guardrails
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, BG_DARK)
    add_header(s8, "Voice Translation Pipeline & Clinical Reliability Guardrails")

    top_card = add_card(s8, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.3))
    tf_tc = top_card.text_frame
    tf_tc.word_wrap = True
    p = tf_tc.paragraphs[0]
    p.text = "Multi-Strategy Audio Ingestion Pipeline"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    pts_tc = [
        "Step 1: Multi-strategy recognition tries standard threshold (150), followed by aggressive dysarthric thresholds (100, 50).",
        "Step 2: Dynamic pause threshold extended to 2.5 seconds to accommodate slow speech rates and breath pauses.",
        "Step 3: Fallback audio normalization & volume boost (+10 dB) via pydub recovers low-intensity, breathy recordings."
    ]
    for pt in pts_tc:
        p = tf_tc.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(5)

    # 3 Reliability Tiers
    tiers = [
        ("🟢 High Confidence (>= 70%)", "Confident phrase match from clinical index. Safe for immediate autonomous communication.", GREEN),
        ("🔵 Medium Confidence (55% - 69%)", "Probable match. User visual confirmation advised before vocalization.", ACCENT_CYAN),
        ("🔴 Low Confidence (< 55%)", "Severe distortion. System switches to literal word-repair and displays a warning banner.", AMBER)
    ]
    for i, (title, desc, color) in enumerate(tiers):
        c = add_card(s8, Inches(0.8) + Inches(3.98)*i, Inches(4.1), Inches(3.75), Inches(2.7))
        tf = c.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = color
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_LIGHT
        p2.space_before = Pt(10)

    # =========================================================================
    # SLIDE 9: Experimental Results & Accuracy Benchmark
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, BG_DARK)
    add_header(s9, "Experimental Results: Benchmark Across 5 Severity Levels (N=50)")

    # Left: Accuracy Stats
    left_stat = add_card(s9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    tf_ls = left_stat.text_frame
    tf_ls.word_wrap = True
    p = tf_ls.paragraphs[0]
    p.text = "Benchmark Accuracy by Severity"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GREEN

    stats = [
        ("0% Slurred (Clear Baseline)", "10 / 10 (100% Accuracy)"),
        ("40% Slurred (Mild Dysarthria)", "10 / 10 (100% Accuracy)"),
        ("60% Slurred (Moderate Dysarthria)", "10 / 10 (100% Accuracy)"),
        ("80% Slurred (Severe Dysarthria)", "9 / 10 (90% Accuracy)"),
        ("100% Slurred (Extreme Dysarthria)", "5 / 10 (50% Accuracy + Warning Banner)"),
        ("OVERALL SYSTEM ACCURACY", "44 / 50 (88.0% Accuracy)")
    ]
    for sev, acc in stats:
        p = tf_ls.add_paragraph()
        p.text = f"- {sev}: {acc}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(8)

    # Right: Real Recovery Cases
    right_cases = add_card(s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tf_rc = right_cases.text_frame
    tf_rc.word_wrap = True
    p = tf_rc.paragraphs[0]
    p.text = "Real Recovery Cases (Extreme Slur)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN

    cases = [
        ("Raw ASR: 'I want to go hotel'", "NLP Translation: 'I want to go home today' [OK]"),
        ("Raw ASR: 'do you for having me'", "NLP Translation: 'Thank you for helping me' [OK]"),
        ("Raw ASR: 'right right for my version'", "NLP Translation: 'Is it time for my medicine' [OK]"),
        ("Raw ASR: 'C A H U Honours in May'", "NLP Translation: 'Can you understand me' [OK]"),
        ("Raw ASR: 'what's the time for my medicin'", "NLP Translation: 'Is it time for my medicine' [OK]")
    ]
    for inp, out in cases:
        p = tf_rc.add_paragraph()
        p.text = f"• {inp}\n  -> {out}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 10: Conclusion, Future Roadmap & Q&A
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, BG_DARK)
    add_header(s10, "Conclusion, Future Roadmap & Open Questions")

    card_concl = add_card(s10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    tf_c = card_concl.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = "Key Contributions"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = GREEN
    concl_pts = [
        "Built a clinically grounded NLP system achieving 88% intent recovery on dysarthric speech.",
        "Integrated dual-modality: Gamified minimal-pair biofeedback + Assistive Voice Translator.",
        "Designed an asymmetric dysarthric confusion matrix that outperforms off-the-shelf commercial ASR.",
        "Provides open-source, zero-cost tele-rehabilitation accessible from any modern web browser."
    ]
    for pt in concl_pts:
        p = tf_c.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    card_future = add_card(s10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    tf_f = card_future.text_frame
    tf_f.word_wrap = True
    p = tf_f.paragraphs[0]
    p.text = "Future Roadmap & Repository"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    fut_pts = [
        "Edge Whisper ASR: Fine-tune Whisper-Small on the TORGO and UASpeech clinical dysarthria datasets.",
        "Clinician Portal: Remote dashboard for speech-language pathologists (SLPs) to prescribe target pairs.",
        "Multilingual Expansion: Extend confusion matrix to regional Indian languages (Hindi, Tamil, Telugu).",
        "Project GitHub: https://github.com/ts3363/VocalRehab",
        "Thank you! Open for Questions & Evaluation."
    ]
    for pt in fut_pts:
        p = tf_f.add_paragraph()
        p.text = "- " + pt
        p.font.size = Pt(13.5)
        p.font.color.rgb = TEXT_LIGHT
        p.space_before = Pt(12)

    # Save presentation
    output_workspace = r"c:\Users\tejasri\OneDrive\Desktop\CL\VocalRehab\VocalRehab_Presentation.pptx"
    output_downloads = os.path.join(os.path.expanduser("~"), "Downloads", "VocalRehab_Presentation.pptx")
    prs.save(output_workspace)
    prs.save(output_downloads)
    print(f"Presentation saved successfully to:\n  1. {output_workspace}\n  2. {output_downloads}")

if __name__ == "__main__":
    create_deck()
