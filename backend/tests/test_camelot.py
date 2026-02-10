"""Tests for Camelot Wheel logic."""

from app.analysis.camelot import (
    key_to_camelot, camelot_distance, camelot_relation, harmonic_score,
)


class TestKeyToCamelot:
    def test_common_keys(self):
        assert key_to_camelot("Am") == "8A"
        assert key_to_camelot("C") == "8B"
        assert key_to_camelot("Em") == "9A"
        assert key_to_camelot("G") == "9B"

    def test_full_names(self):
        assert key_to_camelot("A minor") == "8A"
        assert key_to_camelot("C major") == "8B"

    def test_unknown_key(self):
        assert key_to_camelot("X#dim7") == "?"


class TestCamelotDistance:
    def test_same_key(self):
        assert camelot_distance("8A", "8A") == 0

    def test_relative_major_minor(self):
        # Am (8A) and C (8B) are relative major/minor
        assert camelot_distance("8A", "8B") == 0

    def test_adjacent(self):
        assert camelot_distance("8A", "9A") == 1
        assert camelot_distance("8A", "7A") == 1

    def test_wrap_around(self):
        assert camelot_distance("1A", "12A") == 1
        assert camelot_distance("12A", "1A") == 1

    def test_far_keys(self):
        assert camelot_distance("1A", "7A") == 6

    def test_unknown(self):
        assert camelot_distance("?", "8A") == -1


class TestCamelotRelation:
    def test_same(self):
        assert camelot_relation("8A", "8A") == "same"
        assert camelot_relation("8A", "8B") == "same"

    def test_adjacent(self):
        assert camelot_relation("8A", "9A") == "adjacent"

    def test_relative(self):
        assert camelot_relation("8A", "10A") == "relative"

    def test_incompatible(self):
        assert camelot_relation("1A", "7A") == "incompatible"


class TestHarmonicScore:
    def test_same_key_perfect(self):
        assert harmonic_score("8A", "8A") == 1.0

    def test_adjacent_high(self):
        assert harmonic_score("8A", "9A") == 0.85

    def test_far_keys_low(self):
        assert harmonic_score("1A", "7A") <= 0.1
