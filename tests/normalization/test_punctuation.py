from backend.normalization import normalize_text

def test_parentheses_removed_content_preserved():
    assert normalize_text("Wish You Were Here (Remastered)") == \
           "wish you were here remastered"

def test_hyphens_become_spaces():
    assert normalize_text("AC-DC") == "ac dc"

def test_mixed_punctuation_removed():
    assert normalize_text("Time, (The Dark Side of the Moon)") == \
           "time the dark side of the moon"
