"""点击分数步骤"""
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult
from src.core.automation import Automation


class ClickScoreStep(BaseStep):
    name = '点击分数'
    description = '点击对应分数按钮'

    def execute(self, context: StepContext) -> StepResult:
        config = context.config
        score = context.get('score', 0)

        automation = Automation(config)
        success = automation.click_score_button(score)

        if not success:
            return StepResult(success=False, error=f'未找到分数 {score} 对应的按钮')

        return StepResult(success=True)
