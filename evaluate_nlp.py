"""
VocalRehab NLP Robustness Evaluation Benchmark
==============================================
Simulates dysarthric speech distortions (phoneme dropping, voicing errors,
manner confusions, final consonant deletion) and benchmarks VocalRehab's
NLP Speech-to-Intent engine against baseline exact-match ASR.
"""

import os
import sys
import random

sys.path.insert(0, os.path.dirname(__file__))
from models.nlp_engine import NLPEngine

def simulate_dysarthric_noise(word: str, severity: float = 0.3) -> str:
    """
    Simulate typical dysarthric acoustic degradation:
    - Voicing substitution (b <-> p, d <-> t, g <-> k)
    - Final consonant dropping
    - Cluster simplification
    - Vowel distortion
    """
    if len(word) <= 1 or random.random() > severity:
        return word

    chars = list(word)
    mutation_type = random.choice(["substitute", "drop_final", "slur_vowel"])

    if mutation_type == "drop_final" and len(chars) > 2:
        chars = chars[:-1]
    elif mutation_type == "substitute":
        confusions = {
            'b': 'p', 'p': 'b', 'd': 't', 't': 'd', 'g': 'k', 'k': 'g',
            's': 'z', 'z': 's', 'f': 'v', 'v': 'f', 'm': 'n', 'n': 'm'
        }
        for i, c in enumerate(chars):
            if c in confusions and random.random() < 0.6:
                chars[i] = confusions[c]
                break
    elif mutation_type == "slur_vowel":
        vowels = {'ee': 'i', 'ea': 'i', 'oo': 'u', 'i': 'ee'}
        for src, target in vowels.items():
            joined = "".join(chars)
            if src in joined:
                joined = joined.replace(src, target, 1)
                return joined

    return "".join(chars)

def run_benchmark():
    print("=" * 65)
    print(" VocalRehab NLP Speech-to-Intent Benchmark: Dysarthric Robustness")
    print("=" * 65)

    nlp = NLPEngine()

    test_pairs = [
        ("ship", "sheep"), ("bat", "pat"), ("big", "pig"), ("fan", "van"),
        ("bad", "bat"), ("play", "pay"), ("right", "light"), ("some", "sun"),
        ("dip", "tip"), ("game", "came"), ("fine", "vine"), ("pool", "pull"),
        ("beat", "bit"), ("stop", "top"), ("rock", "lock"), ("bed", "bet"),
        ("goal", "coal"), ("sip", "zip"), ("feet", "fit"), ("weed", "read")
    ]

    noise_levels = [0.10, 0.20, 0.30, 0.40]

    for noise in noise_levels:
        total_trials = 0
        baseline_correct = 0
        vocalrehab_correct = 0

        for target, distractor in test_pairs:
            for _ in range(5):  # 5 variations per pair
                total_trials += 1
                # Simulate degraded ASR transcription
                degraded = simulate_dysarthric_noise(target, severity=noise)

                # 1. Baseline: Exact match or naive check
                if degraded == target:
                    baseline_correct += 1

                # 2. VocalRehab NLP Intent Classification
                intent_res = nlp.classify_intent(
                    asr_output=degraded,
                    target_words=[target, distractor],
                    alternatives=[degraded]
                )

                if intent_res["predicted_word"] == target:
                    vocalrehab_correct += 1

        base_acc = (baseline_correct / total_trials) * 100
        vr_acc = (vocalrehab_correct / total_trials) * 100
        gain = vr_acc - base_acc

        print(f"Noise / Degradation Level: {int(noise*100)}%")
        print(f"  • Standard Exact-Match ASR Accuracy : {base_acc:5.1f}%")
        print(f"  • VocalRehab NLP Intent Accuracy     : {vr_acc:5.1f}%")
        print(f"  • Robustness Improvement             : +{gain:4.1f}%")
        print("-" * 65)

if __name__ == "__main__":
    run_benchmark()
