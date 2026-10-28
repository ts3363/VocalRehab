"""
VocalRehab Database Manager
============================
SQLite database for storing user profiles, sessions, trial results,
and progress metrics.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager


class DatabaseManager:
    """SQLite database manager for VocalRehab."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "vocalrehab.db",
            )
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    age INTEGER,
                    condition_type TEXT DEFAULT 'other',
                    severity_level TEXT DEFAULT 'unknown',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    started_at TEXT DEFAULT (datetime('now')),
                    ended_at TEXT,
                    total_score INTEGER DEFAULT 0,
                    total_trials INTEGER DEFAULT 0,
                    correct_trials INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    difficulty_level INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS trial_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    category TEXT,
                    minimal_pair TEXT,
                    target_word TEXT,
                    spoken_word TEXT,
                    asr_raw_output TEXT,
                    is_correct INTEGER DEFAULT 0,
                    confidence_score REAL DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    score_earned INTEGER DEFAULT 0,
                    phoneme_errors TEXT DEFAULT '{}',
                    feedback_given TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (session_id) REFERENCES sessions(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS progress_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    phoneme_category TEXT,
                    accuracy REAL DEFAULT 0,
                    avg_confidence REAL DEFAULT 0,
                    trials_count INTEGER DEFAULT 0,
                    improvement_rate REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_trials_session ON trial_results(session_id);
                CREATE INDEX IF NOT EXISTS idx_trials_user ON trial_results(user_id);
                CREATE INDEX IF NOT EXISTS idx_progress_user_date ON progress_metrics(user_id, date);
            """)

    # ================================================================== #
    #  USER CRUD
    # ================================================================== #

    def create_user(self, username: str, display_name: str, age: int = None,
                    condition_type: str = "other") -> int:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, display_name, age, condition_type) "
                "VALUES (?, ?, ?, ?)",
                (username, display_name, age, condition_type),
            )
            return cursor.lastrowid

    def get_user(self, user_id: int) -> dict:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                d = dict(row)
                d["name"] = d.get("display_name", "")
                return d
            return None

    def get_user_by_username(self, username: str) -> dict:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                d = dict(row)
                d["name"] = d.get("display_name", "")
                return d
            return None

    def update_user(self, user_id: int, **kwargs) -> bool:
        allowed = {"display_name", "age", "condition_type", "severity_level"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        with self._get_conn() as conn:
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            return True

    # ================================================================== #
    #  SESSION MANAGEMENT
    # ================================================================== #

    def start_session(self, user_id: int, difficulty: int = 1) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (user_id, difficulty_level) VALUES (?, ?)",
                (user_id, difficulty),
            )
            return cursor.lastrowid

    def end_session(self, session_id: int) -> dict:
        with self._get_conn() as conn:
            # Calculate session stats from trial_results
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total_trials,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_trials,
                    SUM(score_earned) as total_score,
                    AVG(response_time_ms) as avg_response_time
                FROM trial_results WHERE session_id = ?
            """, (session_id,)).fetchone()

            conn.execute("""
                UPDATE sessions
                SET ended_at = datetime('now'),
                    total_trials = ?,
                    correct_trials = ?,
                    total_score = ?,
                    avg_response_time = ?
                WHERE id = ?
            """, (
                stats["total_trials"] or 0,
                stats["correct_trials"] or 0,
                stats["total_score"] or 0,
                round(stats["avg_response_time"] or 0, 2),
                session_id,
            ))

            return {
                "session_id": session_id,
                "total_trials": stats["total_trials"] or 0,
                "correct_trials": stats["correct_trials"] or 0,
                "total_score": stats["total_score"] or 0,
                "avg_response_time": round(stats["avg_response_time"] or 0, 2),
            }

    def get_session(self, session_id: int) -> dict:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            return dict(row) if row else None

    # ================================================================== #
    #  TRIAL RESULTS
    # ================================================================== #

    def record_trial(self, session_id: int, user_id: int, category: str,
                     target_word: str, spoken_word: str, asr_raw: str,
                     is_correct: bool, confidence: float, response_time_ms: int,
                     score_earned: int, phoneme_errors: dict = None,
                     feedback: str = "", minimal_pair: str = "") -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO trial_results
                    (session_id, user_id, category, minimal_pair, target_word,
                     spoken_word, asr_raw_output, is_correct, confidence_score,
                     response_time_ms, score_earned, phoneme_errors, feedback_given)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, category, minimal_pair, target_word,
                spoken_word, asr_raw, 1 if is_correct else 0, confidence,
                response_time_ms, score_earned,
                json.dumps(phoneme_errors or {}), feedback,
            ))
            return cursor.lastrowid

    def get_session_trials(self, session_id: int) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM trial_results WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ================================================================== #
    #  PROGRESS & ANALYTICS
    # ================================================================== #

    def get_user_stats(self, user_id: int) -> dict:
        with self._get_conn() as conn:
            session_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(total_score) as lifetime_score,
                    SUM(total_trials) as lifetime_trials,
                    SUM(correct_trials) as lifetime_correct,
                    AVG(avg_response_time) as avg_response_time
                FROM sessions WHERE user_id = ? AND ended_at IS NOT NULL
            """, (user_id,)).fetchone()

            # Best streak across all trials
            trials = conn.execute(
                "SELECT is_correct FROM trial_results WHERE user_id = ? ORDER BY created_at",
                (user_id,),
            ).fetchall()
            best_streak = 0
            cur_streak = 0
            for t in trials:
                if t["is_correct"]:
                    cur_streak += 1
                    best_streak = max(best_streak, cur_streak)
                else:
                    cur_streak = 0

            total_trials = session_stats["lifetime_trials"] or 0
            correct = session_stats["lifetime_correct"] or 0

            return {
                "total_sessions": session_stats["total_sessions"] or 0,
                "lifetime_score": session_stats["lifetime_score"] or 0,
                "total_trials": total_trials,
                "correct_trials": correct,
                "overall_accuracy": round(correct / total_trials, 4) if total_trials > 0 else 0,
                "avg_response_time": round(session_stats["avg_response_time"] or 0, 2),
                "best_streak": best_streak,
            }

    def get_daily_progress(self, user_id: int, days: int = 7) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as trials,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(confidence_score) as avg_confidence,
                    SUM(score_earned) as total_score
                FROM trial_results
                WHERE user_id = ? AND created_at >= datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (user_id, f"-{days} days")).fetchall()

            result = []
            for r in rows:
                total = r["trials"]
                correct = r["correct"]
                result.append({
                    "date": r["date"],
                    "trials": total,
                    "correct": correct,
                    "accuracy": round(correct / total, 4) if total > 0 else 0,
                    "avg_confidence": round(r["avg_confidence"] or 0, 4),
                    "total_score": r["total_score"] or 0,
                })
            return result

    def get_category_performance(self, user_id: int) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    category,
                    COUNT(*) as trials,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(confidence_score) as avg_confidence
                FROM trial_results
                WHERE user_id = ?
                GROUP BY category
                ORDER BY category
            """, (user_id,)).fetchall()

            result = []
            for r in rows:
                total = r["trials"]
                correct = r["correct"]
                result.append({
                    "category": r["category"],
                    "trials": total,
                    "correct": correct,
                    "accuracy": round(correct / total, 4) if total > 0 else 0,
                    "avg_confidence": round(r["avg_confidence"] or 0, 4),
                })
            return result

    def get_weak_phonemes(self, user_id: int, threshold: float = 0.6) -> list:
        """Get phoneme categories with accuracy below threshold, sorted worst-first."""
        perf = self.get_category_performance(user_id)
        weak = [p for p in perf if p["accuracy"] < threshold and p["trials"] >= 3]
        weak.sort(key=lambda x: x["accuracy"])
        return weak

    def get_recent_sessions(self, user_id: int, limit: int = 10) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM sessions
                WHERE user_id = ? AND ended_at IS NOT NULL
                ORDER BY started_at DESC LIMIT ?
            """, (user_id, limit)).fetchall()
            return [dict(r) for r in rows]
