from ai_engine.terminology.engine import TerminologyEngine,Term
def test_preserves_longest_overlapping_term():
    e=TerminologyEngine([Term("Machine"),Term("Machine Learning")])
    p,t=e.protect("Machine Learning works")
    assert "Machine Learning" not in p
    assert e.restore(p,t)=="Machine Learning works"
def test_alias_and_punctuation():
    e=TerminologyEngine([Term("Python",("python3",))])
    p,t=e.protect("Use python3, please.")
    assert e.restore(p,t)=="Use python3, please."
def test_case_sensitive():
    e=TerminologyEngine([Term("API",case_sensitive=True)])
    p,t=e.protect("api API")
    assert e.restore(p,t)=="api API"
def test_unicode_and_multiple():
    e=TerminologyEngine([Term("ಕನ್ನಡ"),Term("SQL")])
    p,t=e.protect("ಕನ್ನಡ and SQL!")
    assert e.restore(p,t)=="ಕನ್ನಡ and SQL!"
