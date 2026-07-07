"""清分步骤"""
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult
from src.core.automation import Automation


class ClearScoreStep(BaseStep):
    name = '清分'
    description = '点击清分按钮'

    def execute(self, context: StepContext) -> StepResult:
        config = context.config
        automation = Automation(config)
        automation.click_clear_score()
        return StepResult(success=True)
