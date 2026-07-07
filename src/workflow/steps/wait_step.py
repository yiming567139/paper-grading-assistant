"""等待步骤"""
import time
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult


class WaitStep(BaseStep):
    name = '等待'
    description = '等待指定秒数'

    def execute(self, context: StepContext) -> StepResult:
        duration = self.params.get('duration', 1.0)
        time.sleep(duration)
        return StepResult(success=True)
