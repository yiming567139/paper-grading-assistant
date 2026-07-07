"""测试条件表达式安全求值模块"""
import pytest
from src.workflow.expression import evaluate_expression


class TestEvaluateExpression:
    """测试 evaluate_expression 函数"""

    def test_empty_expression_returns_true(self):
        """空表达式应返回 True"""
        assert evaluate_expression('', {}) is True

    def test_simple_comparison_gt(self):
        """测试大于比较"""
        assert evaluate_expression('score > 0', {'score': 5}) is True
        assert evaluate_expression('score > 10', {'score': 5}) is False

    def test_simple_comparison_lt(self):
        """测试小于比较"""
        assert evaluate_expression('score < 10', {'score': 5}) is True
        assert evaluate_expression('score < 0', {'score': 5}) is False

    def test_comparison_gte_lte(self):
        """测试大于等于和小于等于"""
        assert evaluate_expression('score >= 5', {'score': 5}) is True
        assert evaluate_expression('score <= 5', {'score': 5}) is True

    def test_equality_comparison(self):
        """测试等于和不等于"""
        assert evaluate_expression('score == 6', {'score': 6}) is True
        assert evaluate_expression('score == 6', {'score': 5}) is False
        assert evaluate_expression('score != 6', {'score': 5}) is True
        assert evaluate_expression('score != 6', {'score': 6}) is False

    def test_in_operator(self):
        """测试 in 操作符"""
        assert evaluate_expression('score in [1, 2, 3]', {'score': 2}) is True
        assert evaluate_expression('score in [1, 2, 3]', {'score': 5}) is False

    def test_not_in_operator(self):
        """测试 not in 操作符"""
        assert evaluate_expression('score not in [1, 2, 3]', {'score': 5}) is True
        assert evaluate_expression('score not in [1, 2, 3]', {'score': 2}) is False

    def test_boolean_and(self):
        """测试 and 布尔运算"""
        assert evaluate_expression('score > 0 and score < 10', {'score': 5}) is True
        assert evaluate_expression('score > 0 and score < 3', {'score': 5}) is False

    def test_boolean_or(self):
        """测试 or 布尔运算"""
        assert evaluate_expression('score == 1 or score == 5', {'score': 5}) is True
        assert evaluate_expression('score == 1 or score == 2', {'score': 5}) is False

    def test_unary_not(self):
        """测试 not 运算"""
        assert evaluate_expression('not score == 5', {'score': 3}) is True
        assert evaluate_expression('not score == 5', {'score': 5}) is False

    def test_complex_expression(self):
        """测试复杂组合表达式"""
        context = {'score': 5, 'success': True}
        assert evaluate_expression('score > 0 and success == True', context) is True
        assert evaluate_expression('score > 10 or success == False', context) is False

    def test_chained_comparison(self):
        """测试链式比较"""
        assert evaluate_expression('score > 1 and score < 10', {'score': 5}) is True

    def test_disallowed_variable(self):
        """测试不允许的变量名应抛出异常并返回 False"""
        assert evaluate_expression('dangerous_var > 0', {'dangerous_var': 5}) is False

    def test_invalid_expression_returns_false(self):
        """测试无效表达式返回 False"""
        assert evaluate_expression('score @#$ 5', {'score': 5}) is False

    def test_missing_variable_defaults_to_zero(self):
        """测试缺失变量默认返回 0"""
        assert evaluate_expression('score > 0', {}) is False
        assert evaluate_expression('score == 0', {}) is True

    def test_allowed_names_score(self):
        """测试 score 变量"""
        assert evaluate_expression('score == 100', {'score': 100}) is True

    def test_allowed_names_success(self):
        """测试 success 变量"""
        assert evaluate_expression('success == True', {'success': True}) is True

    def test_allowed_names_screenshot_size(self):
        """测试 screenshot_size 变量"""
        assert evaluate_expression('screenshot_size > 0', {'screenshot_size': 1024}) is True

    def test_function_call_not_allowed(self):
        """测试函数调用不被允许（返回 False）"""
        assert evaluate_expression('__import__("os").system("ls")', {}) is False

    def test_attribute_access_not_allowed(self):
        """测试属性访问不被允许"""
        assert evaluate_expression('score.__class__', {'score': 5}) is False

    def test_literal_values(self):
        """测试字面量值"""
        assert evaluate_expression('5 > 3', {}) is True
        assert evaluate_expression('"a" == "a"', {}) is True

    def test_success_with_boolean_true(self):
        """测试 success == True"""
        assert evaluate_expression('success == True', {'success': True}) is True
        assert evaluate_expression('success == True', {'success': False}) is False

    def test_not_in_with_strings(self):
        """测试字符串 not in"""
        assert evaluate_expression('score not in [1, 2]', {'score': 3}) is True
