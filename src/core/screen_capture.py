"""
屏幕截图模块

使用mss库进行屏幕区域截取，支持指定区域截图和全屏截图。
截图文件保存为PNG格式，按时间戳命名。

Dependencies:
    mss: 高速屏幕截图库

Author: AI助手
Version: 1.0.0
"""
import mss
import os
from pathlib import Path
from datetime import datetime


class ScreenCapture:
    """
    屏幕截图类

    使用mss库截取屏幕指定区域的图片。

    Attributes:
        config: 配置字典，包含paths.screenshots和region.capture等
        screenshot_dir: 截图保存目录路径
    """

    def __init__(self, config):
        self.config = config
        self.screenshot_dir = Path(config['paths']['screenshots'])
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, region=None):
        """
        截图

        Args:
            region: 区域配置 {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}

        Returns:
            tuple: (截图文件路径, 截图数据)
        """
        if region is None:
            region = self.config['region']['capture']

        with mss.mss() as sct:
            screenshot = sct.grab({
                'left': region['x1'],
                'top': region['y1'],
                'width': region['x2'] - region['x1'],
                'height': region['y2'] - region['y1']
            })

            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}.png"
            counter = 1
            while (self.screenshot_dir / filename).exists():
                filename = f"{timestamp}_{counter}.png"
                counter += 1
            filepath = self.screenshot_dir / filename

            # 保存图片
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))

            return str(filepath), screenshot

    def capture_full_screen(self):
        """截取全屏"""
        with mss.mss() as sct:
            screenshot = sct.monitors[1]  # 主显示器

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}.png"
            counter = 1
            while (self.screenshot_dir / filename).exists():
                filename = f"{timestamp}_{counter}.png"
                counter += 1
            filepath = self.screenshot_dir / filename

            img = sct.grab(screenshot)
            mss.tools.to_png(img.rgb, img.size, output=str(filepath))

            return str(filepath), img
