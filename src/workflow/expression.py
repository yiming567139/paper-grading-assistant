"""条件表达式安全求值 - 基于 AST 解析，不使用 eval"""
import ast
import logging
import operator

COMPARE_OPS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}

ALLOWED_NAMES = {'score', 'success', 'screenshot_size'}


def evaluate_expression(expression: str, context: dict) -> bool:
    """
    安全求值条件表达式

    支持: score > 0, score == 6, score in [1, 2, 3], success == True
    不支持: 函数调用、属性访问、任意代码执行

    Args:
        expression: 条件表达式字符串
        context: 包含 score, success 等变量的字典

    Returns:
        bool: 表达式结果
    """
    if not expression:
        return True

    try:
        tree = ast.parse(expression, mode='eval')
        return bool(_eval_node(tree.body, context))
    except Exception as e:
        logging.getLogger('GradingApp').warning(f'条件表达式求值失败 "{expression}": {e}')
        return False


def _eval_node(node, context):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, context)

    # 字面量
    if isinstance(node, ast.Constant):
        return node.value

    # 数字 (Python 3.7 兼容)
    if isinstance(node, ast.Num):
        return node.n

    # 列表
    if isinstance(node, ast.List):
        return [_eval_node(elt, context) for elt in node.elts]

    # 变量名（仅允许白名单）
    if isinstance(node, ast.Name):
        if node.id not in ALLOWED_NAMES:
            raise ValueError(f'不允许的变量: {node.id}')
        return context.get(node.id, 0)

    # 一元运算 (not)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_node(node.operand, context)

    # 比较运算
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, context)
            op_func = COMPARE_OPS.get(type(op))
            if op_func is None:
                raise ValueError(f'不支持的操作符: {type(op).__name__}')
            if not op_func(left, right):
                return False
            left = right
        return True

    # 布尔运算 (and, or)
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, context) for v in node.values]
        op_func = BOOL_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f'不支持的布尔操作符: {type(node.op).__name__}')
        return op_func(values)

    raise ValueError(f'不支持的表达式类型: {type(node).__name__}')
