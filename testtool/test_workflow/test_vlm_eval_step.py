from unittest.mock import patch, MagicMock
from src.workflow.steps.vlm_eval_step import VLMEvalStep
from src.workflow.context import StepContext


def _ctx(config):
    ctx = StepContext(config=config)
    ctx.set('screenshot_path', '/tmp/x.png')
    return ctx


def test_single_mode_sets_primary_only():
    config = {'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'}}
    client = MagicMock()
    client.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': '5'}
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client', return_value=client):
        step = VLMEvalStep('evaluate')
        ctx = _ctx(config)
        result = step.execute(ctx)
    assert result.success
    assert ctx.get('score') == 5
    assert ctx.get('grading_mode') == 'single'
    assert ctx.get('score_secondary') is None
    assert ctx.get('score_consistent') is None


def test_dual_mode_consistent():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    primary = MagicMock(); primary.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': '5'}
    secondary = MagicMock(); secondary.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': 'five'}

    def factory(cfg):
        return primary if cfg.get('model') == 'mA' else secondary

    with patch('src.workflow.steps.vlm_eval_step.create_llm_client', side_effect=factory):
        step = VLMEvalStep('evaluate')
        ctx = _ctx(config)
        result = step.execute(ctx)
    assert result.success
    assert ctx.get('score') == 5
    assert ctx.get('score_secondary') == 5
    assert ctx.get('vlm_model_secondary') == 'mB'
    assert ctx.get('grading_mode') == 'dual'
    assert ctx.get('score_consistent') == 1


def test_dual_mode_inconsistent():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    primary = MagicMock(); primary.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': '5'}
    secondary = MagicMock(); secondary.evaluate.return_value = {'success': True, 'score': 3, 'raw_response': '3'}
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client', side_effect=lambda cfg: primary if cfg.get('model') == 'mA' else secondary):
        step = VLMEvalStep('evaluate')
        ctx = _ctx(config)
        step.execute(ctx)
    assert ctx.get('score_consistent') == 0


def test_dual_mode_secondary_failure_marks_inconsistent():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    primary = MagicMock(); primary.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': '5'}
    secondary = MagicMock(); secondary.evaluate.return_value = {'success': False, 'score': 0, 'raw_response': '', 'error': 'boom'}
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client', side_effect=lambda cfg: primary if cfg.get('model') == 'mA' else secondary):
        step = VLMEvalStep('evaluate')
        ctx = _ctx(config)
        result = step.execute(ctx)
    assert result.success            # 主成功即步骤成功
    assert ctx.get('score') == 5
    assert ctx.get('score_secondary') is None
    assert ctx.get('score_consistent') == 0


def test_dual_mode_secondary_exception_does_not_fail_step():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    primary = MagicMock(); primary.evaluate.return_value = {'success': True, 'score': 5, 'raw_response': '5'}
    secondary = MagicMock(); secondary.evaluate.side_effect = RuntimeError('network down')
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client',
               side_effect=lambda cfg: primary if cfg.get('model') == 'mA' else secondary):
        step = VLMEvalStep('evaluate')
        ctx = StepContext(config=config)
        ctx.set('screenshot_path', '/tmp/x.png')
        result = step.execute(ctx)
    assert result.success            # primary succeeded → step succeeds
    assert ctx.get('score') == 5
    assert ctx.get('score_secondary') is None
    assert ctx.get('score_consistent') == 0


def test_mock_single_mode_does_not_call_client():
    config = {'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'}}
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client') as factory:
        step = VLMEvalStep('evaluate', params={
            'mock_result': {
                'enabled': True,
                'primary': {'score': 4, 'explanation': 'mock primary'},
                'secondary': {'score': 4, 'explanation': 'mock secondary'},
            }
        })
        ctx = _ctx(config)
        result = step.execute(ctx)
    factory.assert_not_called()
    assert result.success
    assert result.data['score'] == 4
    assert result.data['raw_response'] == 'mock primary'
    assert ctx.get('score') == 4
    assert ctx.get('vlm_response') == 'mock primary'
    assert ctx.get('vlm_model') == 'mock'
    assert ctx.get('grading_mode') == 'single'
    assert ctx.get('score_secondary') is None


def test_mock_dual_mode_consistent():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client') as factory:
        step = VLMEvalStep('evaluate', params={
            'mock_result': {
                'enabled': True,
                'primary': {'score': 5, 'explanation': 'mock primary'},
                'secondary': {'score': 5, 'explanation': 'mock secondary'},
            }
        })
        ctx = _ctx(config)
        result = step.execute(ctx)
    factory.assert_not_called()
    assert result.success
    assert result.data['score'] == 5
    assert ctx.get('score') == 5
    assert ctx.get('vlm_response') == 'mock primary'
    assert ctx.get('vlm_model') == 'mock'
    assert ctx.get('score_secondary') == 5
    assert ctx.get('vlm_response_secondary') == 'mock secondary'
    assert ctx.get('vlm_model_secondary') == 'mock'
    assert ctx.get('grading_mode') == 'dual'
    assert ctx.get('score_consistent') == 1


def test_mock_dual_mode_inconsistent():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client') as factory:
        step = VLMEvalStep('evaluate', params={
            'mock_result': {
                'enabled': True,
                'primary': {'score': 5, 'explanation': 'mock primary'},
                'secondary': {'score': 3, 'explanation': 'mock secondary'},
            }
        })
        ctx = _ctx(config)
        result = step.execute(ctx)
    factory.assert_not_called()
    assert result.success
    assert ctx.get('score') == 5
    assert ctx.get('score_secondary') == 3
    assert ctx.get('score_consistent') == 0


def test_mock_disabled_uses_real_client():
    config = {'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'}}
    client = MagicMock()
    client.evaluate.return_value = {'success': True, 'score': 6, 'raw_response': '6'}
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client', return_value=client) as factory:
        step = VLMEvalStep('evaluate', params={
            'mock_result': {
                'enabled': False,
                'primary': {'score': 4, 'explanation': 'ignored'},
                'secondary': {'score': 4, 'explanation': 'ignored'},
            }
        })
        ctx = _ctx(config)
        result = step.execute(ctx)
    factory.assert_called_once()
    assert result.success
    assert ctx.get('score') == 6


def test_mock_null_score_defaults_to_zero():
    config = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'mA', 'prompt_template': 'p'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB', 'prompt_template': 'p2'},
    }
    with patch('src.workflow.steps.vlm_eval_step.create_llm_client') as factory:
        step = VLMEvalStep('evaluate', params={
            'mock_result': {
                'enabled': True,
                'primary': {'score': None, 'explanation': 'null score'},
                'secondary': {'score': None, 'explanation': 'null score'},
            }
        })
        ctx = _ctx(config)
        result = step.execute(ctx)
    factory.assert_not_called()
    assert result.success
    assert ctx.get('score') == 0
    assert ctx.get('score_secondary') == 0
