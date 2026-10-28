"""Batch test the heavy slur files (80% + 100%)."""
import os, sys
sys.path.insert(0, r"c:\Users\tejasri\OneDrive\Desktop\CL\VocalRehab")
import speech_recognition as sr
from models.nlp_engine import NLPEngine

nlp = NLPEngine()
AUDIO_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "VocalRehab_Test_Audio")

SENTENCES = {
    1: "hello doctor I need help",
    2: "can I have some water please",
    3: "I want to go home today",
    4: "thank you for helping me",
    5: "please call my family",
    6: "is it time for my medicine",
    7: "I need to use the bathroom",
    8: "I am feeling much better now",
    9: "I am very hungry right now",
    10: "can you understand me",
}

ALL_SEVS = ["clear", "40pct_slur", "60pct_slur", "80pct_slur", "100pct_slur"]

def recognize(filepath):
    rec = sr.Recognizer()
    rec.energy_threshold = 100
    rec.pause_threshold = 2.5
    try:
        with sr.AudioFile(filepath) as src:
            rec.adjust_for_ambient_noise(src, duration=0.3)
            audio = rec.record(src)
        raw = rec.recognize_google(audio, language="en-US", show_all=True)
        transcript, alts = "", []
        if isinstance(raw, dict) and "alternative" in raw:
            a = raw["alternative"]
            if a:
                transcript = a[0].get("transcript", "")
                alts = [x.get("transcript", "") for x in a[1:5]]
        elif isinstance(raw, str):
            transcript = raw
        elif isinstance(raw, list) and raw:
            f = raw[0]
            if isinstance(f, dict):
                a = f.get("alternative", [])
                if a:
                    transcript = a[0].get("transcript", "")
                    alts = [x.get("transcript", "") for x in a[1:5]]
        return transcript, alts
    except sr.UnknownValueError:
        return "[UNRECOGNIZED]", []
    except sr.RequestError as e:
        return f"[ERROR]", []

def main():
    print()
    print("=" * 105)
    print("  VocalRehab - ALL Severity Levels Test (0% to 100% slur)")
    print("=" * 105)
    print()
    print(f"{'#':>2} | {'Severity':>14} | {'ASR Heard':32s} | {'NLP Translation':35s} | {'Conf':>5} | {'Rel':>6}")
    print("-" * 105)

    total, correct = 0, 0
    by_sev = {s: {"total": 0, "correct": 0} for s in ALL_SEVS}

    for sid in sorted(SENTENCES.keys()):
        expected = SENTENCES[sid]
        for sev in ALL_SEVS:
            fn = f"test_{sid:02d}_{sev}.wav"
            fp = os.path.join(AUDIO_DIR, fn)
            if not os.path.exists(fp):
                continue
            transcript, alts = recognize(fp)
            total += 1
            by_sev[sev]["total"] += 1
            if transcript.startswith("["):
                print(f"{sid:2d} | {sev:>14} | {transcript:32s} | {'-':35s} | {'0%':>5} | {'FAIL':>6}")
                continue
            result = nlp.translate_dysarthric(transcript, alts)
            clean = result["clean_text"]
            conf = f"{int(result['confidence']*100)}%"
            rel = result["reliability"].upper()[:4]
            match = expected.lower() in clean.lower()
            if match:
                correct += 1
                by_sev[sev]["correct"] += 1
            mk = "OK" if match else "XX"
            print(f"{sid:2d} | {sev:>14} | {transcript[:32]:32s} | {clean[:35]:35s} | {conf:>5} | {rel:>6} {mk}")
        print()

    print("=" * 105)
    print(f"  OVERALL: {correct}/{total} ({100*correct/total:.0f}%)")
    print()
    print("  BY SEVERITY:")
    for sev in ALL_SEVS:
        d = by_sev[sev]
        if d["total"] > 0:
            pct = 100 * d["correct"] / d["total"]
            bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
            print(f"    {sev:>14}: {d['correct']:2d}/{d['total']:2d} ({pct:3.0f}%)  [{bar}]")
    print("=" * 105)

if __name__ == "__main__":
    main()
