from src.workflow.dual_grading import is_dual_enabled


def test_dual_disabled_when_no_secondary():
    assert is_dual_enabled({'llm': {'model': 'm'}}) is False


def test_dual_disabled_when_enabled_false():
    cfg = {'llm_secondary': {'enabled': False, 'api_key': 'k', 'model': 'm'}}
    assert is_dual_enabled(cfg) is False


def test_dual_disabled_when_missing_key_or_model():
    assert is_dual_enabled({'llm_secondary': {'enabled': True, 'model': 'm'}}) is False
    assert is_dual_enabled({'llm_secondary': {'enabled': True, 'api_key': 'k'}}) is False


def test_dual_enabled_when_complete():
    cfg = {'llm_secondary': {'api_key': 'k', 'model': 'm'}}  # enabled 缺省视为 True
    assert is_dual_enabled(cfg) is True
