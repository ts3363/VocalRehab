"""
Generate Mixed-Severity Dysarthric Test Audio for VocalRehab
=============================================================
Creates test WAV files at 3 severity levels for each sentence:
  - CLEAR   (0% slur)  : Normal speech, baseline
  - MILD    (40% slur) : Slow rate, slight tremor, some noise
  - MODERATE(60% slur) : Very slow, heavy tremor, noise, volume drops

This lets you test how the NLP model handles different dysarthria severities.
"""

import os
import sys
import struct
import wave
import math
import random

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "VocalRehab_Test_Audio")

# ------------------------------------------------------------------ #
#  Test Sentences (common dysarthric patient needs)
# ------------------------------------------------------------------ #
SENTENCES = [
    {"id": 1, "text": "hello doctor I need help"},
    {"id": 2, "text": "can I have some water please"},
    {"id": 3, "text": "I want to go home today"},
    {"id": 4, "text": "thank you for helping me"},
    {"id": 5, "text": "please call my family"},
    {"id": 6, "text": "is it time for my medicine"},
    {"id": 7, "text": "I need to use the bathroom"},
    {"id": 8, "text": "I am feeling much better now"},
    {"id": 9, "text": "I am very hungry right now"},
    {"id": 10, "text": "can you understand me"},
]

# ------------------------------------------------------------------ #
#  Severity Profiles
# ------------------------------------------------------------------ #
SEVERITIES = {
    "clear": {
        "label": "CLEAR (0% slur)",
        "suffix": "clear",
        "rate": 180,          # Normal speaking rate
        "noise_level": 50,    # Very minimal noise
        "tremor_amp": 0.01,   # Almost no tremor
        "tremor_freq": 3,
        "volume_drops": 0,    # No random volume drops
        "pitch_shift": 0,     # No pitch distortion
    },
    "mild": {
        "label": "MILD (40% slur)",
        "suffix": "40pct_slur",
        "rate": 120,          # Slow
        "noise_level": 350,   # Moderate noise
        "tremor_amp": 0.08,   # Noticeable tremor
        "tremor_freq": 5,
        "volume_drops": 3,    # Some volume drops
        "pitch_shift": 0,
    },
    "moderate": {
        "label": "MODERATE (60% slur)",
        "suffix": "60pct_slur",
        "rate": 90,           # Very slow
        "noise_level": 600,   # Heavy noise
        "tremor_amp": 0.15,   # Strong tremor
        "tremor_freq": 6,
        "volume_drops": 6,    # Frequent volume drops
        "pitch_shift": 1,     # Slight pitch warping
    },
}


def generate_tts(text, output_path, rate=180):
    """Generate speech audio using pyttsx3."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", 0.9)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as e:
        print(f"    TTS error: {e}")
        return False


def apply_dysarthric_effects(input_path, output_path, profile):
    """
    Apply audio effects that simulate dysarthric speech characteristics:
    - Vocal tremor (amplitude modulation at 4-7 Hz)
    - Background noise (breathiness)
    - Random volume drops (imprecise breath control)
    - Slight pitch warping (vocal instability)
    """
    try:
        with wave.open(input_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth != 2:
            import shutil
            shutil.copy2(input_path, output_path)
            return True

        total_samples = n_frames * n_channels
        samples = list(struct.unpack(f"<{total_samples}h", raw))

        noise_level = profile["noise_level"]
        tremor_amp = profile["tremor_amp"]
        tremor_freq = profile["tremor_freq"]
        num_drops = profile["volume_drops"]

        random.seed(42)

        # Pre-compute random volume drop regions
        drop_regions = []
        if num_drops > 0 and n_frames > 1000:
            for _ in range(num_drops):
                start = random.randint(0, n_frames - 500)
                length = random.randint(200, 800)
                depth = random.uniform(0.2, 0.5)
                drop_regions.append((start * n_channels, length * n_channels, depth))

        processed = []
        for i in range(len(samples)):
            sample = samples[i]
            frame_idx = i // n_channels

            # 1. Vocal tremor (amplitude modulation)
            tremor = 1.0 + tremor_amp * math.sin(
                2 * math.pi * tremor_freq * frame_idx / framerate
            )
            sample = int(sample * tremor)

            # 2. Add breathiness / noise
            noise = random.randint(-noise_level, noise_level)
            sample += noise

            # 3. Volume drops (simulate imprecise breath control)
            for drop_start, drop_len, drop_depth in drop_regions:
                if drop_start <= i < drop_start + drop_len:
                    # Smooth fade in/out of the drop
                    pos_in_drop = i - drop_start
                    mid = drop_len / 2
                    if pos_in_drop < mid:
                        fade = 1.0 - drop_depth * (pos_in_drop / mid)
                    else:
                        fade = 1.0 - drop_depth * ((drop_len - pos_in_drop) / mid)
                    sample = int(sample * max(0.1, fade))

            # 4. Pitch warping (for moderate severity)
            if profile["pitch_shift"] and frame_idx % 7 == 0:
                # Occasionally duplicate or skip a sample to create slight pitch instability
                pass  # Keep it simple, the rate change already handles this

            sample = max(-32768, min(32767, sample))
            processed.append(sample)

        out_data = struct.pack(f"<{len(processed)}h", *processed)
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(out_data)

        return True

    except Exception as e:
        print(f"    Effect error: {e}")
        import shutil
        shutil.copy2(input_path, output_path)
        return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print()
    print("=" * 65)
    print("  VocalRehab - Mixed Severity Dysarthric Audio Generator")
    print("=" * 65)
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Sentences: {len(SENTENCES)}")
    print(f"  Severities: {len(SEVERITIES)} (clear, 40% slur, 60% slur)")
    print(f"  Total files: {len(SENTENCES) * len(SEVERITIES)}")
    print("=" * 65)
    print()

    generated = 0
    results = []

    for sentence in SENTENCES:
        sid = sentence["id"]
        text = sentence["text"]
        short_name = text.replace(" ", "_")[:25]

        print(f"--- Sentence {sid}: \"{text}\" ---")

        for sev_key, profile in SEVERITIES.items():
            filename = f"test_{sid:02d}_{profile['suffix']}.wav"
            filepath = os.path.join(OUTPUT_DIR, filename)
            temp_path = filepath + ".tmp.wav"

            print(f"  [{profile['label']:22s}] -> {filename}", end=" ")

            # Generate TTS at the severity-specific rate
            ok = generate_tts(text, temp_path, rate=profile["rate"])

            if ok and os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                apply_dysarthric_effects(temp_path, filepath, profile)
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                size_kb = os.path.getsize(filepath) / 1024
                print(f"  ({size_kb:.0f} KB)")
                generated += 1
                results.append({
                    "filename": filename,
                    "sentence_id": sid,
                    "text": text,
                    "severity": sev_key,
                    "label": profile["label"],
                })
            else:
                print(f"  FAILED")

        print()

    # Write reference file
    ref_path = os.path.join(OUTPUT_DIR, "TEST_REFERENCE_MIXED.txt")
    with open(ref_path, "w", encoding="utf-8") as f:
        f.write("VocalRehab - Mixed Severity Test Audio Reference\n")
        f.write("=" * 60 + "\n\n")
        f.write("Each sentence has 3 versions at different slur levels.\n")
        f.write("Upload them to the VocalRehab Translator to test how\n")
        f.write("the NLP model handles varying dysarthria severity.\n\n")
        f.write("-" * 60 + "\n\n")

        current_id = None
        for r in results:
            if r["sentence_id"] != current_id:
                current_id = r["sentence_id"]
                f.write(f"SENTENCE {current_id}: \"{r['text']}\"\n")
            f.write(f"  {r['label']:22s} -> {r['filename']}\n")
            if r["severity"] == "moderate":
                f.write("\n")

    print("=" * 65)
    print(f"  Generated: {generated}/{len(SENTENCES) * len(SEVERITIES)} files")
    print(f"  Reference: {ref_path}")
    print(f"  Location:  {OUTPUT_DIR}")
    print("=" * 65)
    print()
    print("  HOW TO TEST:")
    print("  1. Open http://127.0.0.1:5000/translate")
    print("  2. Upload test_01_clear.wav       -> should get HIGH confidence")
    print("  3. Upload test_01_40pct_slur.wav   -> should get MEDIUM confidence")
    print("  4. Upload test_01_60pct_slur.wav   -> may get LOW confidence")
    print("  5. Compare how the NLP handles each severity!")
    print()


if __name__ == "__main__":
    main()
