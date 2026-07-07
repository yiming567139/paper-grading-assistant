"""测试校准相关 API 端点"""
from unittest.mock import patch, MagicMock


def test_calibration_screenshot(app_client):
    """测试校准截图接口"""
    with patch('src.core.screen_capture.ScreenCapture') as MockCapture:
        mock_instance = MagicMock()
        mock_instance.capture_full_screen.return_value = ('/tmp/test_screenshots/calib.png', MagicMock())
        MockCapture.return_value = mock_instance

        response = app_client.post('/api/v1/calibration/screenshot')
        assert response.status_code == 200
        data = response.get_json()
        assert data['filename'] == 'calib.png'
        assert data['url'] == '/api/v1/screenshots/calib.png'
        mock_instance.capture_full_screen.assert_called_once()


def test_calibration_screenshot_different_filename(app_client):
    """测试校准截图接口返回不同文件名"""
    with patch('src.core.screen_capture.ScreenCapture') as MockCapture:
        mock_instance = MagicMock()
        mock_instance.capture_full_screen.return_value = ('/tmp/test_screenshots/full_123.png', MagicMock())
        MockCapture.return_value = mock_instance

        response = app_client.post('/api/v1/calibration/screenshot')
        assert response.status_code == 200
        data = response.get_json()
        assert data['filename'] == 'full_123.png'
        assert data['url'] == '/api/v1/screenshots/full_123.png'


def test_calibration_screenshot_remote_denied(app_client):
    """测试校准截图接口拒绝远程访问"""
    response = app_client.post('/api/v1/calibration/screenshot',
                               environ_base={'REMOTE_ADDR': '192.168.1.100'})
    assert response.status_code == 403
    data = response.get_json()
    assert '仅限本地访问' in data['error']


def test_calibration_move_mouse_success(app_client):
    """测试鼠标移动接口成功"""
    with patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.size', return_value=(1920, 1080)):
        response = app_client.post('/api/v1/calibration/move-mouse',
                                   json={'x': 100, 'y': 200})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        mock_move.assert_called_once_with(100, 200, duration=0.3)


def test_calibration_move_mouse_missing_params(app_client):
    """测试鼠标移动接口缺少参数"""
    response = app_client.post('/api/v1/calibration/move-mouse', json={'x': 100})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '缺少 x 或 y 参数' in data['error']


def test_calibration_move_mouse_empty_body(app_client):
    """测试鼠标移动接口空请求体"""
    response = app_client.post('/api/v1/calibration/move-mouse', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '缺少 x 或 y 参数' in data['error']


def test_calibration_move_mouse_exception(app_client):
    """测试鼠标移动接口异常处理"""
    with patch('pyautogui.moveTo', side_effect=Exception('Mouse not found')), \
         patch('pyautogui.size', return_value=(1920, 1080)):
        response = app_client.post('/api/v1/calibration/move-mouse',
                                   json={'x': 50, 'y': 50})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Mouse not found' in data['error']


def test_calibration_move_mouse_remote_denied(app_client):
    """测试鼠标移动接口拒绝远程访问"""
    response = app_client.post('/api/v1/calibration/move-mouse',
                               json={'x': 100, 'y': 100},
                               environ_base={'REMOTE_ADDR': '192.168.1.100'})
    assert response.status_code == 403
    data = response.get_json()
    assert '仅限本地访问' in data['error']
