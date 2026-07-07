"""Mock 测试 LLM 客户端"""
from unittest.mock import patch, MagicMock


def test_dashscope_client_evaluate_success():
    """测试 DashScopeClient evaluate 成功场景"""
    with patch('src.llm.dashscope_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '分数是 5 分'}}]
        }
        mock_post.return_value = mock_response

        with patch('src.llm.dashscope_client.open', MagicMock()):
            with patch('src.llm.dashscope_client.os.path.splitext', return_value=('/tmp/test', '.png')):
                from src.llm.dashscope_client import DashScopeClient
                client = DashScopeClient({
                    'api_key': 'test-key',
                    'model': 'qwen-vl-plus',
                    'timeout': 5
                })
                with patch.object(client, '_image_to_base64', return_value='base64data'):
                    result = client.evaluate('/tmp/test.png', '请评分')

        assert result['success'] is True
        assert result['score'] == 5
        assert '分数是 5 分' in result['raw_response']


def test_dashscope_client_evaluate_http_error():
    """测试 DashScopeClient HTTP 错误"""
    with patch('src.llm.dashscope_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.json.return_value = {'error': 'rate limited'}
        mock_post.return_value = mock_response

        from src.llm.dashscope_client import DashScopeClient
        client = DashScopeClient({
            'api_key': 'test-key',
            'model': 'qwen-vl-plus',
            'timeout': 5
        })
        with patch.object(client, '_image_to_base64', return_value='base64data'):
            result = client.evaluate('/tmp/test.png', '请评分')

        assert result['success'] is False
        assert result['score'] == 0
        assert 'HTTP 429' in result['error']


def test_dashscope_client_extract_score():
    """测试 DashScopeClient _extract_score 提取分数"""
    from src.llm.dashscope_client import DashScopeClient
    client = DashScopeClient({'api_key': 'test', 'model': 'test'})

    assert client._extract_score('答案是 3') == 3
    assert client._extract_score('score: 6') == 6
    assert client._extract_score('没有分数') == 0


def test_deepseek_client_evaluate_success():
    """测试 DeepSeekClient evaluate 成功场景"""
    with patch('src.llm.deepseek_client.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '我认为是 4 分'}}]
        }
        mock_post.return_value = mock_response

        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient({
            'api_key': 'test-key',
            'model': 'deepseek-vl',
            'timeout': 5
        })
        with patch.object(client, '_image_to_base64', return_value='base64data'):
            result = client.evaluate('/tmp/test.png', '请评分')

        assert result['success'] is True
        assert result['score'] == 4


def test_deepseek_client_evaluate_exception():
    """测试 DeepSeekClient evaluate 异常处理"""
    with patch('src.llm.deepseek_client.requests.post', side_effect=Exception('Connection timeout')):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient({
            'api_key': 'test-key',
            'model': 'deepseek-vl',
            'timeout': 5
        })
        with patch.object(client, '_image_to_base64', return_value='base64data'):
            result = client.evaluate('/tmp/test.png', '请评分')

        assert result['success'] is False
        assert 'Connection timeout' in result['error']


def test_deepseek_client_extract_score():
    """测试 DeepSeekClient _extract_score 提取分数"""
    from src.llm.deepseek_client import DeepSeekClient
    client = DeepSeekClient({'api_key': 'test', 'model': 'test'})

    assert client._extract_score('结果是 2') == 2
    assert client._extract_score('5分') == 5
    assert client._extract_score('abc') == 0


def test_create_llm_client_factory():
    """测试 LLM 客户端工厂函数"""
    from src.llm import create_llm_client

    dashscope = create_llm_client({'provider': 'dashscope', 'api_key': 'k', 'model': 'm'})
    from src.llm.dashscope_client import DashScopeClient
    assert isinstance(dashscope, DashScopeClient)

    deepseek = create_llm_client({'provider': 'deepseek', 'api_key': 'k', 'model': 'm'})
    from src.llm.deepseek_client import DeepSeekClient
    assert isinstance(deepseek, DeepSeekClient)


def test_create_llm_client_unknown_provider():
    """测试工厂函数遇到未知 provider 抛出异常"""
    from src.llm import create_llm_client
    try:
        create_llm_client({'provider': 'unknown', 'api_key': 'k'})
        assert False, '应该抛出 ValueError'
    except ValueError as e:
        assert 'Unknown LLM provider' in str(e)
