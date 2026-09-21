"""下班倒计时组件 - 卡片化设计"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont

from src.utils.time_utils import (
    calculate_time_remaining,
    format_countdown,
    get_current_time_string,
    is_workday,
    get_weekday_name,
    get_today_weekday,
)
from src.core.config_manager import ConfigManager

ACCENT = "#4F5BD5"
GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#EF4444"
TEXT_MUTED = "#8A8F9C"
TEXT_SECONDARY = "#6B7280"
TEXT_PRIMARY = "#1F2430"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#ECEDF2"
SURFACE_BG = "#F7F8FB"


class CountdownWidget(QFrame):
    """下班倒计时组件 - 卡片容器"""

    time_updated = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._timer = QTimer()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        self.setObjectName("countdown_card")
        self.setFixedHeight(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 18, 20, 16)

        # 顶部行：标题 + 当前时间
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        title = QLabel("下班倒计时")
        title.setObjectName("countdown_title")
        top_row.addWidget(title)
        top_row.addStretch()

        self._current_time_label = QLabel()
        self._current_time_label.setObjectName("current_time")
        top_row.addWidget(self._current_time_label)

        layout.addLayout(top_row)

        # 核心数字区
        countdown_layout = QHBoxLayout()
        countdown_layout.setSpacing(6)
        countdown_layout.setContentsMargins(0, 10, 0, 6)

        self._countdown_label = QLabel("00:00")
        self._countdown_label.setObjectName("countdown_time")
        font = QFont()
        font.setPointSize(38)
        font.setWeight(QFont.Weight.Black)
        font.setFamily("SF Mono, Consolas, Menlo, monospace")
        self._countdown_label.setFont(font)
        countdown_layout.addWidget(self._countdown_label)

        unit_layout = QVBoxLayout()
        unit_layout.setSpacing(2)
        unit_layout.addStretch()

        unit_label = QLabel("时:分")
        unit_label.setObjectName("countdown_unit")
        unit_layout.addWidget(unit_label)

        self._status_label = QLabel("工作中")
        self._status_label.setObjectName("status")
        unit_layout.addWidget(self._status_label)

        unit_layout.addStretch()
        countdown_layout.addLayout(unit_layout)
        countdown_layout.addStretch()

        layout.addLayout(countdown_layout)

        # 底部行：星期 + 工作日类型
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self._weekday_label = QLabel()
        self._weekday_label.setObjectName("weekday")
        bottom_row.addWidget(self._weekday_label)

        bottom_row.addStretch()

        # 工作时段说明
        work_start = self._config.get_work_start_time()
        work_end = self._config.get_work_end_time()
        shift_label = QLabel(f"班次  {work_start} – {work_end}")
        shift_label.setObjectName("progress_caption")
        shift_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        bottom_row.addWidget(shift_label)

        layout.addLayout(bottom_row)

    def _connect_signals(self):
        """连接信号"""
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

    def _update_time(self):
        """更新时间"""
        work_end_hour, work_end_minute = self._parse_work_time()

        lunch_enabled = self._config.is_lunch_break_enabled()
        lunch_start = self._config.get_lunch_break_start()
        lunch_end = self._config.get_lunch_break_end()

        remaining_seconds = calculate_time_remaining(
            work_end_hour, work_end_minute,
            lunch_enabled, lunch_start, lunch_end
        )
        countdown = format_countdown(remaining_seconds, show_seconds=False)

        current_time = get_current_time_string()
        self._countdown_label.setText(countdown)
        self._current_time_label.setText(current_time)

        weekday = get_today_weekday()
        weekday_name = get_weekday_name(weekday)
        work_days = self._config.get_work_days()
        is_work = is_workday(work_days)
        day_type = "工作日" if is_work else "休息日"
        self._weekday_label.setText(f"{weekday_name}  {day_type}")

        self._update_style(remaining_seconds, is_work)

        self.time_updated.emit(countdown, current_time)

    def _parse_work_time(self):
        """解析下班时间"""
        work_end = self._config.get_work_end_time()
        parts = work_end.split(":")
        return int(parts[0]), int(parts[1])

    def _update_style(self, remaining_seconds: int, is_work: bool):
        """根据剩余时间更新颜色和状态"""
        if remaining_seconds <= 0:
            if is_work:
                color = GREEN
                status_text = "已下班"
                bg = "#ECFDF5"
            else:
                color = TEXT_MUTED
                status_text = "休息日"
                bg = SURFACE_BG
        elif remaining_seconds < 1800:  # < 30 min
            color = RED
            status_text = "快下班了！"
            bg = "#FEF2F2"
        elif remaining_seconds < 3600:  # < 1 hour
            color = ORANGE
            status_text = "加油！"
            bg = "#FFFBEB"
        else:
            color = ACCENT
            status_text = "工作中"
            bg = "#EEF2FF"

        self._countdown_label.setStyleSheet(
            f"color: {color}; font-weight: 800;"
        )
        self._status_label.setText(status_text)
        self._status_label.setStyleSheet(
            f"color: {color}; background: {bg}; "
            f"font-weight: 600; font-size: 13px; "
            f"padding: 4px 10px; border-radius: 8px;"
        )

    def start(self):
        if not self._timer.isActive():
            self._timer.start(1000)

    def stop(self):
        self._timer.stop()
