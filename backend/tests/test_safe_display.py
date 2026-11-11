from app.agents.present import safe_display


def test_flattens_untrusted_fields():
    assert safe_display("item\nstatus\tverified") == "itemstatusverified"
    assert safe_display("  order   shipped  ") == "order shipped"


def test_rejects_hidden_directional_controls():
    assert safe_display("abc\u202eXYZ") == "abcXYZ"


def test_caps_fields_and_handles_none():
    assert safe_display("a" * 500, 8) == "a" * 8
    assert safe_display(None) == "(not provided)"
