"""确认步骤"""
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult
from src.core.automation import Automation


class ConfirmStep(BaseStep):
    name = '确认'
    description = '点击确认按钮'

    def execute(self, context: StepContext) -> StepResult:
        config = context.config
        automation = Automation(config)
        automation.click_confirm()
        return StepResult(success=True)
