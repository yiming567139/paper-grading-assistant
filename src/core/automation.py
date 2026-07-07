"""
自动化控制模块

通过pyautogui控制鼠标和键盘操作，实现自动点击分数按钮等功能。
"""
import logging
import pyautogui
import time

logger = logging.getLogger('GradingApp')

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5


class Automation:

    def __init__(self, config):
        self.config = config

    def _is_simulate(self):
        return self.config.get('automation', {}).get('simulate_click', False)

    def click(self, x, y, button='left'):
        if self._is_simulate():
            logger.info(f'[模拟点击] x={x}, y={y}, button={button}')
            time.sleep(0.2)
            return

        logger.info(f'点击: x={x}, y={y}, button={button}')
        pyautogui.click(x, y, button=button)
        time.sleep(0.2)

    def double_click(self, x, y):
        if self._is_simulate():
            logger.info(f'[模拟双击] x={x}, y={y}')
            time.sleep(0.2)
            return
        logger.info(f'双击: x={x}, y={y}')
        pyautogui.doubleClick(x, y)
        time.sleep(0.2)

    def type_text(self, text):
        if self._is_simulate():
            logger.info(f'[模拟输入] text={text}')
            time.sleep(0.2)
            return
        logger.info(f'输入文本: {text}')
        pyautogui.write(text, interval=0.1)
        time.sleep(0.2)

    def press_key(self, key):
        if self._is_simulate():
            logger.info(f'[模拟按键] key={key}')
            time.sleep(0.2)
            return
        logger.info(f'按键: {key}')
        pyautogui.press(key)
        time.sleep(0.2)

    def click_clear_score(self):
        """点击清分按钮"""
        clear_score = self.config['region'].get('clear_score')
        if not clear_score or not clear_score.get('enabled'):
            logger.debug('清分按钮未配置或已禁用，跳过')
            return False
        self.click(clear_score['x'], clear_score['y'])
        return True

    def click_score_button(self, score):
        score_buttons = self.config['region']['score_buttons']

        try:
            score_int = int(score)
        except (ValueError, TypeError):
            logger.warning(f'无效的分数值: {score} (类型: {type(score).__name__})')
            return False

        for btn in score_buttons:
            if btn['score'] == score_int:
                self.click(btn['x'], btn['y'])
                return True

        logger.warning(f'未找到分数 {score} 对应的按钮')
        return False

    def click_next(self):
        next_btn = self.config['region'].get('next_button')
        if not next_btn:
            logger.warning('next_button 未配置')
            return
        self.click(next_btn['x'], next_btn['y'])

    def click_confirm(self):
        """点击确认打分"""
        confirm_btn = self.config['region'].get('confirm_button')
        if not confirm_btn:
            logger.warning('confirm_button 未配置')
            return
        self.click(confirm_btn['x'], confirm_btn['y'])

    def get_current_position(self):
        return pyautogui.position()
