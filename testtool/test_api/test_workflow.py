"""测试工作流 API 端点"""
from unittest.mock import patch


def test_workflow_start(app_client):
    """测试启动工作流"""
    with patch('src.app.threading.Thread') as MockThread:
        mock_thread = MockThread.return_value
        response = app_client.post('/api/v1/workflow/start',
                                   json={'batch_limit': 5})
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'started'
        assert data['batch_limit'] == 5
        MockThread.assert_called_once()
        mock_thread.start.assert_called_once()


def test_workflow_start_default_limit(app_client):
    """测试启动工作流（默认 batch_limit=0）"""
    with patch('src.app.threading.Thread') as MockThread:
        mock_thread = MockThread.return_value
        response = app_client.post('/api/v1/workflow/start', json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'started'
        assert data['batch_limit'] == 0
        MockThread.assert_called_once()
        mock_thread.start.assert_called_once()


def test_workflow_stop(app_client):
    """测试停止工作流"""
    response = app_client.post('/api/v1/workflow/stop')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'stopped'


def test_workflow_pause(app_client):
    """测试暂停工作流"""
    response = app_client.post('/api/v1/workflow/pause')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'paused'


def test_workflow_resume(app_client):
    """测试恢复工作流"""
    response = app_client.post('/api/v1/workflow/resume')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'resumed'


def test_workflow_status(app_client):
    """测试获取工作流状态"""
    response = app_client.get('/api/v1/workflow/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'is_running' in data
    assert 'is_paused' in data
    assert 'current_step' in data
    assert 'batch_id' in data
