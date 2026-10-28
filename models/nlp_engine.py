"""
VocalRehab NLP Engine
=====================
Handles noisy dysarthric ASR output and classifies user intent
despite high phoneme error rates (up to 30%+ syllable drop).

Key techniques:
1. Phonetic encoding (Soundex, Metaphone, NYSIIS) for fuzzy matching
2. Levenshtein / Jaro-Winkler distance for edit-distance similarity
3. Phoneme-level confusion matrix for common dysarthric substitutions
4. Context-aware intent classification using semantic similarity
5. N-best hypothesis re-ranking
"""

import re
import json
import difflib
from collections import Counter

try:
    import jellyfish
    HAS_JELLYFISH = True
except ImportError:
    HAS_JELLYFISH = False


class NLPEngine:
    """Core NLP engine for dysarthric speech intent classification."""

    # ------------------------------------------------------------------ #
    # Common filler / hesitation tokens produced by dysarthric speakers
    # ------------------------------------------------------------------ #
    FILLER_PATTERN = re.compile(
        r"\b(um+|uh+|ah+|er+|eh+|hm+|hmm+|oh+|like|you know|i mean|well)\b",
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------ #
    # Dysarthric phoneme confusion matrix
    # Keys = intended phoneme, values = list of common substitutions
    # Based on clinical literature on dysarthric speech patterns:
    #   - Voiced / voiceless confusions
    #   - Manner confusions (stops <-> fricatives)
    #   - Place confusions (alveolar <-> velar)
    #   - Vowel tense / lax confusions
    #   - Final consonant deletion & cluster reduction
    # ------------------------------------------------------------------ #
    CONFUSION_MATRIX = {
        # Voiced <-> Voiceless stops
        "b": ["p", "m", "v"],
        "p": ["b", "f"],
        "d": ["t", "n", "th"],
        "t": ["d", "k"],
        "g": ["k", "d"],
        "k": ["g", "t"],
        # Fricatives
        "v": ["f", "b", "w"],
        "f": ["v", "p", "th"],
        "z": ["s", "d"],
        "s": ["z", "t", "th", "sh"],
        "sh": ["s", "ch", "zh"],
        "zh": ["sh", "z", "j"],
        "th": ["s", "f", "d", "t"],
        # Affricates
        "ch": ["sh", "t", "j"],
        "j": ["ch", "d", "zh"],
        # Nasals
        "m": ["n", "b"],
        "n": ["m", "d", "ng"],
        "ng": ["n", "g"],
        # Liquids & Glides
        "r": ["l", "w", "y"],
        "l": ["r", "w", "n"],
        "w": ["r", "l", "v"],
        "y": ["w", "l"],
        # Vowels (tense <-> lax)
        "iy": ["ih"],   # sheep <-> ship
        "ih": ["iy"],
        "uw": ["uh"],   # pool <-> pull
        "uh": ["uw"],
        "ey": ["eh"],   # bait <-> bet
        "eh": ["ey", "ae"],
        "ae": ["eh"],   # bat <-> bet
        "aa": ["ah"],   # cot <-> cut
        "ah": ["aa"],
    }

    # Character-level substitution cost overrides for weighted edit distance
    # Pairs that are commonly confused in dysarthria get a LOWER cost
    SUBSTITUTION_COSTS = {}
    for phoneme, confusions in CONFUSION_MATRIX.items():
        for confused_with in confusions:
            SUBSTITUTION_COSTS[(phoneme, confused_with)] = 0.3
            SUBSTITUTION_COSTS[(confused_with, phoneme)] = 0.3

    # ------------------------------------------------------------------ #
    # Articulatory tips keyed by phoneme
    # ------------------------------------------------------------------ #
    ARTICULATION_TIPS = {
        "b": "Press both lips firmly together, then release with a voiced burst. Try saying 'buh' slowly.",
        "p": "Press both lips together and release with a puff of air. Hold a tissue in front — it should flutter.",
        "d": "Place your tongue tip firmly on the ridge behind your upper teeth. Voice the sound.",
        "t": "Touch your tongue tip to the ridge behind your upper teeth and release with a puff of air.",
        "g": "Raise the back of your tongue to touch the soft palate. Feel the vibration in your throat.",
        "k": "Raise the back of your tongue to touch the soft palate and release with a puff of air.",
        "f": "Gently bite your lower lip with your upper teeth and blow air through steadily.",
        "v": "Gently bite your lower lip and hum — you should feel vibration in your lip.",
        "s": "Keep your tongue behind your teeth with a narrow gap. Blow a steady stream of air, like a snake hissing.",
        "z": "Same position as 's', but add your voice. Feel the buzz in your tongue.",
        "sh": "Round your lips slightly and push your tongue up. Blow a wide stream of air, like saying 'shh'.",
        "ch": "Start with your tongue in the 't' position, then release into 'sh'. It's like a sneeze — 'achoo'!",
        "th": "Put your tongue gently between your teeth and blow air. Look in a mirror — you should see your tongue tip.",
        "r": "Curl your tongue tip up slightly without touching the roof. Try saying 'rrr' like a growl.",
        "l": "Press your tongue tip firmly against the ridge behind your upper teeth. Let air flow around the sides.",
        "m": "Press both lips together and hum. You should feel vibration in your lips and nose.",
        "n": "Press your tongue tip behind your upper teeth and hum through your nose.",
        "w": "Round your lips into a small circle, then open them. Think of blowing out a candle.",
        "vowel_length": "Try to hold the vowel sound a little longer. Stretch it out like you're singing the note.",
        "final_consonant": "Focus on finishing the word clearly. Exaggerate the last sound — don't let it trail off.",
        "cluster": "Break the consonant cluster into two parts. Say each sound separately first, then blend them together.",
    }

    # ------------------------------------------------------------------ #
    # Common Dysarthric Phrase Bank
    # Maps garbled fragments to intended clear phrases.
    # These represent common needs/requests that dysarthria patients
    # frequently try to communicate (clinical ADL phrases).
    # ------------------------------------------------------------------ #
    PHRASE_BANK = [
        # Medical / Hospital needs
        "Hello doctor I need help",
        "Can I have some water please",
        "I am feeling pain in my head",
        "I want to go home today",
        "Thank you for helping me",
        "My name is a patient here",
        "Please call my family",
        "Is it time for my medicine",
        "I am feeling much better now",
        "I need to use the bathroom",
        "I am very hungry right now",
        "I want to eat something",
        "I need my wheelchair",
        "Can you help me stand up",
        "I feel dizzy right now",
        "I am feeling very tired",
        "I want to see my doctor",
        "I am having trouble breathing",
        "I need to rest now",
        "Can I have a blanket please",
        "My back hurts a lot",
        "I want to sit down please",
        "Please turn off the light",
        "I feel cold right now",
        "I feel hot right now",
        "I need my glasses please",
        "What time is it now",
        "Can I watch television please",
        "I want to talk to my family",
        "Please open the window",
        "Please close the door",
        "I want to go outside",

        # Daily life / Communication
        "Good morning how are you",
        "I am doing fine thank you",
        "I don't understand what you said",
        "Can you repeat that please",
        "I want to go to the store",
        "What is for dinner today",
        "I need to take my medicine",
        "Can you drive me to the hospital",
        "I need to see my therapist",
        "Please help me get dressed",
        "I want to brush my teeth",
        "Can I have some more food",
        "I am feeling happy today",
        "I am feeling sad today",
        "I love you very much",
        "Please be patient with me",
        "I am trying my best",
        "Can you understand me",
        "Yes I agree with you",
        "No I don't want that",
        "I want to go to sleep",
        "Please wake me up later",
        "I am in a lot of pain",
        "I feel much better today",
        "Thank you for your help",
        "I appreciate your patience",

        # Therapy-specific
        "The ship is near the sheep",
        "The cat sat on the mat",
        "Please pass me the cup",
        "I can see the big tree",
        "The dog is in the park",
        "She sells sea shells",
        "Peter picked a pepper",
        "How much wood could a woodchuck chuck",
        "The rain in Spain falls mainly on the plain",
        "Red lorry yellow lorry",
    ]

    # Common dysarthric word mappings (what ASR hears -> what they meant)
    DYSARTHRIC_WORD_MAP = {
        # Truncated / slurred words
        "wah": "want", "wan": "want", "waw": "want", "waht": "want",
        "wa": "want", "wuh": "want",
        "hoh": "home", "hoe": "home", "ho": "home", "hom": "home",
        "heh": "help", "hel": "help", "hep": "help", "hah": "have",
        "doh": "doctor", "dor": "doctor", "dah": "doctor", "doc": "doctor",
        "nee": "need", "neh": "need", "ne": "need",
        "wah der": "water", "wader": "water", "wadder": "water",
        "wotter": "water", "wata": "water",
        "pees": "please", "pee": "please", "plez": "please",
        "peez": "please", "pleh": "please",
        "fee": "feeling", "feeing": "feeling", "feelin": "feeling",
        "fee ing": "feeling", "feelin": "feeling",
        "pay": "pain", "pah": "pain", "pai": "pain",
        "ahm": "am", "ah": "am", "uhm": "am",
        "ih": "in", "ihn": "in",
        "heh": "head", "hed": "head",
        "thah": "thank", "thak": "thank", "tahk": "thank",
        "foh": "for", "fo": "for", "faw": "for",
        "mee": "me", "meh": "me",
        "nay": "name", "naym": "name",
        "cah": "call", "caw": "call", "cal": "call",
        "fah": "family", "fahm": "family", "fam": "family",
        "tie": "time", "tye": "time",
        "sin": "medicine", "med sin": "medicine", "medsin": "medicine",
        "beh er": "better", "beh": "better", "betta": "better",
        "muh": "much", "muc": "much",
        "shih": "ship", "shee": "sheep",
        "bah roo": "bathroom", "bahroo": "bathroom", "bafroom": "bathroom",
        "huh gree": "hungry", "hungree": "hungry",
        "veh": "very", "verry": "very",
        "rye": "right", "rie": "right",
        "oo": "use", "yoo": "use", "oos": "use",
        "duh": "the", "da": "the", "de": "the",
        "suh": "some", "su": "some", "som": "some",
        "hah": "have", "hav": "have",
        "to day": "today", "toodey": "today",
        "goh": "go", "goo": "go",
        # Common ASR mishears for dysarthric speech
        "was": "want", "wasp": "want", "what": "want",
        "eye": "I", "aye": "I",
        "do": "to", "too": "to", "tuh": "to",
    }

    def __init__(self):
        """Initialize the NLP engine with phonetic maps and configuration."""
        self._build_char_confusion_set()
        self._build_phrase_index()

    def _build_char_confusion_set(self):
        """Build a fast lookup set for confused character pairs."""
        self._confused_pairs = set()
        for (a, b) in self.SUBSTITUTION_COSTS:
            self._confused_pairs.add((a, b))

    def _build_phrase_index(self):
        """Pre-compute phonetic signatures for all phrases in the bank."""
        self._phrase_words = []
        for phrase in self.PHRASE_BANK:
            words = phrase.lower().split()
            self._phrase_words.append({
                "phrase": phrase,
                "words": words,
                "word_set": set(words),
                "length": len(words),
            })

    # ================================================================== #
    #  DYSARTHRIC SPEECH TRANSLATION
    # ================================================================== #

    def translate_dysarthric(self, raw_text: str, alternatives: list = None) -> dict:
        """
        Translate garbled dysarthric speech into the most likely intended
        clear phrase.  Uses a multi-stage pipeline:

        1. Word-level repair using DYSARTHRIC_WORD_MAP
        2. Phrase-level matching against PHRASE_BANK using phonetic similarity
        3. N-best alternative fusion
        4. Context-aware re-ranking

        Returns dict with:
            raw_text:       Original ASR text
            repaired_text:  After word-level repair
            clean_text:     Best matching phrase from bank (or repaired if no match)
            confidence:     Overall confidence [0-1]
            match_method:   How the match was found
            corrections:    Number of word-level corrections made
        """
        if not raw_text or not raw_text.strip():
            return {
                "raw_text": raw_text,
                "repaired_text": "",
                "clean_text": "",
                "confidence": 0,
                "match_method": "none",
                "corrections": 0,
            }

        cleaned = self.preprocess_text(raw_text)
        all_texts = [cleaned]
        if alternatives:
            for alt in alternatives:
                a = self.preprocess_text(alt) if isinstance(alt, str) else self.preprocess_text(str(alt))
                if a and a not in all_texts:
                    all_texts.append(a)

        # ---- Stage 1: Word-level repair ----
        repaired_words = []
        corrections = 0
        for word in cleaned.split():
            mapped = self.DYSARTHRIC_WORD_MAP.get(word)
            if mapped:
                repaired_words.append(mapped)
                corrections += 1
            else:
                repaired_words.append(word)
        repaired_text = " ".join(repaired_words)

        # Also repair each alternative
        repaired_alternatives = [repaired_text]
        for alt_text in all_texts[1:]:
            rw = []
            for word in alt_text.split():
                mapped = self.DYSARTHRIC_WORD_MAP.get(word)
                rw.append(mapped if mapped else word)
            rt = " ".join(rw)
            if rt not in repaired_alternatives:
                repaired_alternatives.append(rt)

        # ---- Stage 2: Phrase-level matching ----
        best_phrase = None
        best_score = 0.0
        best_method = "word_repair"

        for candidate_text in repaired_alternatives + all_texts:
            cand_words = candidate_text.split()

            for entry in self._phrase_words:
                phrase = entry["phrase"]
                phrase_words = entry["words"]

                # 2a. Compute word overlap score (how many words from candidate
                #     appear in or phonetically match phrase words)
                overlap_score = self._phrase_overlap_score(cand_words, phrase_words)

                # 2b. Compute full-string phonetic similarity
                string_sim = self._phrase_string_similarity(candidate_text, phrase.lower())

                # 2c. Combine: overlap matters more for short ASR fragments
                #     (which is the main problem — ASR only gets 1-2 words)
                if len(cand_words) <= 2:
                    combined = 0.55 * overlap_score + 0.45 * string_sim
                else:
                    combined = 0.40 * overlap_score + 0.60 * string_sim

                if combined > best_score:
                    best_score = combined
                    best_phrase = phrase
                    best_method = "phrase_bank_match"

        # ---- Stage 3: Decide output ----
        # Threshold: only use phrase bank match if confidence is reasonable
        # Higher threshold prevents garbage ASR → wrong phrase matches
        if best_score >= 0.42 and best_phrase:
            clean_text = best_phrase
            confidence = min(1.0, best_score * 1.1)
            # Determine reliability level based on score
            if best_score >= 0.70:
                reliability = "high"
            elif best_score >= 0.55:
                reliability = "medium"
            else:
                reliability = "low"
        else:
            # Fall back to word-level repair only
            clean_text = repaired_text
            confidence = max(0.15, best_score * 0.8) if best_score > 0 else 0.15
            best_method = "word_repair"
            reliability = "low"

        # Capitalize
        if clean_text:
            clean_text = clean_text[0].upper() + clean_text[1:]

        return {
            "raw_text": raw_text,
            "repaired_text": repaired_text,
            "clean_text": clean_text,
            "confidence": round(confidence, 4),
            "match_method": best_method,
            "corrections": corrections,
            "reliability": reliability,
        }

    def _phrase_overlap_score(self, candidate_words: list, phrase_words: list) -> float:
        """
        Score how well candidate words match phrase words using both
        exact matching and phonetic similarity.
        Returns 0-1.
        """
        if not phrase_words:
            return 0.0

        matched = 0
        used_indices = set()

        for cw in candidate_words:
            best_match_score = 0.0
            best_idx = -1

            for i, pw in enumerate(phrase_words):
                if i in used_indices:
                    continue

                # Exact match
                if cw == pw:
                    score = 1.0
                # Check dysarthric word map
                elif self.DYSARTHRIC_WORD_MAP.get(cw) == pw:
                    score = 0.9
                else:
                    # Phonetic similarity
                    sim = self.compute_similarity(cw, pw)
                    score = sim["combined"]

                if score > best_match_score:
                    best_match_score = score
                    best_idx = i

            if best_match_score >= 0.45 and best_idx >= 0:
                matched += best_match_score
                used_indices.add(best_idx)

        # Normalize: penalize if candidate has very few words relative to phrase
        coverage = matched / len(phrase_words)
        # Bonus if candidate matched most of its own words
        if candidate_words:
            match_ratio = len(used_indices) / len(candidate_words)
        else:
            match_ratio = 0
        return 0.7 * coverage + 0.3 * match_ratio

    def _phrase_string_similarity(self, candidate: str, phrase: str) -> float:
        """
        Compute string-level similarity between candidate and phrase
        using multiple methods.
        """
        # Sequence ratio
        seq = difflib.SequenceMatcher(None, candidate, phrase).ratio()

        # Jaro-Winkler if available
        if HAS_JELLYFISH:
            try:
                jw = jellyfish.jaro_winkler_similarity(candidate, phrase)
            except Exception:
                jw = seq
        else:
            jw = seq

        # Confusion-aware similarity at character level
        conf = self._confusion_aware_similarity(candidate, phrase)

        return 0.30 * seq + 0.35 * jw + 0.35 * conf

    # ================================================================== #
    #  TEXT PREPROCESSING
    # ================================================================== #

    def preprocess_text(self, text) -> str:
        """
        Normalize ASR output:
        - Handle dict or string
        - Lowercase
        - Remove filler words and hesitations
        - Collapse whitespace
        - Strip punctuation except apostrophes (for contractions)
        """
        if not text:
            return ""
        if isinstance(text, dict):
            text = text.get("transcript", "") or ""
        elif not isinstance(text, str):
            text = str(text)

        text = text.lower().strip()
        text = self.FILLER_PATTERN.sub(" ", text)
        text = re.sub(r"[^\w\s']", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ================================================================== #
    #  PHONETIC ENCODING
    # ================================================================== #

    def phonetic_encode(self, word: str) -> dict:
        """
        Return multiple phonetic encodings of a word.
        Uses jellyfish library when available, falls back to built-in soundex.
        """
        word = word.lower().strip()
        result = {"original": word}

        if HAS_JELLYFISH:
            try:
                result["soundex"] = jellyfish.soundex(word)
            except Exception:
                result["soundex"] = self._simple_soundex(word)
            try:
                result["metaphone"] = jellyfish.metaphone(word)
            except Exception:
                result["metaphone"] = ""
            try:
                result["nysiis"] = jellyfish.nysiis(word)
            except Exception:
                result["nysiis"] = ""
        else:
            result["soundex"] = self._simple_soundex(word)
            result["metaphone"] = self._simple_metaphone(word)
            result["nysiis"] = ""

        return result

    @staticmethod
    def _simple_soundex(word: str) -> str:
        """Fallback Soundex implementation."""
        if not word:
            return ""
        word = word.upper()
        code_map = {
            "B": "1", "F": "1", "P": "1", "V": "1",
            "C": "2", "G": "2", "J": "2", "K": "2",
            "Q": "2", "S": "2", "X": "2", "Z": "2",
            "D": "3", "T": "3",
            "L": "4",
            "M": "5", "N": "5",
            "R": "6",
        }
        result = [word[0]]
        prev = code_map.get(word[0], "0")
        for ch in word[1:]:
            code = code_map.get(ch, "0")
            if code != "0" and code != prev:
                result.append(code)
            prev = code if code != "0" else prev
            if len(result) == 4:
                break
        return "".join(result).ljust(4, "0")

    @staticmethod
    def _simple_metaphone(word: str) -> str:
        """Very simplified metaphone for fallback."""
        if not word:
            return ""
        word = word.upper()
        # Drop duplicate adjacent letters
        result = [word[0]]
        for ch in word[1:]:
            if ch != result[-1]:
                result.append(ch)
        # Drop vowels (except leading)
        cleaned = result[0] + "".join(c for c in result[1:] if c not in "AEIOU")
        return cleaned[:6]

    # ================================================================== #
    #  SIMILARITY COMPUTATION
    # ================================================================== #

    def compute_similarity(self, word1: str, word2: str) -> dict:
        """
        Combined similarity score using:
        1. Sequence ratio (difflib)
        2. Phonetic similarity (Soundex / Metaphone match)
        3. Dysarthric confusion-aware weighted edit distance
        4. Jaro-Winkler (if jellyfish available)

        Returns dict with individual scores and a combined weighted score [0-1].
        """
        w1 = word1.lower().strip()
        w2 = word2.lower().strip()

        # 1. Sequence ratio
        seq_ratio = difflib.SequenceMatcher(None, w1, w2).ratio()

        # 2. Phonetic similarity
        enc1 = self.phonetic_encode(w1)
        enc2 = self.phonetic_encode(w2)
        phonetic_score = 0.0
        phonetic_matches = 0
        for key in ["soundex", "metaphone", "nysiis"]:
            if enc1.get(key) and enc2.get(key):
                if enc1[key] == enc2[key]:
                    phonetic_matches += 1
        phonetic_score = phonetic_matches / 3.0

        # 3. Dysarthric confusion-aware score
        confusion_score = self._confusion_aware_similarity(w1, w2)

        # 4. Jaro-Winkler
        if HAS_JELLYFISH:
            try:
                jw_score = jellyfish.jaro_winkler_similarity(w1, w2)
            except Exception:
                jw_score = seq_ratio
        else:
            jw_score = seq_ratio

        # Combined weighted score
        combined = (
            0.25 * seq_ratio
            + 0.20 * phonetic_score
            + 0.30 * confusion_score
            + 0.25 * jw_score
        )

        return {
            "sequence_ratio": round(seq_ratio, 4),
            "phonetic_score": round(phonetic_score, 4),
            "confusion_score": round(confusion_score, 4),
            "jaro_winkler": round(jw_score, 4),
            "combined": round(combined, 4),
        }

    def _confusion_aware_similarity(self, w1: str, w2: str) -> float:
        """
        Edit-distance similarity with lower costs for dysarthric-common
        substitutions and deletions.
        """
        n, m = len(w1), len(w2)
        if n == 0 and m == 0:
            return 1.0
        if n == 0 or m == 0:
            return 0.0

        # Dynamic programming with custom costs
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = i * 0.8  # deletion cost (lower for final consonant drop)
        for j in range(m + 1):
            dp[0][j] = j * 1.0  # insertion cost

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if w1[i - 1] == w2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    sub_cost = self.SUBSTITUTION_COSTS.get(
                        (w1[i - 1], w2[j - 1]), 1.0
                    )
                    # Lower deletion cost for final position (final consonant drop)
                    del_cost = 0.5 if i == n else 0.8
                    dp[i][j] = min(
                        dp[i - 1][j - 1] + sub_cost,  # substitution
                        dp[i - 1][j] + del_cost,       # deletion
                        dp[i][j - 1] + 1.0,            # insertion
                    )

        max_len = max(n, m)
        distance = dp[n][m]
        similarity = max(0.0, 1.0 - (distance / max_len))
        return similarity

    # ================================================================== #
    #  INTENT CLASSIFICATION
    # ================================================================== #

    def classify_intent(self, asr_output: str, target_words: list,
                        alternatives: list = None, context: str = None) -> dict:
        """
        Given noisy ASR text and a list of target minimal-pair words,
        determine which word the user most likely intended.

        Parameters:
            asr_output:   Primary ASR transcript (may be noisy/garbled)
            target_words: List of valid target words (e.g., ["ship", "sheep"])
            alternatives: N-best ASR hypotheses for re-ranking
            context:      Optional context hint (e.g., sentence or category)

        Returns dict with:
            predicted_word: Best matching target word
            confidence:     Confidence score [0-1]
            all_scores:     Scores for each target word
            phoneme_analysis: Detailed phoneme-level analysis
            method:         Which matching method dominated
        """
        asr_clean = self.preprocess_text(asr_output)
        all_candidates = [asr_clean]
        if alternatives:
            all_candidates.extend(
                self.preprocess_text(alt) for alt in alternatives if alt
            )

        # Score each target word against ALL candidates
        word_scores = {}
        for target in target_words:
            target_lower = target.lower().strip()
            best_score = 0.0
            best_method = "similarity"

            for candidate in all_candidates:
                # Check for exact match first
                if target_lower in candidate.split():
                    best_score = max(best_score, 1.0)
                    best_method = "exact_match"
                    continue

                # Check each word in the candidate
                for cand_word in candidate.split():
                    sim = self.compute_similarity(cand_word, target_lower)
                    score = sim["combined"]

                    # Boost if phonetic encodings match
                    if sim["phonetic_score"] > 0.5:
                        score = min(1.0, score + 0.1)

                    if score > best_score:
                        best_score = score
                        best_method = "similarity"

                # Also check the full candidate string
                sim_full = self.compute_similarity(candidate, target_lower)
                if sim_full["combined"] > best_score:
                    best_score = sim_full["combined"]

            word_scores[target] = {
                "score": round(best_score, 4),
                "method": best_method,
            }

        # Find the best match
        predicted = max(word_scores, key=lambda w: word_scores[w]["score"])
        best = word_scores[predicted]["score"]

        # Calculate confidence (based on margin between top two)
        scores_sorted = sorted(word_scores.values(), key=lambda x: x["score"],
                               reverse=True)
        if len(scores_sorted) >= 2:
            margin = scores_sorted[0]["score"] - scores_sorted[1]["score"]
            confidence = min(1.0, best * 0.6 + margin * 2.0)
        else:
            confidence = best

        # Phoneme analysis for the predicted word vs ASR output
        phoneme_analysis = self.analyze_phoneme_errors(asr_clean, predicted)

        return {
            "predicted_word": predicted,
            "confidence": round(confidence, 4),
            "all_scores": word_scores,
            "phoneme_analysis": phoneme_analysis,
            "method": word_scores[predicted]["method"],
            "asr_cleaned": asr_clean,
        }

    # ================================================================== #
    #  PHONEME ERROR ANALYSIS
    # ================================================================== #

    def analyze_phoneme_errors(self, spoken: str, target: str) -> dict:
        """
        Detailed analysis of which characters/phonemes were substituted,
        dropped, or distorted between the spoken output and the target word.

        Returns a structured error report.
        """
        spoken = spoken.lower().strip()
        target = target.lower().strip()

        # If spoken contains the target exactly, no errors
        if target in spoken.split():
            return {
                "match": True,
                "errors": [],
                "error_count": 0,
                "error_types": {},
                "accuracy": 1.0,
            }

        # Find the closest word in spoken to the target
        best_word = spoken
        best_ratio = 0
        for w in spoken.split():
            r = difflib.SequenceMatcher(None, w, target).ratio()
            if r > best_ratio:
                best_ratio = r
                best_word = w

        # Use SequenceMatcher to find operations
        matcher = difflib.SequenceMatcher(None, best_word, target)
        opcodes = matcher.get_opcodes()

        errors = []
        error_types = Counter()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                continue
            elif tag == "replace":
                spoken_chars = best_word[i1:i2]
                target_chars = target[j1:j2]
                error_type = "substitution"
                # Check if it's a known dysarthric confusion
                if len(spoken_chars) == 1 and len(target_chars) == 1:
                    if (spoken_chars, target_chars) in self._confused_pairs:
                        error_type = "dysarthric_substitution"
                errors.append({
                    "type": error_type,
                    "position": j1,
                    "expected": target_chars,
                    "produced": spoken_chars,
                    "position_label": self._position_label(j1, len(target)),
                })
                error_types[error_type] += 1
            elif tag == "delete":
                errors.append({
                    "type": "insertion",
                    "position": j1,
                    "expected": "",
                    "produced": best_word[i1:i2],
                    "position_label": self._position_label(j1, len(target)),
                })
                error_types["insertion"] += 1
            elif tag == "insert":
                err_type = "deletion"
                if j1 >= len(target) - 1:
                    err_type = "final_consonant_deletion"
                elif j1 == 0:
                    err_type = "initial_deletion"
                errors.append({
                    "type": err_type,
                    "position": j1,
                    "expected": target[j1:j2],
                    "produced": "",
                    "position_label": self._position_label(j1, len(target)),
                })
                error_types[err_type] += 1

        accuracy = matcher.ratio()

        return {
            "match": len(errors) == 0,
            "spoken_word": best_word,
            "target_word": target,
            "errors": errors,
            "error_count": len(errors),
            "error_types": dict(error_types),
            "accuracy": round(accuracy, 4),
        }

    @staticmethod
    def _position_label(pos: int, length: int) -> str:
        """Label a character position as initial, medial, or final."""
        if pos == 0:
            return "initial"
        elif pos >= length - 1:
            return "final"
        return "medial"

    # ================================================================== #
    #  FEEDBACK GENERATION
    # ================================================================== #

    def generate_feedback(self, analysis_result: dict, is_correct: bool) -> str:
        """
        Generate natural language feedback based on phoneme analysis.
        Warm, encouraging tone suitable for therapy patients.
        """
        if is_correct and analysis_result.get("match", False):
            return "Perfect pronunciation! That was crystal clear! 🌟"

        if is_correct:
            return "Great job — I understood you correctly! Keep it up! 🎉"

        errors = analysis_result.get("errors", [])
        if not errors:
            return "Good try! Let's practice that word one more time. You've got this! 💪"

        # Build specific tips based on the first error found
        tips = []
        seen_types = set()

        for error in errors[:2]:  # Focus on first 2 errors max
            etype = error["type"]
            expected = error.get("expected", "")
            position = error.get("position_label", "")

            if etype in seen_types:
                continue
            seen_types.add(etype)

            if etype == "final_consonant_deletion":
                tips.append(
                    f"💡 Try to finish the word with a clear '{expected}' sound. "
                    + self.ARTICULATION_TIPS.get("final_consonant", "")
                )
            elif etype == "initial_deletion":
                tip = self.ARTICULATION_TIPS.get(expected, "")
                tips.append(
                    f"💡 Focus on starting the word with '{expected}'. {tip}"
                )
            elif etype in ("substitution", "dysarthric_substitution"):
                produced = error.get("produced", "")
                tip = self.ARTICULATION_TIPS.get(expected, "")
                if tip:
                    tips.append(
                        f"💡 I heard '{produced}' instead of '{expected}'. {tip}"
                    )
                else:
                    tips.append(
                        f"💡 Try to make the '{expected}' sound a bit more distinct "
                        f"from '{produced}'. Take your time!"
                    )
            elif etype == "deletion":
                tips.append(
                    f"💡 The '{expected}' sound was missing. "
                    + self.ARTICULATION_TIPS.get("cluster", "")
                )

        if not tips:
            tips.append("💡 Take a breath, slow down, and try again. You're doing great! 💪")

        return "Almost there! " + " ".join(tips)

    # ================================================================== #
    #  SEVERITY ASSESSMENT
    # ================================================================== #

    def assess_severity(self, session_scores: list) -> dict:
        """
        Given a list of trial accuracy scores (0.0-1.0) from a session,
        classify dysarthria severity and suggest appropriate difficulty.

        Based on clinical intelligibility score ranges:
          - Mild:     accuracy >= 70%
          - Moderate: accuracy 40-69%
          - Severe:   accuracy < 40%
        """
        if not session_scores:
            return {
                "severity": "unknown",
                "avg_accuracy": 0,
                "suggested_difficulty": 1,
                "recommendation": "Complete a few exercises so we can learn your speech patterns.",
            }

        avg = sum(session_scores) / len(session_scores)
        correct_ratio = sum(1 for s in session_scores if s >= 0.5) / len(session_scores)

        if correct_ratio >= 0.70:
            severity = "mild"
            difficulty = 3
            rec = (
                "Your speech clarity is strong! We can challenge you with "
                "harder word pairs and consonant clusters."
            )
        elif correct_ratio >= 0.40:
            severity = "moderate"
            difficulty = 2
            rec = (
                "You're making solid progress! Let's keep practicing with "
                "clear, common word pairs to build consistency."
            )
        else:
            severity = "severe"
            difficulty = 1
            rec = (
                "Great effort on every attempt! We'll focus on simple, "
                "high-contrast pairs and build up gradually. Every practice counts!"
            )

        return {
            "severity": severity,
            "avg_accuracy": round(avg, 4),
            "correct_ratio": round(correct_ratio, 4),
            "suggested_difficulty": difficulty,
            "recommendation": rec,
            "trials_analyzed": len(session_scores),
        }

    # ================================================================== #
    #  DYSARTHRIC CONFUSION MATRIX (public accessor)
    # ================================================================== #

    def get_dysarthric_confusion_matrix(self) -> dict:
        """Return the full phoneme confusion matrix for inspection."""
        return dict(self.CONFUSION_MATRIX)
