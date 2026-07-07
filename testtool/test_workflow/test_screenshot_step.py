from unittest.mock import patch, MagicMock
from src.workflow.steps.screenshot_step import ScreenshotStep
from src.workflow.context import StepContext


def _make_capture(paths):
    cap = MagicMock()
    cap.capture.side_effect = [(p, MagicMock()) for p in paths]
    return cap


def test_screenshot_without_human_region():
    config = {'region': {'capture': {'x1': 0, 'y1': 0, 'x2': 10, 'y2': 10}},
              'paths': {'screenshots': '/tmp'}}
    cap = _make_capture(['/tmp/model.png'])
    with patch('src.workflow.steps.screenshot_step.ScreenCapture', return_value=cap):
        with patch('os.path.getsize', return_value=1024):
            with patch('os.path.exists', return_value=True):
                ctx = StepContext(config=config)
                result = ScreenshotStep('screenshot', {'region': 'capture'}).execute(ctx)
    assert result.success
    assert ctx.get('screenshot_path') == '/tmp/model.png'
    assert ctx.get('screenshot_human_path') is None
    assert cap.capture.call_count == 1


def test_screenshot_with_human_region():
    config = {'region': {
        'capture': {'x1': 0, 'y1': 0, 'x2': 10, 'y2': 10},
        'capture_human': {'x1': 0, 'y1': 0, 'x2': 50, 'y2': 50},
    }, 'paths': {'screenshots': '/tmp'}}
    cap = _make_capture(['/tmp/model.png', '/tmp/human.png'])
    with patch('src.workflow.steps.screenshot_step.ScreenCapture', return_value=cap):
        with patch('os.path.getsize', return_value=1024):
            with patch('os.path.exists', return_value=True):
                ctx = StepContext(config=config)
                result = ScreenshotStep('screenshot', {'region': 'capture'}).execute(ctx)
    assert result.success
    assert ctx.get('screenshot_path') == '/tmp/model.png'
    assert ctx.get('screenshot_human_path') == '/tmp/human.png'
    assert cap.capture.call_count == 2


def test_screenshot_human_capture_failure_does_not_fail_step():
    """人看截图抛异常时不应让步骤失败，模型截图仍然有效"""
    config = {'region': {
        'capture': {'x1': 0, 'y1': 0, 'x2': 10, 'y2': 10},
        'capture_human': {'x1': 0, 'y1': 0, 'x2': 50, 'y2': 50},
    }, 'paths': {'screenshots': '/tmp'}}
    cap = MagicMock()
    # 第一次（模型截图）成功，第二次（人看截图）抛异常
    cap.capture.side_effect = [('/tmp/model.png', MagicMock()), RuntimeError('grab failed')]
    with patch('src.workflow.steps.screenshot_step.ScreenCapture', return_value=cap):
        with patch('os.path.getsize', return_value=1024):
            with patch('os.path.exists', return_value=True):
                ctx = StepContext(config=config)
                result = ScreenshotStep('screenshot', {'region': 'capture'}).execute(ctx)
    assert result.success
    assert ctx.get('screenshot_path') == '/tmp/model.png'
    assert ctx.get('screenshot_human_path') is None
    assert cap.capture.call_count == 2
