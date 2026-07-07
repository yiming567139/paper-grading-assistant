"""步骤注册表"""
from src.workflow.steps.screenshot_step import ScreenshotStep
from src.workflow.steps.vlm_eval_step import VLMEvalStep
from src.workflow.steps.clear_score_step import ClearScoreStep
from src.workflow.steps.click_score_step import ClickScoreStep
from src.workflow.steps.confirm_step import ConfirmStep
from src.workflow.steps.wait_step import WaitStep
from src.workflow.steps.condition_step import ConditionStep

STEP_REGISTRY = {
    'ScreenshotStep': ScreenshotStep,
    'VLMEvalStep': VLMEvalStep,
    'ClearScoreStep': ClearScoreStep,
    'ClickScoreStep': ClickScoreStep,
    'ConfirmStep': ConfirmStep,
    'WaitStep': WaitStep,
    'ConditionStep': ConditionStep,
}


def create_step(step_id: str, step_type: str, params: dict = None):
    step_class = STEP_REGISTRY.get(step_type)
    if not step_class:
        raise ValueError(f'Unknown step type: {step_type}')
    return step_class(step_id, params)
