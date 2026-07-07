"""测试 WorkflowEngine 核心方法"""
from unittest.mock import patch, MagicMock
import time


def test_engine_start_stop(workflow_engine_with_repo):
    """测试启动和停止工作流引擎"""
    engine = workflow_engine_with_repo
    assert not engine.is_running

    with patch.object(engine, '_execute_workflow'):
        with patch.object(engine, 'load_workflow'):
            with patch.object(engine.repository, 'create_batch', return_value=1):
                with patch.object(engine.repository, 'finish_batch'):
                    # 使用线程启动，避免阻塞；batch_limit=0 表示无限循环，直到 stop
                    import threading
                    t = threading.Thread(target=engine.start, args=(0,))
                    t.start()
                    import time
                    time.sleep(0.1)
                    assert engine.is_running
                    engine.stop()
                    t.join(timeout=1)
                    assert not engine.is_running


def test_engine_pause_resume(workflow_engine_with_repo):
    """测试暂停和恢复工作流引擎"""
    engine = workflow_engine_with_repo
    assert not engine.is_paused

    engine.pause()
    assert engine.is_paused

    engine.resume()
    assert not engine.is_paused


def test_engine_is_running_property(workflow_engine):
    """测试 is_running 属性状态变化"""
    engine = workflow_engine
    assert engine.is_running is False
    engine._running = True
    engine._stop_event.clear()
    assert engine.is_running is True
    engine._stop_event.set()
    assert engine.is_running is False


def test_engine_get_status(workflow_engine):
    """测试获取引擎状态"""
    engine = workflow_engine
    status = engine.get_status()
    assert 'is_running' in status
    assert 'is_paused' in status
    assert 'current_step' in status
    assert 'batch_id' in status
    assert status['is_running'] is False


def test_engine_stop_sets_event(workflow_engine):
    """测试 stop 方法设置停止事件"""
    engine = workflow_engine
    engine._running = True
    engine._stop_event.clear()
    assert engine.is_running is True
    engine.stop()
    assert engine.is_running is False
    assert engine._stop_event.is_set()


def test_engine_start_creates_batch(workflow_engine_with_repo):
    """测试 start 方法创建批次"""
    engine = workflow_engine_with_repo
    with patch.object(engine, 'load_workflow'):
        with patch.object(engine, '_execute_workflow'):
            with patch.object(engine.repository, 'create_batch', return_value=42) as mock_create:
                with patch.object(engine.repository, 'finish_batch'):
                    import threading
                    t = threading.Thread(target=engine.start, args=(0,))
                    t.start()
                    import time
                    time.sleep(0.1)
                    engine.stop()
                    t.join(timeout=1)
                    mock_create.assert_called_once_with(0)
def test_engine_status_includes_batch_and_completed(workflow_engine_with_repo):
    """测试 get_status 包含 batch_limit 和 completed_count"""
    engine = workflow_engine_with_repo
    status = engine.get_status()
    assert 'batch_limit' in status
    assert 'completed_count' in status
    assert status['batch_limit'] == 0
    assert status['completed_count'] == 0


def test_engine_start_sets_batch_limit_and_completed_count(workflow_engine_with_repo):
    """测试启动后 batch_limit 和 completed_count 被正确设置"""
    engine = workflow_engine_with_repo
    def slow_execute(*a, **k):
        time.sleep(0.5)

    with patch.object(engine, '_execute_workflow', side_effect=slow_execute):
        with patch.object(engine, 'load_workflow'):
            with patch.object(engine.repository, 'create_batch', return_value=1):
                with patch.object(engine.repository, 'finish_batch'):
                    import threading
                    t = threading.Thread(target=engine.start, args=(3,))
                    t.start()
                    time.sleep(0.1)
                    assert engine.batch_limit == 3
                    assert engine.completed_count == 0
                    engine.stop()
                    t.join(timeout=1)


def test_get_status_includes_dual_grading(sample_config, mock_logger):
    """单评配置下 dual_grading 为 False"""
    from src.workflow.engine import WorkflowEngine
    engine = WorkflowEngine(sample_config, mock_logger)
    status = engine.get_status()
    assert status['dual_grading'] is False
    assert status['primary_model'] == sample_config['llm']['model']
    assert status['secondary_model'] == ''


def test_get_status_dual_enabled(sample_config, mock_logger):
    """配置副模型后 dual_grading 为 True 且带副模型名"""
    from src.workflow.engine import WorkflowEngine
    cfg = dict(sample_config)
    cfg['llm_secondary'] = {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'mB'}
    engine = WorkflowEngine(cfg, mock_logger)
    status = engine.get_status()
    assert status['dual_grading'] is True
    assert status['secondary_model'] == 'mB'
