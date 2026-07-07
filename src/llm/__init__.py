"""LLM 客户端工厂"""
from src.llm.dashscope_client import DashScopeClient
from src.llm.deepseek_client import DeepSeekClient


LLM_CLIENTS = {
    'dashscope': DashScopeClient,
    'deepseek': DeepSeekClient,
}


def create_llm_client(config: dict):
    provider = config.get('provider', 'dashscope')
    client_class = LLM_CLIENTS.get(provider)
    if not client_class:
        raise ValueError(f'Unknown LLM provider: {provider}')
    return client_class(config)
