from backend.normalization import normalize_text

def test_repeated_spaces_collapse():
    assert normalize_text("Pink     Floyd") == "pink floyd"

def test_leading_and_trailing_whitespace():
    assert normalize_text("   Radiohead   ") == "radiohead"
