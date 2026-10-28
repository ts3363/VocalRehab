"""VocalRehab Configuration."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = "vocalrehab-secret-key-change-in-production"
    DATABASE_PATH = os.path.join(BASE_DIR, "data", "vocalrehab.db")
    MINIMAL_PAIRS_PATH = os.path.join(BASE_DIR, "data", "minimal_pairs.json")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DEFAULT_DIFFICULTY = 1
    DEFAULT_SESSION_LENGTH = 15
    SPEECH_TIMEOUT_MS = 10000
    MAX_ALTERNATIVES = 5
    DIFFICULTY_UP_THRESHOLD = 0.80
    DIFFICULTY_DOWN_THRESHOLD = 0.50
    MIN_TRIALS_FOR_ADAPT = 5
