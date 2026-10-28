"""
Generate HEAVILY Slurred Dysarthric Test Audio for VocalRehab
==============================================================
Adds 80% and 100% slur levels with:
  - Altered spoken text (dropped consonants, simplified words)
  - Very slow speech rate
  - Heavy tremor, noise, volume drops, pitch wobble
  - Low-pass filter simulation
"""

import os
import struct
import wave
import math
import random

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "VocalRehab_Test_Audio")

# Each sentence has the clear text + what a severely dysarthric person
# would actually say (phoneme simplification + consonant drops)
SENTENCES = [
    {
        "id": 1,
        "intended": "hello doctor I need help",
        "slur_80": "helo docor I nee hel",
        "slur_100": "heh oh dah I nee heh",
    },
    {
        "id": 2,
        "intended": "can I have some water please",
        "slur_80": "cah I hav some wader plees",
        "slur_100": "cah I hah suh wadah pees",
    },
    {
        "id": 3,
        "intended": "I want to go home today",
        "slur_80": "I wan to go hom today",
        "slur_100": "I wah to goh ho tuhday",
    },
    {
        "id": 4,
        "intended": "thank you for helping me",
        "slur_80": "thang you for helpin me",
        "slur_100": "thah yoo foh hepin mee",
    },
    {
        "id": 5,
        "intended": "please call my family",
        "slur_80": "plees call my famly",
        "slur_100": "pees cah my fahlee",
    },
    {
        "id": 6,
        "intended": "is it time for my medicine",
        "slur_80": "is it time for my medsin",
        "slur_100": "ih ih tie foh my mehsin",
    },
    {
        "id": 7,
        "intended": "I need to use the bathroom",
        "slur_80": "I nee to use the bathrum",
        "slur_100": "I nee to oos duh bahroo",
    },
    {
        "id": 8,
        "intended": "I am feeling much better now",
        "slur_80": "I am feelin much bedder now",
        "slur_100": "I ahm feein muh behder now",
    },
    {
        "id": 9,
        "intended": "I am very hungry right now",
        "slur_80": "I am verry hungree right now",
        "slur_100": "I ahm vehree hungree rye now",
    },
    {
        "id": 10,
        "intended": "can you understand me",
        "slur_80": "can you understan me",
        "slur_100": "cah yoo unersan mee",
    },
]

SEVERITIES = {
    "80pct_slur": {
        "label": "SEVERE (80% slur)",
        "text_key": "slur_80",
        "rate": 85,
        "noise_level": 900,
        "tremor_amp": 0.20,
        "tremor_freq": 6,
        "volume_drops": 8,
        "drop_depth_range": (0.3, 0.7),
        "lowpass": True,
        "pitch_wobble": 0.02,
    },
    "100pct_slur": {
        "label": "EXTREME (100% slur)",
        "text_key": "slur_100",
        "rate": 70,
        "noise_level": 1200,
        "tremor_amp": 0.28,
        "tremor_freq": 7,
        "volume_drops": 12,
        "drop_depth_range": (0.4, 0.8),
        "lowpass": True,
        "pitch_wobble": 0.04,
    },
}


def generate_tts(text, output_path, rate=100):
    """Generate speech audio using pyttsx3."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", 0.85)
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


def simple_lowpass(samples, framerate, cutoff=2500):
    """Simple low-pass filter to muffle speech (simulates oral weakness)."""
    rc = 1.0 / (2.0 * math.pi * cutoff)
    dt = 1.0 / framerate
    alpha = dt / (rc + dt)
    filtered = [samples[0]]
    for i in range(1, len(samples)):
        filtered.append(int(filtered[-1] + alpha * (samples[i] - filtered[-1])))
    return filtered


def apply_heavy_effects(input_path, output_path, profile):
    """
    Apply heavy dysarthric effects:
    - Low-pass filter (oral muscle weakness -> muffled sound)
    - Strong vocal tremor
    - Heavy noise (breathiness)
    - Frequent volume drops (breath control issues)
    - Pitch wobble (vocal cord instability)
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

        random.seed(42)

        # 1. Low-pass filter (muffled speech)
        if profile.get("lowpass"):
            samples = simple_lowpass(samples, framerate, cutoff=2200)

        # 2. Pre-compute volume drop regions
        drop_regions = []
        num_drops = profile["volume_drops"]
        depth_lo, depth_hi = profile["drop_depth_range"]
        if num_drops > 0 and len(samples) > 2000:
            for _ in range(num_drops):
                start = random.randint(0, len(samples) - 1000)
                length = random.randint(300, 1200)
                depth = random.uniform(depth_lo, depth_hi)
                drop_regions.append((start, length, depth))

        noise_level = profile["noise_level"]
        tremor_amp = profile["tremor_amp"]
        tremor_freq = profile["tremor_freq"]
        pitch_wobble = profile.get("pitch_wobble", 0)

        processed = []
        for i in range(len(samples)):
            sample = samples[i]
            frame_idx = i // n_channels

            # Vocal tremor
            t_val = 2 * math.pi * tremor_freq * frame_idx / framerate
            tremor = 1.0 + tremor_amp * math.sin(t_val)
            # Add secondary tremor for more irregularity
            tremor += 0.3 * tremor_amp * math.sin(2.7 * t_val + 1.3)
            sample = int(sample * tremor)

            # Pitch wobble (slight frequency modulation)
            if pitch_wobble > 0:
                wobble = 1.0 + pitch_wobble * math.sin(
                    2 * math.pi * 3.5 * frame_idx / framerate
                )
                sample = int(sample * wobble)

            # Noise (breathiness)
            noise = random.randint(-noise_level, noise_level)
            sample += noise

            # Volume drops
            for drop_start, drop_len, drop_depth in drop_regions:
                if drop_start <= i < drop_start + drop_len:
                    pos = i - drop_start
                    mid = drop_len / 2
                    if pos < mid:
                        fade = 1.0 - drop_depth * (pos / mid)
                    else:
                        fade = 1.0 - drop_depth * ((drop_len - pos) / mid)
                    sample = int(sample * max(0.05, fade))

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

    total_files = len(SENTENCES) * len(SEVERITIES)
    print()
    print("=" * 70)
    print("  VocalRehab - Heavy Slur Audio Generator (80% + 100%)")
    print("=" * 70)
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Files:  {total_files} new audio files")
    print("=" * 70)
    print()

    generated = 0
    results = []

    for sentence in SENTENCES:
        sid = sentence["id"]
        intended = sentence["intended"]
        print(f"--- Sentence {sid}: \"{intended}\" ---")

        for sev_key, profile in SEVERITIES.items():
            text_key = profile["text_key"]
            spoken_text = sentence[text_key]
            filename = f"test_{sid:02d}_{sev_key}.wav"
            filepath = os.path.join(OUTPUT_DIR, filename)
            temp_path = filepath + ".tmp.wav"

            print(f"  [{profile['label']:22s}]")
            print(f"    Speaking: \"{spoken_text}\"")
            print(f"    Rate: {profile['rate']} wpm, Noise: {profile['noise_level']}, Tremor: {profile['tremor_amp']}")

            ok = generate_tts(spoken_text, temp_path, rate=profile["rate"])

            if ok and os.path.exists(temp_path) and os.path.getsize(temp_path) > 100:
                apply_heavy_effects(temp_path, filepath, profile)
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                size_kb = os.path.getsize(filepath) / 1024
                print(f"    -> {filename} ({size_kb:.0f} KB)")
                generated += 1
                results.append({
                    "filename": filename,
                    "sid": sid,
                    "intended": intended,
                    "spoken": spoken_text,
                    "severity": sev_key,
                    "label": profile["label"],
                })
            else:
                print(f"    -> FAILED")
        print()

    # Write reference
    ref_path = os.path.join(OUTPUT_DIR, "TEST_REFERENCE_HEAVY_SLUR.txt")
    with open(ref_path, "w", encoding="utf-8") as f:
        f.write("VocalRehab - Heavy Slur Test Audio Reference\n")
        f.write("=" * 60 + "\n\n")
        f.write("These files simulate SEVERE and EXTREME dysarthric speech.\n")
        f.write("Spoken text has dropped consonants, simplified syllables,\n")
        f.write("and audio has heavy tremor, noise, and volume drops.\n\n")
        f.write("-" * 60 + "\n\n")

        cur_id = None
        for r in results:
            if r["sid"] != cur_id:
                cur_id = r["sid"]
                f.write(f"SENTENCE {cur_id}\n")
                f.write(f"  Intended:  \"{r['intended']}\"\n")
            f.write(f"  {r['label']:22s}\n")
            f.write(f"    Speaking: \"{r['spoken']}\"\n")
            f.write(f"    File:     {r['filename']}\n")
            if r["severity"] == "100pct_slur":
                f.write("\n")

    print("=" * 70)
    print(f"  Generated: {generated}/{total_files} files")
    print(f"  Reference: {ref_path}")
    print("=" * 70)
    print()
    print("  FULL TEST SET NOW AVAILABLE:")
    print("    test_XX_clear.wav        (0% slur)")
    print("    test_XX_40pct_slur.wav   (40% slur)")
    print("    test_XX_60pct_slur.wav   (60% slur)")
    print("    test_XX_80pct_slur.wav   (80% slur)  <- NEW")
    print("    test_XX_100pct_slur.wav  (100% slur) <- NEW")
    print()


if __name__ == "__main__":
    main()
