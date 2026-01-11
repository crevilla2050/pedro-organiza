from backend.normalization import normalize_text

def test_remaster_token_removed():
    assert normalize_text("Paranoid (2012 Remastered)") == "paranoid"

def test_multiple_noise_tokens_removed():
    assert normalize_text("Come Together - 2019 Stereo Mix") == "come together"

def test_noise_tokens_removed_only_as_words():
    assert normalize_text("Remasterpiece") == "remasterpiece"
