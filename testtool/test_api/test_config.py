"""测试 /api/v1/config 端点"""
import json


class TestConfigApi:
    """测试配置 API"""

    def test_get_config_returns_current_config(self, app_client, sample_config):
        """GET /api/v1/config 应返回当前配置内容（敏感字段已脱敏）"""
        response = app_client.get('/api/v1/config')

        assert response.status_code == 200
        data = json.loads(response.data)

        # 期望：除敏感字段外与 sample_config 一致
        expected = json.loads(json.dumps(sample_config))
        expected['llm']['api_key'] = '***'
        expected['mysql']['password'] = '***'
        assert data == expected

    def test_post_config_updates_config_file(self, app_client, tmp_path):
        """POST /api/v1/config 应将新配置写入文件"""
        new_config = {
            'automation': {'simulate_click': False},
            'http_server': {'host': '0.0.0.0', 'port': 9999},
            'llm': {
                'provider': 'openai',
                'api_key': 'new-key',
                'model': 'gpt-4',
                'base_url': 'https://api.openai.com/v1',
                'timeout': 10,
                'max_retries': 3,
                'prompt_template': '新提示词'
            },
            'mysql': {
                'host': 'new_host',
                'port': 3307,
                'database': 'new_db',
                'user': 'new_user',
                'password': 'new_password',
                'charset': 'utf8mb4'
            },
            'paths': {
                'logs': './new_logs',
                'screenshots': './new_screenshots'
            },
            'region': {
                'capture': {'x1': 10, 'y1': 20, 'x2': 200, 'y2': 300},
                'clear_score': {'enabled': False, 'x': 0, 'y': 0},
                'confirm_button': {'x': 100, 'y': 200},
                'score_buttons': []
            },
            'window': {'auto_open_browser': True}
        }

        response = app_client.post(
            '/api/v1/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'saved'

        config_path = tmp_path / 'config' / 'config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        assert saved_config == new_config

    def test_post_config_returns_saved_status(self, app_client):
        """POST /api/v1/config 应返回 saved 状态"""
        new_config = {
            'automation': {'simulate_click': True},
            'http_server': {'host': '127.0.0.1', 'port': 8080},
            'llm': {
                'provider': 'dashscope',
                'api_key': 'test-key',
                'model': 'test-model',
                'base_url': '',
                'timeout': 5,
                'max_retries': 0,
                'prompt_template': '测试'
            },
            'mysql': {
                'host': '',
                'port': 3306,
                'database': '',
                'user': '',
                'password': '',
                'charset': 'utf8mb4'
            },
            'paths': {
                'logs': './logs',
                'screenshots': './screenshots'
            },
            'region': {
                'capture': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100},
                'clear_score': {'enabled': True, 'x': 0, 'y': 0},
                'confirm_button': {'x': 50, 'y': 50},
                'score_buttons': []
            },
            'window': {'auto_open_browser': False}
        }

        response = app_client.post(
            '/api/v1/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {'status': 'saved'}

    def test_config_roundtrip(self, app_client):
        """配置应能正确读写往返"""
        new_config = {
            'automation': {'simulate_click': False},
            'http_server': {'host': '192.168.1.1', 'port': 7777},
            'llm': {
                'provider': 'test-provider',
                'api_key': 'roundtrip-key',
                'model': 'roundtrip-model',
                'base_url': 'https://roundtrip.example.com',
                'timeout': 30,
                'max_retries': 5,
                'prompt_template': '往返测试'
            },
            'mysql': {
                'host': 'roundtrip_host',
                'port': 3309,
                'database': 'roundtrip_db',
                'user': 'roundtrip_user',
                'password': 'roundtrip_pass',
                'charset': 'utf8mb4'
            },
            'paths': {
                'logs': './roundtrip_logs',
                'screenshots': './roundtrip_screenshots'
            },
            'region': {
                'capture': {'x1': 1, 'y1': 2, 'x2': 3, 'y2': 4},
                'clear_score': {'enabled': True, 'x': 5, 'y': 6},
                'confirm_button': {'x': 7, 'y': 8},
                'score_buttons': [{'score': 0, 'x': 0, 'y': 0}]
            },
            'window': {'auto_open_browser': True}
        }

        post_response = app_client.post(
            '/api/v1/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        assert post_response.status_code == 200

        get_response = app_client.get('/api/v1/config')
        assert get_response.status_code == 200

        retrieved_config = json.loads(get_response.data)
        # GET 返回脱敏版本，敏感字段应为 ***
        expected = json.loads(json.dumps(new_config))
        expected['llm']['api_key'] = '***'
        expected['mysql']['password'] = '***'
        assert retrieved_config == expected


def test_post_config_allows_llm_secondary(app_client):
    """配置含 llm_secondary 顶级键时应保存成功"""
    payload = {
        'llm': {'provider': 'dashscope', 'api_key': 'k', 'model': 'm'},
        'llm_secondary': {'enabled': True, 'provider': 'deepseek', 'api_key': 'k2', 'model': 'm2'},
        'region': {'capture': {'x1': 0, 'y1': 0, 'x2': 10, 'y2': 10}},
    }
    resp = app_client.post('/api/v1/config', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'saved'


def test_post_config_preserves_masked_secrets(app_client):
    """保存时若敏感字段为脱敏值 '***'，应保留旧的真实值，不被覆盖"""
    # 先读取当前配置（其中 api_key/password 会被脱敏为 '***'）
    masked = app_client.get('/api/v1/config').get_json()
    assert masked['llm']['api_key'] == '***'
    real_key = 'test-api-key'  # sample_config 中的真实值

    # 原样回传（含 '***'），保存
    resp = app_client.post('/api/v1/config', json=masked)
    assert resp.status_code == 200

    # 再次读取仍脱敏，但直接读文件应为真实旧值而非 '***'
    import json as _json
    from src.app import project_root
    with open(project_root / 'config' / 'config.json', encoding='utf-8') as f:
        saved = _json.load(f)
    assert saved['llm']['api_key'] == real_key
    assert saved['mysql']['password'] != '***'


def test_post_config_updates_real_secret(app_client):
    """若敏感字段传入真实新值（非 '***'），应正常更新"""
    masked = app_client.get('/api/v1/config').get_json()
    masked['llm']['api_key'] = 'brand-new-key'
    resp = app_client.post('/api/v1/config', json=masked)
    assert resp.status_code == 200
    import json as _json
    from src.app import project_root
    with open(project_root / 'config' / 'config.json', encoding='utf-8') as f:
        saved = _json.load(f)
    assert saved['llm']['api_key'] == 'brand-new-key'
