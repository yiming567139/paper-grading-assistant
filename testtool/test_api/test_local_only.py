"""测试本地访问限制装饰器 @local_only"""
import pytest


class TestLocalOnly:
    """测试危险端点对远程访问返回 403，本地访问不被拒绝"""

    LOCAL_ENDPOINTS = [
        ('POST', '/api/v1/workflow/start'),
        ('POST', '/api/v1/workflow/stop'),
        ('POST', '/api/v1/workflow/pause'),
        ('POST', '/api/v1/workflow/resume'),
        ('GET', '/api/v1/config'),
        ('POST', '/api/v1/config'),
        ('GET', '/api/v1/workflow/config'),
        ('POST', '/api/v1/workflow/config'),
        ('POST', '/api/v1/calibration/move-mouse'),
        ('POST', '/api/v1/llm/test'),
    ]

    @pytest.mark.parametrize('method,endpoint', LOCAL_ENDPOINTS)
    def test_remote_access_denied(self, app_client, method, endpoint):
        """模拟远程 IP 访问应返回 403"""
        json_data = {}
        if endpoint == '/api/v1/workflow/start':
            json_data = {'batch_limit': 0}
        elif endpoint == '/api/v1/calibration/move-mouse':
            json_data = {'x': 100, 'y': 100}
        elif endpoint == '/api/v1/llm/test':
            json_data = {'provider': 'dashscope', 'api_key': 'test', 'model': 'test'}

        if method == 'POST':
            response = app_client.post(
                endpoint,
                json=json_data,
                environ_base={'REMOTE_ADDR': '192.168.1.100'}
            )
        else:
            response = app_client.get(
                endpoint,
                environ_base={'REMOTE_ADDR': '192.168.1.100'}
            )

        assert response.status_code == 403
        data = response.get_json()
        assert '仅限本地访问' in data['error']

    @pytest.mark.parametrize('method,endpoint', LOCAL_ENDPOINTS)
    def test_local_access_not_forbidden(self, app_client, method, endpoint):
        """本地默认访问不应返回 403（可能返回其他状态，但不允许是 403）"""
        json_data = {}
        if endpoint == '/api/v1/workflow/start':
            json_data = {'batch_limit': 0}
        elif endpoint == '/api/v1/calibration/move-mouse':
            json_data = {'x': 100, 'y': 100}
        elif endpoint == '/api/v1/llm/test':
            json_data = {'provider': 'dashscope', 'api_key': 'test', 'model': 'test'}

        if method == 'POST':
            response = app_client.post(endpoint, json=json_data)
        else:
            response = app_client.get(endpoint)

        assert response.status_code != 403

    def test_llm_evaluate_remote_denied(self, app_client):
        """LLM evaluate 文件上传端点远程访问应返回 403"""
        response = app_client.post(
            '/api/v1/llm/evaluate',
            environ_base={'REMOTE_ADDR': '192.168.1.100'}
        )
        assert response.status_code == 403
        data = response.get_json()
        assert '仅限本地访问' in data['error']

    def test_open_endpoints_remote_allowed(self, app_client):
        """只读端点远程访问不应被 403 拦截"""
        open_endpoints = [
            ('GET', '/api/v1'),
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/services/status'),
            ('GET', '/api/v1/workflow/status'),
        ]
        for method, endpoint in open_endpoints:
            if method == 'GET':
                response = app_client.get(
                    endpoint,
                    environ_base={'REMOTE_ADDR': '192.168.1.100'}
                )
            assert response.status_code != 403, f'{endpoint} 不应被本地限制拦截'
