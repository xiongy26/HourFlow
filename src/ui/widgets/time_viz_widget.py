"""时间可视化组件 - 进度环卡片"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from src.utils.time_utils import calculate_work_progress, get_time_period
from src.core.config_manager import ConfigManager

ACCENT = "#4F5BD5"
MORNING_COLOR = "#F59E0B"
AFTERNOON_COLOR = "#3B82F6"
EVENING_COLOR = "#8B5CF6"
TEXT_MUTED = "#8A8F9C"
TEXT_SECONDARY = "#6B7280"
TEXT_PRIMARY = "#1F2430"
SURFACE_BG = "#F7F8FB"


class TimeVizWidget(QFrame):
    """时间进度可视化组件 - 进度环卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._progress = 0.0
        self._timer = QTimer()
        self._init_ui()
        self._connect_signals()
        self._update_progress()

    def _init_ui(self):
        """初始化UI"""
        self.setObjectName("viz_card")
        self.setFixedHeight(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 18, 20, 16)

        # 标题
        title = QLabel("今日进度")
        title.setObjectName("viz_title")
        layout.addWidget(title)

        # 进度环 + 百分比（水平排列）
        ring_layout = QHBoxLayout()
        ring_layout.setSpacing(12)
        ring_layout.setContentsMargins(0, 10, 0, 6)
        ring_layout.addStretch()

        # 自定义绘制区域
        self._ring_widget = ProgressRingWidget()
        ring_layout.addWidget(self._ring_widget)

        # 右侧数值
        value_layout = QVBoxLayout()
        value_layout.setSpacing(4)
        value_layout.addStretch()

        self._progress_label = QLabel("0%")
        self._progress_label.setObjectName("progress_percent")
        font = QFont()
        font.setPointSize(22)
        font.setWeight(QFont.Weight.Black)
        self._progress_label.setFont(font)
        value_layout.addWidget(self._progress_label)

        cap_label = QLabel("今日已过")
        cap_label.setObjectName("progress_caption")
        value_layout.addWidget(cap_label)

        value_layout.addStretch()
        ring_layout.addLayout(value_layout)
        ring_layout.addStretch()

        layout.addLayout(ring_layout)

        # 时间段 + 午休指示
        period_layout = QHBoxLayout()
        period_layout.setSpacing(8)

        self._period_label = QLabel()
        self._period_label.setObjectName("period_pill")
        period_layout.addWidget(self._period_label)

        period_layout.addStretch()

        self._lunch_label = QLabel()
        self._lunch_label.setObjectName("progress_caption")
        period_layout.addWidget(self._lunch_label)

        layout.addLayout(period_layout)

    def _connect_signals(self):
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(60000)

    def _update_progress(self):
        """更新进度"""
        work_start = self._config.get_work_start_time()
        work_end = self._config.get_work_end_time()
        lunch_enabled = self._config.is_lunch_break_enabled()
        lunch_start = self._config.get_lunch_break_start()
        lunch_end = self._config.get_lunch_break_end()

        self._progress = calculate_work_progress(
            work_start, work_end,
            lunch_enabled, lunch_start, lunch_end
        )

        self._progress_label.setText(f"{self._progress:.0f}%")
        self._ring_widget.set_progress(self._progress)

        period = get_time_period()
        period_names = {"morning": "上午", "afternoon": "下午", "evening": "傍晚"}
        period_text = period_names.get(period, "")

        period_colors = {
            "morning": ("#FFFBEB", "#D97706"),
            "afternoon": ("#EFF6FF", "#2563EB"),
            "evening": ("#F5F3FF", "#7C3AED"),
        }
        bg, fg = period_colors.get(period, ("#F3F4F6", "#6B7280"))
        self._period_label.setText(period_text)
        self._period_label.setStyleSheet(
            f"font-size: 12px; font-weight: 600; "
            f"color: {fg}; background: {bg}; "
            f"padding: 3px 10px; border-radius: 10px;"
        )

        if lunch_enabled:
            self._lunch_label.setText(f"午休 {lunch_start}–{lunch_end}")
        else:
            self._lunch_label.setText("无午休")

        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

    def get_progress(self) -> float:
        return self._progress

    def start(self):
        self._update_progress()
        if not self._timer.isActive():
            self._timer.start(60000)

    def stop(self):
        self._timer.stop()


class ProgressRingWidget(QWidget):
    """独立进度环绘制组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._ring_size = 80
        self.setFixedSize(self._ring_size, self._ring_size)

    def set_progress(self, value: float):
        self._progress = min(max(value, 0.0), 100.0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx = self._ring_size // 2
        cy = self._ring_size // 2
        radius = cx - 8
        pen_width = 8

        # 背景环
        bg_color = QColor("#ECEDF2")
        painter.setPen(QPen(bg_color, pen_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # 进度环
        if self._progress > 0:
            # 渐变色：从蓝到深蓝
            progress_color = QColor(ACCENT)
            painter.setPen(QPen(progress_color, pen_width))
            painter.setBrush(Qt.NoBrush)

            # 绘制弧（从12点钟方向顺时针）
            rect_x = cx - radius
            rect_y = cy - radius
            start_angle = 90 * 16  # 从顶部开始
            span_angle = int(-360 * self._progress / 100 * 16)
            painter.drawArc(rect_x, rect_y, radius * 2, radius * 2,
                           start_angle, span_angle)

        # 中心数字
        painter.setPen(QColor(TEXT_PRIMARY))
        font = QFont()
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Black)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._progress:.0f}%")
