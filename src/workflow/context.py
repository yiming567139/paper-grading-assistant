"""工作流上下文与结果类型"""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StepResult:
    """步骤执行结果"""
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ''


@dataclass
class StepContext:
    """步骤执行上下文 - 在步骤间传递数据"""
    config: dict = field(default_factory=dict)
    shared: dict = field(default_factory=dict)

    def set(self, key: str, value: Any):
        self.shared[key] = value

    def get(self, key: str, default=None):
        return self.shared.get(key, default)


@dataclass
class ParamDef:
    """参数定义（用于前端表单渲染）"""
    name: str
    label: str
    type: str  # 'string', 'number', 'boolean', 'select'
    default: Any = None
    options: list = field(default_factory=list)
    required: bool = False
