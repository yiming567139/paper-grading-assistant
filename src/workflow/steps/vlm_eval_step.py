"""VLM 评分步骤（支持主+副双模型并发）"""
import logging
from concurrent.futures import ThreadPoolExecutor
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult
from src.workflow.dual_grading import is_dual_enabled
from src.llm import create_llm_client

logger = logging.getLogger('GradingApp')

DEFAULT_PROMPT = '请评分0-6分，只返回数字'


class VLMEvalStep(BaseStep):
    name = 'VLM评分'
    description = '调用大模型识别并评分（支持双评）'

    def __init__(self, step_id: str, params: dict = None):
        super().__init__(step_id, params)
        self._clients = {}
        self._signatures = {}

    def _get_client(self, role: str, cfg: dict):
        sig = (cfg.get('provider'), cfg.get('api_key'), cfg.get('model'), cfg.get('base_url'))
        if self._clients.get(role) is None or self._signatures.get(role) != sig:
            self._clients[role] = create_llm_client(cfg)
            self._signatures[role] = sig
        return self._clients[role]

    def _apply_mock_result(self, context: StepContext, config: dict) -> StepResult | None:
        """如果当前步骤启用了模拟结果，直接写入上下文并返回结果，否则返回 None。"""
        mock_cfg = self.params.get('mock_result', {})
        if not mock_cfg.get('enabled'):
            return None

        primary_mock = mock_cfg.get('primary', {})
        primary_score = int(primary_mock.get('score') or 0)
        primary_explanation = primary_mock.get('explanation') or 'mock result'

        context.set('score', primary_score)
        context.set('vlm_response', primary_explanation)
        context.set('vlm_model', 'mock')

        if not is_dual_enabled(config):
            context.set('grading_mode', 'single')
            logger.info(f'单评模拟结果: score={primary_score}')
            return StepResult(
                success=True,
                data={'score': primary_score, 'raw_response': primary_explanation},
                error=''
            )

        secondary_mock = mock_cfg.get('secondary', {})
        secondary_score = int(secondary_mock.get('score') or 0)
        secondary_explanation = secondary_mock.get('explanation') or 'mock result'

        context.set('grading_mode', 'dual')
        context.set('vlm_model_secondary', 'mock')
        context.set('score_secondary', secondary_score)
        context.set('vlm_response_secondary', secondary_explanation)
        context.set('score_consistent', 1 if primary_score == secondary_score else 0)

        logger.info(
            f'双评模拟结果: 主={primary_score}, 副={secondary_score}, '
            f'一致={context.get("score_consistent")}'
        )
        return StepResult(
            success=True,
            data={'score': primary_score, 'raw_response': primary_explanation},
            error=''
        )

    def execute(self, context: StepContext) -> StepResult:
        config = context.config
        screenshot_path = context.get('screenshot_path')
        if not screenshot_path:
            return StepResult(success=False, error='没有截图路径')

        mock_result = self._apply_mock_result(context, config)
        if mock_result is not None:
            return mock_result

        primary_cfg = config.get('llm', {})
        primary_prompt = primary_cfg.get('prompt_template', DEFAULT_PROMPT)
        primary_client = self._get_client('primary', primary_cfg)

        if not is_dual_enabled(config):
            context.set('grading_mode', 'single')
            result = primary_client.evaluate(screenshot_path, primary_prompt)
            if result['success']:
                context.set('score', result['score'])
                context.set('vlm_response', result['raw_response'])
                context.set('vlm_model', primary_cfg.get('model', ''))
                logger.info(f'单评结果: score={result["score"]}')
            else:
                logger.error(f'单评失败: {result.get("error")}')
            return StepResult(
                success=result['success'],
                data={'score': result.get('score', 0), 'raw_response': result.get('raw_response', '')},
                error=result.get('error', '')
            )

        # 双评模式
        secondary_cfg = config.get('llm_secondary', {})
        secondary_prompt = secondary_cfg.get('prompt_template', primary_prompt)
        secondary_client = self._get_client('secondary', secondary_cfg)
        context.set('grading_mode', 'dual')
        context.set('vlm_model_secondary', secondary_cfg.get('model', ''))

        logger.info(f'双评: 主={primary_cfg.get("model")}, 副={secondary_cfg.get("model")}')
        with ThreadPoolExecutor(max_workers=2) as ex:
            fut_p = ex.submit(primary_client.evaluate, screenshot_path, primary_prompt)
            fut_s = ex.submit(secondary_client.evaluate, screenshot_path, secondary_prompt)
            primary_result = fut_p.result()
            try:
                secondary_result = fut_s.result()
            except Exception as e:
                logger.warning(f'副模型评分异常: {e}')
                secondary_result = {'success': False, 'score': 0, 'raw_response': '', 'error': str(e)}

        if primary_result['success']:
            context.set('score', primary_result['score'])
            context.set('vlm_response', primary_result['raw_response'])
            context.set('vlm_model', primary_cfg.get('model', ''))

        if secondary_result['success']:
            context.set('score_secondary', secondary_result['score'])
            context.set('vlm_response_secondary', secondary_result['raw_response'])
        else:
            context.set('score_secondary', None)
            context.set('vlm_response_secondary', secondary_result.get('error', ''))

        if (primary_result['success'] and secondary_result['success']
                and primary_result['score'] == secondary_result['score']):
            context.set('score_consistent', 1)
        else:
            context.set('score_consistent', 0)

        logger.info(f'双评结果: 主={primary_result.get("score")}, 副={secondary_result.get("score")}, '
                    f'一致={context.get("score_consistent")}')
        return StepResult(
            success=primary_result['success'],
            data={'score': primary_result.get('score', 0), 'raw_response': primary_result.get('raw_response', '')},
            error=primary_result.get('error', '')
        )
