"""条件分支步骤"""
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult
from src.workflow.expression import evaluate_expression


class ConditionStep(BaseStep):
    name = '条件分支'
    description = '根据表达式结果选择分支'

    def execute(self, context: StepContext) -> StepResult:
        result = self.evaluate(context)
        return StepResult(success=True, data={'branch_result': result})

    def evaluate(self, context: StepContext) -> bool:
        expression = self.params.get('expression', '')
        return evaluate_expression(expression, context.shared)
