"""
Pytest 全局 fixtures 配置文件

此文件定义了所有测试模块共享的 fixture，包括：
- 测试用 Flask 应用客户端
- Mock 数据库连接
- Mock 日志记录器
- 临时配置文件
- 工作流引擎实例
- Mock LLM 客户端
- Mock 屏幕捕获与自动化
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope='session')
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture(scope='session')
def sample_config():
    """返回测试用的配置字典"""
    return {
        'automation': {'simulate_click': True},
        'http_server': {'host': '127.0.0.1', 'port': 8081},
        'llm': {
            'provider': 'dashscope',
            'api_key': 'test-api-key',
            'model': 'test-model',
            'base_url': 'https://test.example.com/v1',
            'timeout': 5,
            'max_retries': 0,
            'prompt_template': '请评分0-6分，只返回数字'
        },
        'mysql': {
            'host': '',
            'port': 3306,
            'database': 'test_grading_app',
            'user': 'test_user',
            'password': 'test_password',
            'charset': 'utf8mb4'
        },
        'paths': {
            'logs': './test_logs',
            'screenshots': './test_screenshots'
        },
        'region': {
            'capture': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100},
            'clear_score': {'enabled': True, 'x': 10, 'y': 10},
            'confirm_button': {'x': 50, 'y': 50},
            'score_buttons': [
                {'score': i, 'x': i * 10, 'y': 100} for i in range(7)
            ]
        },
        'window': {'auto_open_browser': False}
    }


@pytest.fixture(scope='session')
def sample_workflow_config():
    """返回测试用的工作流配置字典"""
    return {
        'workflow': {
            'steps': [
                {
                    'id': 'screenshot',
                    'type': 'ScreenshotStep',
                    'enabled': True,
                    'delay': 0,
                    'params': {'region': 'capture'}
                },
                {
                    'id': 'evaluate',
                    'type': 'VLMEvalStep',
                    'enabled': True,
                    'delay': 0,
                    'params': {}
                },
                {
                    'id': 'clear_score',
                    'type': 'ClearScoreStep',
                    'enabled': True,
                    'delay': 0,
                    'params': {}
                },
                {
                    'id': 'click_score',
                    'type': 'ClickScoreStep',
                    'enabled': True,
                    'delay': 0,
                    'params': {}
                },
                {
                    'id': 'confirm',
                    'type': 'ConfirmStep',
                    'enabled': True,
                    'delay': 0,
                    'params': {}
                }
            ]
        }
    }


@pytest.fixture
def mock_logger():
    """返回一个 Mock 日志记录器"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def mock_db():
    """返回一个 Mock 数据库连接，模拟 pymysql cursor 行为"""
    db = MagicMock()

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 1
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = {'total': 0}
    # 确保 context manager 返回自身，避免 MagicMock 默认返回新对象
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_conn)
    cm.__exit__ = MagicMock(return_value=False)
    db.connection.return_value = cm

    db.test_connection.return_value = True
    return db


@pytest.fixture
def mock_repository(mock_db):
    """返回一个 Mock GradingRepository，方法行为可直接配置"""
    from src.db.repositories import GradingRepository
    repo = GradingRepository(mock_db)
    return repo


@pytest.fixture
def mock_llm_client():
    """返回一个 Mock LLM 客户端"""
    client = MagicMock()
    client.evaluate.return_value = {
        'success': True,
        'score': 5,
        'raw_response': '5',
        'error': ''
    }
    return client


@pytest.fixture
def mock_llm_client_factory(mock_llm_client):
    """Patch create_llm_client 返回 mock_llm_client"""
    with patch('src.llm.create_llm_client', return_value=mock_llm_client):
        yield mock_llm_client


@pytest.fixture
def mock_automation():
    """返回一个 Mock Automation 实例"""
    auto = MagicMock()
    auto.click_score_button.return_value = True
    auto.click_clear_score.return_value = True
    auto.click_confirm.return_value = None
    auto.click.return_value = None
    return auto


@pytest.fixture
def mock_screen_capture():
    """返回一个 Mock ScreenCapture 实例"""
    capture = MagicMock()
    capture.capture.return_value = ('/tmp/test_screenshot.png', MagicMock())
    capture.capture_full_screen.return_value = ('/tmp/test_fullscreen.png', MagicMock())
    return capture


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """创建临时配置文件并返回其路径"""
    config_dir = tmp_path / 'config'
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / 'config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    return config_path


@pytest.fixture
def temp_workflow_file(tmp_path, sample_workflow_config):
    """创建临时工作流配置文件并返回其路径"""
    config_dir = tmp_path / 'config'
    config_dir.mkdir(exist_ok=True)
    workflow_path = config_dir / 'workflow.json'
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(sample_workflow_config, f, ensure_ascii=False, indent=2)
    return workflow_path


@pytest.fixture
def temp_screenshot_dir(tmp_path):
    """创建临时截图目录"""
    screenshot_dir = tmp_path / 'test_screenshots'
    screenshot_dir.mkdir(exist_ok=True)
    return screenshot_dir


@pytest.fixture
def temp_log_dir(tmp_path):
    """创建临时日志目录"""
    log_dir = tmp_path / 'test_logs'
    log_dir.mkdir(exist_ok=True)
    return log_dir


@pytest.fixture
def app_client(tmp_path, sample_config, sample_workflow_config, monkeypatch):
    """
    创建 Flask 测试客户端

    使用临时配置文件，避免修改真实配置文件。
    所有数据库和外部依赖都被 Mock。
    """
    config_dir = tmp_path / 'config'
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / 'config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)

    workflow_path = config_dir / 'workflow.json'
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(sample_workflow_config, f, ensure_ascii=False, indent=2)

    screenshot_dir = tmp_path / 'test_screenshots'
    screenshot_dir.mkdir(exist_ok=True)

    sample_config['paths']['screenshots'] = str(screenshot_dir)
    sample_config['paths']['logs'] = str(tmp_path / 'test_logs')

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)

    with patch('src.app.project_root', tmp_path):
        import importlib
        import src.app
        importlib.reload(src.app)
        # reload 会重新执行模块顶层代码，导致 project_root 被覆盖，需要重新设置
        src.app.project_root = tmp_path
        from src.app import init_app
        app = init_app(sample_config)
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client


@pytest.fixture
def app_client_with_db(tmp_path, sample_config, sample_workflow_config):
    """
    创建带有 Mock 数据库 repository 的 Flask 测试客户端
    """
    config_dir = tmp_path / 'config'
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / 'config.json'
    sample_config['mysql']['host'] = 'mock_host'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)

    workflow_path = config_dir / 'workflow.json'
    with open(workflow_path, 'w', encoding='utf-8') as f:
        json.dump(sample_workflow_config, f, ensure_ascii=False, indent=2)

    screenshot_dir = tmp_path / 'test_screenshots'
    screenshot_dir.mkdir(exist_ok=True)
    sample_config['paths']['screenshots'] = str(screenshot_dir)
    sample_config['paths']['logs'] = str(tmp_path / 'test_logs')

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)

    with patch('src.app.project_root', tmp_path):
        with patch('src.app.Database') as MockDB:
            with patch('src.app.init_database'):
                with patch('src.app.GradingRepository') as MockRepo:
                    mock_db_instance = MagicMock()
                    mock_db_instance.test_connection.return_value = True
                    MockDB.return_value = mock_db_instance

                    mock_repo = MagicMock()
                    mock_repo.db = mock_db_instance
                    MockRepo.return_value = mock_repo

                    import importlib
                    import src.app
                    importlib.reload(src.app)
                    # reload 会重新执行模块顶层代码，需要重新设置 project_root 和补丁
                    src.app.project_root = tmp_path
                    src.app.Database = MockDB
                    src.app.init_database = lambda db: None
                    src.app.GradingRepository = MockRepo
                    from src.app import init_app
                    app = init_app(sample_config)
                    app.config['TESTING'] = True
                    with app.test_client() as client:
                        yield client, mock_repo


@pytest.fixture
def step_context(sample_config):
    """返回一个初始化的 StepContext"""
    from src.workflow.context import StepContext
    return StepContext(config=sample_config)


@pytest.fixture
def mock_step_result():
    """返回一个 Mock StepResult"""
    from src.workflow.context import StepResult
    return StepResult(success=True, data={'score': 5}, error='')


@pytest.fixture
def workflow_engine(sample_config, mock_logger):
    """返回一个未启动的 WorkflowEngine 实例"""
    from src.workflow.engine import WorkflowEngine
    return WorkflowEngine(sample_config, mock_logger)


@pytest.fixture
def workflow_engine_with_repo(sample_config, mock_logger, mock_repository):
    """返回一个带有 Mock repository 的 WorkflowEngine 实例"""
    from src.workflow.engine import WorkflowEngine
    engine = WorkflowEngine(sample_config, mock_logger, mock_repository)
    return engine
