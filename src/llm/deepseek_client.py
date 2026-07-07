"""DeepSeek API 客户端"""
import logging
import os
import time
import requests
import re
from src.llm.base_client import BaseLLMClient

logger = logging.getLogger('GradingApp')


class DeepSeekClient(BaseLLMClient):
    """DeepSeek 多模态 API 客户端"""

    def __init__(self, config: dict):
        super().__init__(config)
        if not self.base_url:
            self.base_url = 'https://api.deepseek.com/v1'

    def evaluate(self, image_path: str, prompt: str) -> dict:
        try:
            image_base64 = self._image_to_base64(image_path)

            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                        '.webp': 'image/webp', '.gif': 'image/gif', '.bmp': 'image/bmp'}
            mime_type = mime_map.get(ext, 'image/png')

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'image_url', 'image_url': {'url': f'data:{mime_type};base64,{image_base64}'}},
                            {'type': 'text', 'text': prompt}
                        ]
                    }
                ]
            }

            url = f'{self.base_url}/chat/completions'
            logger.info(f'DeepSeek 请求: model={self.model}, url={url}, image={image_path}, prompt="{prompt[:50]}..."')

            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            duration_ms = int((time.time() - start_time) * 1000)

            if not response.ok:
                try:
                    err_detail = response.json()
                except Exception:
                    err_detail = response.text
                logger.error(f'DeepSeek API 错误: HTTP {response.status_code}, 耗时={duration_ms}ms, 响应={err_detail}')
                return {
                    'success': False,
                    'score': 0,
                    'raw_response': '',
                    'error': f'HTTP {response.status_code}: {err_detail}'
                }

            result = response.json()
            raw_text = result['choices'][0]['message']['content']
            score = self._extract_score(raw_text)

            logger.info(f'DeepSeek 响应: score={score}, 耗时={duration_ms}ms, 原文="{raw_text[:200]}"')
            return {
                'success': True,
                'score': score,
                'raw_response': raw_text
            }

        except Exception as e:
            logger.exception(f'DeepSeek 调用异常: {e}')
            return {
                'success': False,
                'score': 0,
                'raw_response': '',
                'error': str(e)
            }

    def _extract_score(self, text: str) -> int:
        numbers = re.findall(r'(?<!\d)([0-6])(?!\d)', text.strip())
        if numbers:
            return int(numbers[0])
        return 0
