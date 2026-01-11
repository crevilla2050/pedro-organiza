from backend.normalization import normalize_text

def test_diacritics_are_stripped():
    assert normalize_text("Björk Guðmundsdóttir") == "bjork gudmundsdottir"

def test_case_is_normalized():
    assert normalize_text("DaFt PuNk") == "daft punk"
