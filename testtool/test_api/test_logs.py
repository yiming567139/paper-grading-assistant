"""测试日志与统计 API 端点"""
from unittest.mock import patch, MagicMock


def test_get_statistics_with_db(app_client_with_db):
    """测试获取统计数据（有数据库）"""
    client, mock_repo = app_client_with_db
    mock_repo.get_statistics.return_value = [
        {'date': '2026-05-28', 'total': 10, 'success': 8}
    ]

    response = client.get('/api/v1/statistics?start_date=2026-05-01&end_date=2026-05-31')
    assert response.status_code == 200
    data = response.get_json()
    assert data['data'][0]['total'] == 10
    assert data['data'][0]['success'] == 8
    mock_repo.get_statistics.assert_called_once_with('2026-05-01', '2026-05-31')


def test_get_statistics_no_db(app_client):
    """测试获取统计数据（无数据库）"""
    response = app_client.get('/api/v1/statistics')
    assert response.status_code == 503
    data = response.get_json()
    assert 'error' in data


def test_correction_logs_with_db(app_client_with_db):
    """测试兼容日志接口（有数据库）"""
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (
        1,
        [
            {
                'created_at': '2026-05-28 10:00:00',
                'screenshot_path': '/tmp/test.png',
                'score': 5,
                'status': 'success',
                'error_message': '',
                'vlm_response': '5'
            }
        ]
    )

    response = client.get('/api/v1/correction/logs')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['data']) == 1
    assert data['data'][0]['score'] == 5
    assert data['data'][0]['status'] == '成功'


def test_correction_logs_no_db(app_client):
    """测试兼容日志接口（无数据库）"""
    response = app_client.get('/api/v1/correction/logs')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data'] == []
    assert data['total'] == 0


def test_get_vlm_logs_with_db(app_client_with_db):
    """测试 VLM 日志接口（有数据库）"""
    client, mock_repo = app_client_with_db
    with patch('src.db.repositories.VlmCallLogRepository') as MockVlmRepo:
        mock_vlm = MagicMock()
        mock_vlm.get_logs.return_value = (1, [{'id': 1, 'provider': 'dashscope'}])
        MockVlmRepo.return_value = mock_vlm

        response = client.get('/api/v1/vlm-logs')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 1
        assert len(data['data']) == 1


def test_get_vlm_logs_no_db(app_client):
    """测试 VLM 日志接口（无数据库）"""
    response = app_client.get('/api/v1/vlm-logs')
    assert response.status_code == 503
    data = response.get_json()
    assert 'error' in data


def test_records_passes_consistent_param(app_client_with_db):
    """/records?consistent=0 应把 0 透传给 get_records"""
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (0, [])
    resp = client.get('/api/v1/records?consistent=0')
    assert resp.status_code == 200
    assert mock_repo.get_records.call_args.kwargs.get('consistent') == 0


def test_records_ignores_invalid_consistent(app_client_with_db):
    """非法 consistent 值应被忽略（传 None）"""
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (0, [])
    for bad in ('foo', '2', 'true', ''):
        mock_repo.get_records.reset_mock()
        mock_repo.get_records.return_value = (0, [])
        resp = client.get(f'/api/v1/records?consistent={bad}')
        assert resp.status_code == 200
        assert mock_repo.get_records.call_args.kwargs.get('consistent') is None


def test_correction_logs_includes_dual_fields(app_client_with_db):
    """/correction/logs 映射应包含双评字段"""
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (1, [{
        'created_at': '2026-06-30 10:00:00', 'screenshot_path': '/m.png',
        'screenshot_human_path': '/h.png', 'score': 5, 'score_secondary': 4,
        'status': 'success', 'error_message': '', 'vlm_response': '5',
        'vlm_response_secondary': '4', 'vlm_model': 'mA', 'vlm_model_secondary': 'mB',
        'grading_mode': 'dual', 'score_consistent': 0,
    }])
    resp = client.get('/api/v1/correction/logs')
    data = resp.get_json()['data'][0]
    assert data['score_secondary'] == 4
    assert data['vlm_model_secondary'] == 'mB'
    assert data['grading_mode'] == 'dual'
    assert data['score_consistent'] == 0
    assert data['screenshot_human'] == '/h.png'
    assert data['vlm_model'] == 'mA'


def test_correction_logs_passes_consistent_param(app_client_with_db):
    """/correction/logs?consistent=0 应把 0 透传给 get_records"""
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (0, [])
    resp = client.get('/api/v1/correction/logs?consistent=0')
    assert resp.status_code == 200
    assert mock_repo.get_records.call_args.kwargs.get('consistent') == 0


def test_correction_logs_ignores_invalid_consistent(app_client_with_db):
    """/correction/logs 非法 consistent 值应被忽略（传 None）"""
    client, mock_repo = app_client_with_db
    for bad in ('foo', '2', ''):
        mock_repo.get_records.reset_mock()
        mock_repo.get_records.return_value = (0, [])
        resp = client.get(f'/api/v1/correction/logs?consistent={bad}')
        assert resp.status_code == 200
        assert mock_repo.get_records.call_args.kwargs.get('consistent') is None


def test_records_formats_created_at(app_client_with_db):
    """/records 的 created_at 应格式化为 年-月-日 时:分:秒"""
    from datetime import datetime
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (1, [{'id': 1, 'created_at': datetime(2026, 7, 1, 9, 7, 5)}])
    resp = client.get('/api/v1/records')
    data = resp.get_json()['data'][0]
    assert data['created_at'] == '2026-07-01 09:07:05'


def test_correction_logs_formats_time(app_client_with_db):
    """/correction/logs 的 time 应格式化为 年-月-日 时:分:秒"""
    from datetime import datetime
    client, mock_repo = app_client_with_db
    mock_repo.get_records.return_value = (1, [{'created_at': datetime(2026, 7, 1, 9, 7, 5), 'status': 'success'}])
    resp = client.get('/api/v1/correction/logs')
    data = resp.get_json()['data'][0]
    assert data['time'] == '2026-07-01 09:07:05'
