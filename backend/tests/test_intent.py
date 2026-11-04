import pytest
from app.services.intent_schema import Intent, get_vocab
from app.services.rules_parser import RulesParser, rules_parser

def test_intent_schema_vocabulary_filtering():
    # Valid vocab tags should be preserved, unknown tags silently dropped
    intent = Intent(
        moods=["calm", "invalid_mood_123", "relaxing", "calm", "focus", "sleep"],
        genres=["ambient", "fake_genre_456", "lofi"],
        avoid_genres=["rock", "not_a_genre"],
        context="A very long context string that exceeds sixty characters in total length should be truncated",
        confidence=1.5,
    )

    # Max 3 moods, unknown dropped, duplicates removed, order kept
    assert intent.moods == ["calm", "relaxing", "focus"]
    # Valid genres kept
    assert intent.genres == ["ambient", "lofi"]
    # Avoid genres
    assert intent.avoid_genres == ["rock"]
    # Context truncated to <= 60 chars
    assert len(intent.context) <= 60
    # Confidence clamped
    assert intent.confidence == 1.0

def test_intent_schema_empty():
    intent = Intent()
    assert intent.moods == []
    assert intent.genres == []
    assert intent.avoid_genres == []
    assert intent.context is None
    assert intent.confidence == 1.0

def test_rules_parser_calm_study():
    result = rules_parser.parse("calm study beats for revision")
    assert "calm" in result.moods or "focus" in result.moods or "study" in result.moods
    assert "lofi" in result.genres or "ambient" in result.genres or "classical" in result.genres
    assert result.context == "study"
    assert result.confidence >= 0.8

def test_rules_parser_sleep_night():
    result = rules_parser.parse("deep sleep sounds for late night")
    assert "sleep" in result.moods or "calm" in result.moods
    assert result.context == "late night"
    assert result.confidence >= 0.8

def test_rules_parser_happy_upbeat():
    result = rules_parser.parse("happy upbeat fun party track")
    assert "happy" in result.moods or "energetic" in result.moods
    assert result.confidence >= 0.8

def test_rules_parser_sad_rain():
    result = rules_parser.parse("sad rain and lonely melancholy")
    assert "sad" in result.moods or "calm" in result.moods
    assert result.confidence >= 0.8

def test_rules_parser_gym_workout():
    result = rules_parser.parse("gym workout pump energetic music")
    assert "energetic" in result.moods
    assert "rock" in result.genres or "electronic" in result.genres
    assert result.confidence >= 0.8

def test_rules_parser_romantic():
    result = rules_parser.parse("romantic date night love songs")
    assert "romantic" in result.moods
    assert "jazz" in result.genres or "chillout" in result.genres
    assert result.confidence >= 0.8

def test_rules_parser_dreamy_ambient():
    result = rules_parser.parse("dream dreamy ambient music")
    assert "dream" in result.moods or "atmospheric" in result.moods
    assert "ambient" in result.genres
    assert result.confidence >= 0.8

def test_rules_parser_negation_handling():
    result = rules_parser.parse("calm study no rock without jazz")
    assert "rock" in result.avoid_genres
    assert "jazz" in result.avoid_genres
    assert "rock" not in result.genres
    assert "jazz" not in result.genres

def test_rules_parser_fallback_on_unrecognized():
    result = rules_parser.parse("xyzabc qwerty obscure phrase")
    assert len(result.moods) > 0
    assert result.confidence < 0.5
