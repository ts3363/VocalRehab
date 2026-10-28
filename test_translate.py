"""Quick test of the dysarthric translator."""
import sys
sys.path.insert(0, r"c:\Users\tejasri\OneDrive\Desktop\CL\VocalRehab")
from models.nlp_engine import NLPEngine

e = NLPEngine()

tests = [
    ("I was",                       "I want to go home today"),
    ("I wah to go hoh",             "I want to go home today"),
    ("thah you foh heh ing mee",    "Thank you for helping me"),
    ("cah I hah suh wah der pees",  "Can I have some water please"),
    ("I ahm fee ing pay ih my heh", "I am feeling pain in my head"),
    ("heh oh doh dor I nee hel",    "Hello doctor I need help"),
    ("pees cah my fah ih lee",      "Please call my family"),
    ("I nee to oo duh bah roo",     "I need to use the bathroom"),
    ("I ahm veh ee huh gree rye now", "I am very hungry right now"),
]

print(f"{'ASR INPUT':45s} | {'EXPECTED':40s} | {'GOT':40s} | OK?")
print("-" * 135)
correct = 0
for asr, expected in tests:
    result = e.translate_dysarthric(asr)
    got = result["clean_text"]
    ok = expected.lower() in got.lower()
    if ok:
        correct += 1
    print(f"{asr:45s} | {expected:40s} | {got:40s} | {'YES' if ok else 'NO'}")

print(f"\nAccuracy: {correct}/{len(tests)} ({100*correct/len(tests):.0f}%)")
