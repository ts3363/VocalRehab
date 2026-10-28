"""
VocalRehab Therapy Engine
=========================
Manages therapy sessions: selects minimal pairs based on patient needs,
adapts difficulty, generates game scenarios, and tracks progress.
"""

import json
import os
import random
import time
from datetime import datetime


class TherapyEngine:
    """Manages therapy content, session flow, and adaptive difficulty."""

    GAME_THEMES = {
        "direction": {
            "name": "Choose Your Path",
            "icon": "🧭",
            "option_labels": ["⬅️ Left Path", "➡️ Right Path"],
            "character": "🧙‍♂️",
            "success_msg": "The wizard found the right path!",
        },
        "color": {
            "name": "Color Quest",
            "icon": "🎨",
            "option_labels": ["🔴 Red Door", "🔵 Blue Door"],
            "character": "🎨",
            "success_msg": "You picked the perfect color!",
        },
        "animal": {
            "name": "Animal Safari",
            "icon": "🦁",
            "option_labels": ["🐻 Bear Trail", "🦊 Fox Trail"],
            "character": "🐱",
            "success_msg": "The cat found its way through the safari!",
        },
        "space": {
            "name": "Space Explorer",
            "icon": "🚀",
            "option_labels": ["🌙 Moon", "⭐ Star"],
            "character": "🚀",
            "success_msg": "The rocket reached its destination!",
        },
    }

    ENCOURAGING_MESSAGES = [
        "Amazing! You nailed it! 🎉",
        "Superstar pronunciation! ⭐",
        "You're on fire! Keep going! 🔥",
        "Wonderful! That was so clear! ✨",
        "Fantastic effort! 💪",
        "You're getting stronger every time! 🌟",
        "Brilliant! Your speech is shining! 🌞",
        "Way to go, champion! 🏆",
        "Perfect! You made that look easy! 👏",
        "Outstanding! Keep up the great work! 🎯",
        "Incredible progress! 🚀",
        "That was beautiful! Your practice is paying off! 💖",
        "You did it! So proud of you! 🥳",
        "Excellent! Another one down! 💯",
        "Marvelous! Your voice is strong! 🎤",
    ]

    TRY_AGAIN_MESSAGES = [
        "Good try! Let's give it another shot! 💪",
        "Almost there! You're so close! 🌈",
        "Don't give up — every attempt makes you stronger! 💫",
        "Great effort! Let's try one more time! 🎯",
        "You're doing awesome — let's hear it again! 🎤",
        "Practice makes progress! Try once more! 🌟",
        "So close! I believe in you! ❤️",
        "Nice attempt! Let's polish that one! ✨",
    ]

    def __init__(self, data_path: str = None):
        """Load minimal pairs database from JSON."""
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "minimal_pairs.json",
            )
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.categories = self.data.get("categories", {})
        self._recent_pairs = []  # Track recently shown pairs to avoid repeats
        self._max_recent = 10

    # ================================================================== #
    #  CATEGORY & PAIR MANAGEMENT
    # ================================================================== #

    def get_available_categories(self) -> list:
        """Return list of phoneme contrast categories with metadata."""
        result = []
        for cat_id, cat_data in self.categories.items():
            result.append({
                "id": cat_id,
                "name": cat_data.get("name", cat_id),
                "description": cat_data.get("description", ""),
                "phoneme_targets": cat_data.get("phoneme_targets", []),
                "total_pairs": sum(
                    len(level.get("pairs", []))
                    for level in cat_data.get("difficulty_levels", {}).values()
                ),
            })
        return result

    def select_minimal_pair(self, category: str = None, difficulty: int = None,
                            weak_phonemes: list = None) -> dict:
        """
        Select a minimal pair for therapy.

        Priority:
        1. If weak_phonemes provided, pick from those categories
        2. If category specified, pick from that category
        3. Otherwise, pick randomly

        Avoids recently shown pairs.
        """
        # Determine which category to use
        if category and category in self.categories:
            cat_id = category
        elif weak_phonemes:
            # Map weak phonemes to categories
            cat_id = self._find_category_for_phonemes(weak_phonemes)
        else:
            cat_id = random.choice(list(self.categories.keys()))

        cat_data = self.categories[cat_id]
        difficulty_levels = cat_data.get("difficulty_levels", {})

        # Determine difficulty level
        if difficulty is None:
            difficulty = 1
        diff_key = str(min(difficulty, len(difficulty_levels)))
        if diff_key not in difficulty_levels:
            diff_key = list(difficulty_levels.keys())[0]

        pairs = difficulty_levels[diff_key].get("pairs", [])
        if not pairs:
            # Fallback to any difficulty level with pairs
            for dk, dv in difficulty_levels.items():
                if dv.get("pairs"):
                    pairs = dv["pairs"]
                    diff_key = dk
                    break

        # Filter out recently shown pairs
        available = [
            p for p in pairs
            if (p.get("word1", ""), p.get("word2", "")) not in self._recent_pairs
        ]
        if not available:
            self._recent_pairs.clear()
            available = pairs

        pair = random.choice(available)

        # Track as recent
        self._recent_pairs.append((pair["word1"], pair["word2"]))
        if len(self._recent_pairs) > self._max_recent:
            self._recent_pairs.pop(0)

        # Randomly assign which word is the target
        words = [pair["word1"], pair["word2"]]
        hints = [pair.get("hint1", ""), pair.get("hint2", "")]
        sentences = [pair.get("sentence1", ""), pair.get("sentence2", "")]
        target_idx = random.randint(0, 1)

        return {
            "category": cat_id,
            "category_name": cat_data.get("name", cat_id),
            "difficulty": int(diff_key),
            "word1": words[0],
            "word2": words[1],
            "hint1": hints[0],
            "hint2": hints[1],
            "sentence1": sentences[0],
            "sentence2": sentences[1],
            "target_word": words[target_idx],
            "target_index": target_idx,
            "target_hint": hints[target_idx],
        }

    def _find_category_for_phonemes(self, phonemes: list) -> str:
        """Find the best category that targets given weak phonemes."""
        phoneme_set = set(p.lower() for p in phonemes)
        best_cat = None
        best_overlap = 0

        for cat_id, cat_data in self.categories.items():
            targets = " ".join(cat_data.get("phoneme_targets", [])).lower()
            overlap = sum(1 for p in phoneme_set if p in targets)
            if overlap > best_overlap:
                best_overlap = overlap
                best_cat = cat_id

        return best_cat or random.choice(list(self.categories.keys()))

    # ================================================================== #
    #  GAME SCENARIOS
    # ================================================================== #

    def get_game_scenario(self, pair: dict, game_type: str = "direction") -> dict:
        """
        Create a game scenario for a minimal pair.

        Returns a complete scenario with instructions, visual elements,
        and game metadata.
        """
        theme = self.GAME_THEMES.get(game_type, self.GAME_THEMES["direction"])
        target = pair["target_word"]
        target_idx = pair["target_index"]

        scenario = {
            "theme": game_type,
            "theme_name": theme["name"],
            "theme_icon": theme["icon"],
            "character": theme["character"],
            "instruction": f"Say '{target.upper()}' to guide {theme['character']} the right way!",
            "word1": pair["word1"],
            "word2": pair["word2"],
            "hint1": pair["hint1"],
            "hint2": pair["hint2"],
            "target_word": target,
            "target_index": target_idx,
            "option_left": {
                "word": pair["word1"],
                "hint": pair["hint1"],
                "label": theme["option_labels"][0],
                "is_target": target_idx == 0,
            },
            "option_right": {
                "word": pair["word2"],
                "hint": pair["hint2"],
                "label": theme["option_labels"][1],
                "is_target": target_idx == 1,
            },
            "success_message": theme["success_msg"],
            "category": pair.get("category", ""),
            "difficulty": pair.get("difficulty", 1),
        }
        return scenario

    # ================================================================== #
    #  SCORING
    # ================================================================== #

    def calculate_score(self, response_time_ms: int, is_correct: bool,
                        streak: int, difficulty: int) -> dict:
        """
        Calculate points with bonuses for speed, streaks, and difficulty.

        Base: 100 points for correct answer
        Speed bonus: up to +50 points (under 3 seconds)
        Streak bonus: +10 points per streak level (max +50)
        Difficulty bonus: +20 per difficulty level above 1
        """
        if not is_correct:
            return {
                "base_score": 0,
                "speed_bonus": 0,
                "streak_bonus": 0,
                "difficulty_bonus": 0,
                "total": 0,
                "message": random.choice(self.TRY_AGAIN_MESSAGES),
            }

        base = 100

        # Speed bonus: under 3000ms = full bonus, linear decay to 8000ms
        if response_time_ms <= 3000:
            speed_bonus = 50
        elif response_time_ms <= 8000:
            speed_bonus = int(50 * (1 - (response_time_ms - 3000) / 5000))
        else:
            speed_bonus = 0

        # Streak bonus
        streak_bonus = min(streak * 10, 50)

        # Difficulty bonus
        difficulty_bonus = max(0, (difficulty - 1)) * 20

        total = base + speed_bonus + streak_bonus + difficulty_bonus

        return {
            "base_score": base,
            "speed_bonus": speed_bonus,
            "streak_bonus": streak_bonus,
            "difficulty_bonus": difficulty_bonus,
            "total": total,
            "message": random.choice(self.ENCOURAGING_MESSAGES),
        }

    # ================================================================== #
    #  ADAPTIVE DIFFICULTY
    # ================================================================== #

    def adapt_difficulty(self, session_history: list,
                         current_difficulty: int = 1) -> dict:
        """
        Adaptive difficulty based on recent performance.

        Rules:
        - If accuracy >= 80% for last 5+ trials → increase difficulty
        - If accuracy < 50% for last 5+ trials → decrease difficulty
        - Otherwise → maintain current difficulty
        - Difficulty range: 1-3

        Returns new difficulty level and reasoning.
        """
        min_trials = 5
        if len(session_history) < min_trials:
            return {
                "difficulty": current_difficulty,
                "changed": False,
                "reason": f"Need at least {min_trials} trials to adapt. "
                          f"({len(session_history)}/{min_trials})",
            }

        recent = session_history[-min_trials:]
        correct_count = sum(1 for r in recent if r.get("is_correct", False))
        accuracy = correct_count / len(recent)

        new_difficulty = current_difficulty

        if accuracy >= 0.80 and current_difficulty < 3:
            new_difficulty = current_difficulty + 1
            reason = (
                f"Excellent! {correct_count}/{len(recent)} correct "
                f"({accuracy:.0%}). Moving to level {new_difficulty} for a challenge! 🚀"
            )
        elif accuracy < 0.50 and current_difficulty > 1:
            new_difficulty = current_difficulty - 1
            reason = (
                f"Let's take it a step back to level {new_difficulty} "
                f"to build more confidence. You're doing great! 💪"
            )
        else:
            reason = (
                f"Level {current_difficulty} feels right — "
                f"{correct_count}/{len(recent)} correct ({accuracy:.0%}). "
                f"Keep practicing! 🎯"
            )

        return {
            "difficulty": new_difficulty,
            "changed": new_difficulty != current_difficulty,
            "previous_difficulty": current_difficulty,
            "reason": reason,
            "recent_accuracy": round(accuracy, 4),
            "recent_correct": correct_count,
            "recent_total": len(recent),
        }

    # ================================================================== #
    #  SESSION SUMMARY
    # ================================================================== #

    def generate_session_summary(self, session_data: dict) -> dict:
        """
        Generate a complete session summary with statistics,
        phoneme-specific performance, and recommendations.
        """
        trials = session_data.get("trials", [])
        if not trials:
            return {"message": "No trials recorded in this session."}

        total = len(trials)
        correct = sum(1 for t in trials if t.get("is_correct", False))
        accuracy = correct / total if total > 0 else 0

        # Average response time
        times = [t.get("response_time_ms", 0) for t in trials if t.get("response_time_ms")]
        avg_time = sum(times) / len(times) if times else 0

        # Total score
        total_score = sum(t.get("score", 0) for t in trials)

        # Best streak
        best_streak = 0
        current_streak = 0
        for t in trials:
            if t.get("is_correct", False):
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0

        # Per-category breakdown
        category_stats = {}
        for t in trials:
            cat = t.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"correct": 0, "total": 0}
            category_stats[cat]["total"] += 1
            if t.get("is_correct", False):
                category_stats[cat]["correct"] += 1

        for cat, stats in category_stats.items():
            stats["accuracy"] = round(stats["correct"] / stats["total"], 4) if stats["total"] > 0 else 0

        # Identify weak areas
        weak_categories = [
            cat for cat, stats in category_stats.items()
            if stats["accuracy"] < 0.6 and stats["total"] >= 2
        ]

        # Generate recommendations
        recommendations = []
        if accuracy >= 0.8:
            recommendations.append("🌟 Outstanding session! Consider increasing the difficulty level.")
        elif accuracy >= 0.6:
            recommendations.append("💪 Good progress! Focus on the categories marked as weak areas.")
        else:
            recommendations.append("🎯 Keep practicing! Consistent daily sessions will show improvement.")

        if weak_categories:
            weak_names = []
            for wc in weak_categories:
                cat_data = self.categories.get(wc, {})
                weak_names.append(cat_data.get("name", wc))
            recommendations.append(
                f"📝 Suggested focus areas: {', '.join(weak_names)}"
            )

        if avg_time > 6000:
            recommendations.append(
                "⏱️ Take your time, but try to respond a bit faster as you grow comfortable."
            )

        return {
            "total_trials": total,
            "correct_trials": correct,
            "accuracy": round(accuracy, 4),
            "accuracy_pct": f"{accuracy:.0%}",
            "total_score": total_score,
            "best_streak": best_streak,
            "avg_response_time_ms": round(avg_time),
            "category_breakdown": category_stats,
            "weak_categories": weak_categories,
            "recommendations": recommendations,
            "duration_str": session_data.get("duration_str", ""),
        }

    # ================================================================== #
    #  PRACTICE SENTENCE GENERATION
    # ================================================================== #

    def get_practice_sentences(self, weak_phonemes: list, count: int = 5) -> list:
        """
        Get practice sentences emphasizing the patient's weak phonemes.
        Pulls from the minimal pairs database sentence fields.
        """
        sentences = []
        for cat_id, cat_data in self.categories.items():
            targets = " ".join(cat_data.get("phoneme_targets", [])).lower()
            matches = any(p.lower() in targets for p in weak_phonemes)
            if not matches:
                continue
            for level in cat_data.get("difficulty_levels", {}).values():
                for pair in level.get("pairs", []):
                    if pair.get("sentence1"):
                        sentences.append({
                            "sentence": pair["sentence1"],
                            "target_word": pair["word1"],
                            "category": cat_data.get("name", cat_id),
                        })
                    if pair.get("sentence2"):
                        sentences.append({
                            "sentence": pair["sentence2"],
                            "target_word": pair["word2"],
                            "category": cat_data.get("name", cat_id),
                        })

        if not sentences:
            # Fallback: get sentences from any category
            for cat_data in self.categories.values():
                for level in cat_data.get("difficulty_levels", {}).values():
                    for pair in level.get("pairs", []):
                        if pair.get("sentence1"):
                            sentences.append({
                                "sentence": pair["sentence1"],
                                "target_word": pair["word1"],
                                "category": cat_data.get("name", ""),
                            })

        random.shuffle(sentences)
        return sentences[:count]
