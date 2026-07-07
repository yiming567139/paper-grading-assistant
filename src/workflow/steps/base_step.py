"""Step 抽象基类"""
from abc import ABC, abstractmethod
from src.workflow.context import StepContext, StepResult, ParamDef


class BaseStep(ABC):
    """工作流步骤基类"""

    name: str = ''
    description: str = ''

    def __init__(self, step_id: str, params: dict = None):
        self.step_id = step_id
        self.params = params or {}

    @abstractmethod
    def execute(self, context: StepContext) -> StepResult:
        pass

    @property
    def configurable_params(self) -> list[ParamDef]:
        return []
