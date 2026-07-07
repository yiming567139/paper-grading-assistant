"""LLM 客户端抽象基类"""
from abc import ABC, abstractmethod
import base64


class BaseLLMClient(ABC):
    """多模态大模型客户端基类"""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', '')
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 2)

    def _image_to_base64(self, image_path: str) -> str:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @abstractmethod
    def evaluate(self, image_path: str, prompt: str) -> dict:
        """
        评估截图并返回分数

        Returns:
            {
                'success': bool,
                'score': int,
                'raw_response': str,
                'error': str  # 失败时
            }
        """
        pass
