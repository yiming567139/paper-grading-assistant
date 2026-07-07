"""测试 StepLogger 分环节日志记录器"""
import os
from src.utils.logger import StepLogger


def test_step_logger_screenshot(temp_log_dir):
    """测试截图环节日志记录"""
    logger = StepLogger(temp_log_dir)
    logger.screenshot_start('task_001')
    logger.screenshot_done('/tmp/test.png', 150)

    log_file = temp_log_dir / f"screenshot_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"
    assert log_file.exists()
    content = log_file.read_text(encoding='utf-8')
    assert '截图开始' in content
    assert 'task_001' in content
    assert '截图完成' in content
    assert '/tmp/test.png' in content
    assert '150' in content


def test_step_logger_recognition(temp_log_dir):
    """测试识别环节日志记录"""
    logger = StepLogger(temp_log_dir)
    logger.recognition_start('/tmp/test.png', 'task_002')
    logger.recognition_done(200, score=4, success=True)
    logger.recognition_done(300, score=0, success=False, error='识别失败')

    log_file = temp_log_dir / f"recognition_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"
    assert log_file.exists()
    content = log_file.read_text(encoding='utf-8')
    assert '识别开始' in content
    assert '识别完成' in content
    assert 'score=4' in content
    assert '识别失败' in content


def test_step_logger_scoring(temp_log_dir):
    """测试打分环节日志记录"""
    logger = StepLogger(temp_log_dir)
    logger.scoring_start(5, 'task_003')
    logger.scoring_done(success=True)
    logger.scoring_done(success=False, error='点击失败')

    log_file = temp_log_dir / f"scoring_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"
    assert log_file.exists()
    content = log_file.read_text(encoding='utf-8')
    assert '打分开始' in content
    assert 'score=5' in content
    assert '打分完成' in content
    assert '打分失败' in content
    assert 'error=点击失败' in content


def test_step_logger_reuses_logger(temp_log_dir):
    """测试同一环节复用 logger 实例"""
    logger = StepLogger(temp_log_dir)
    logger.screenshot('message1')
    logger.screenshot('message2')

    log_file = temp_log_dir / f"screenshot_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"
    content = log_file.read_text(encoding='utf-8')
    assert content.count('message1') == 1
    assert content.count('message2') == 1


def test_step_logger_custom_log(temp_log_dir):
    """测试自定义日志记录"""
    logger = StepLogger(temp_log_dir)
    logger.screenshot('自定义消息', key1='val1', key2=42)

    log_file = temp_log_dir / f"screenshot_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"
    content = log_file.read_text(encoding='utf-8')
    assert '自定义消息' in content
    assert 'key1=val1' in content
    assert 'key2=42' in content
