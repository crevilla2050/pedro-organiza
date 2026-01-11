from backend.normalization import normalize_text

def test_idempotence():
    assert normalize_text("pink floyd") == "pink floyd"

def test_empty_string():
    assert normalize_text("") == ""

def test_none_input():
    assert normalize_text(None) == ""
