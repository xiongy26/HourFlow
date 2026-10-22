"""今日计划组件 - 卡片化时间轴"""
from datetime import datetime
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from src.models.time_block import TimeBlock, BlockType
from src.core.task_manager import TaskManager
from src.core.config_manager import ConfigManager
from src.utils.time_utils import format_time_range, get_lunch_window

ACCENT = "#4F5BD5"
GREEN = "#22C55E"
ORANGE = "#F59E0B"
PURPLE = "#8B5CF6"
TEXT_MUTED = "#8A8F9C"
TEXT_SECONDARY = "#6B7280"
TEXT_PRIMARY = "#1F2430"
SURFACE_BG = "#F7F8FB"
CURRENT_BG = "#EEF2FF"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#ECEDF2"


class ScheduleWidget(QWidget):
    """今日计划时间轴组件"""

    add_task_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._config = ConfigManager()
        self._time_blocks: List[TimeBlock] = []
        self._init_ui()
        self._load_time_blocks()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 卡片容器
        card = QFrame()
        card.setObjectName("schedule_card")

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # ---- 卡片头部 ----
        header = QFrame()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #ECEDF2;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(8)

        title = QLabel("今日计划")
        title.setObjectName("schedule_title")
        font = QFont()
        font.setPointSize(15)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        header_layout.addWidget(title)

        # 统计标签
        self._block_count_label = QLabel("0 个时间块")
        self._block_count_label.setObjectName("schedule_subtitle")
        header_layout.addWidget(self._block_count_label)

        header_layout.addStretch()

        add_btn = QPushButton("+ 添加")
        add_btn.setObjectName("add_task_button")
        add_btn.clicked.connect(self.add_task_clicked.emit)
        header_layout.addWidget(add_btn)

        card_layout.addWidget(header)

        # ---- 滚动内容区 ----
        scroll = QScrollArea()
        scroll.setObjectName("schedule_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "#schedule_scroll { border: none; background: transparent; }"
        )

        self._timeline_container = QWidget()
        self._timeline_container.setStyleSheet("background: transparent;")
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setSpacing(8)
        self._timeline_layout.setContentsMargins(18, 14, 18, 14)

        scroll.setWidget(self._timeline_container)
        card_layout.addWidget(scroll, 1)

        layout.addWidget(card)

    def _load_time_blocks(self):
        """加载时间块"""
        blocks_data = self._task_manager.get_time_blocks()

        if blocks_data:
            self._time_blocks = [TimeBlock.from_dict(b) for b in blocks_data]
        else:
            self._regenerate_time_blocks()

        self._update_timeline()

    def _regenerate_time_blocks(self):
        """重新生成时间块"""
        from src.services.schedule_optimizer import ScheduleOptimizer

        tasks = self._task_manager.get_pending_tasks()
        work_start_str = self._config.get_work_start_time()
        work_end_str = self._config.get_work_end_time()

        start_hour, start_min = map(int, work_start_str.split(":"))
        end_hour, end_min = map(int, work_end_str.split(":"))

        now = datetime.now()
        work_start = now.replace(hour=start_hour, minute=start_min, second=0)
        work_end = now.replace(hour=end_hour, minute=end_min, second=0)

        self._time_blocks = ScheduleOptimizer.allocate_time_blocks(
            tasks, work_start, work_end,
            lunch=get_lunch_window(
                now, work_start, work_end,
                self._config.is_lunch_break_enabled(),
                self._config.get_lunch_break_start(),
                self._config.get_lunch_break_end()
            )
        )

        blocks_data = [b.to_dict() for b in self._time_blocks]
        self._task_manager.set_time_blocks(blocks_data)

    def _update_timeline(self):
        """更新时间轴显示"""
        while self._timeline_layout.count():
            item = self._timeline_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        now = datetime.now()
        count = len(self._time_blocks)
        self._block_count_label.setText(
            f"{count} 个时间块" if count else "暂无计划"
        )

        if not self._time_blocks:
            empty = QLabel("暂无计划，点击「+ 添加」创建第一个任务")
            empty.setObjectName("empty_state_label")
            empty.setAlignment(Qt.AlignHCenter)
            self._timeline_layout.addWidget(empty)
            return

        for block in self._time_blocks:
            block_widget = TimeBlockItem(block, now)
            self._timeline_layout.addWidget(block_widget)

        self._timeline_layout.addStretch()

    def refresh(self):
        self._load_time_blocks()


class TimeBlockItem(QFrame):
    """单条时间块卡片"""

    clicked = Signal(str)

    def __init__(self, block: TimeBlock, current_time: datetime, parent=None):
        super().__init__(parent)
        self._block = block
        self._current_time = current_time
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("time_block")
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 10, 14, 10)

        # 左侧色条（视觉指示器）
        dot = QFrame()
        dot.setFixedSize(4, 36)
        color_map = {
            BlockType.WORK: ACCENT,
            BlockType.BREAK: GREEN,
            BlockType.MEETING: ORANGE,
            BlockType.LUNCH: PURPLE,
        }
        dot_color = color_map.get(self._block.type, ACCENT)
        dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 2px;"
        )
        layout.addWidget(dot)

        # 时间标签
        time_str = format_time_range(self._block.start, self._block.end)
        time_label = QLabel(time_str)
        time_label.setObjectName("time_label")
        time_label.setStyleSheet(f"color: {dot_color}; font-weight: 700; font-size: 12px;")
        time_label.setFixedWidth(90)
        layout.addWidget(time_label)

        # 描述
        desc_label = QLabel(self._block.description or "未命名")
        desc_label.setObjectName("description_label")
        layout.addWidget(desc_label, 1)

        # 持续时长
        duration_label = QLabel(self._block.duration_formatted)
        duration_label.setObjectName("duration_label")
        layout.addWidget(duration_label)

        # 类型徽章
        type_map = {
            BlockType.WORK: ("工作", ACCENT, "#EEF2FF"),
            BlockType.BREAK: ("休息", GREEN, "#ECFDF5"),
            BlockType.MEETING: ("会议", ORANGE, "#FFFBEB"),
            BlockType.LUNCH: ("午休", PURPLE, "#F5F3FF"),
        }
        type_text, type_fg, type_bg = type_map.get(
            self._block.type, ("工作", ACCENT, "#EEF2FF")
        )
        badge = QLabel(type_text)
        badge.setObjectName("type_badge")
        badge.setStyleSheet(
            f"color: {type_fg}; background: {type_bg}; "
            f"font-weight: 700; font-size: 10px; padding: 2px 8px; border-radius: 6px;"
        )
        layout.addWidget(badge)

    def _apply_style(self):
        """根据当前时间块状态设置样式"""
        is_current = (
            self._current_time
            and self._block.start <= self._current_time <= self._block.end
        )
        if is_current:
            self.setStyleSheet(
                "#time_block { "
                "background: #EEF2FF; border: 1px solid #DDE3FB; "
                "border-radius: 10px; "
                "}"
            )
        else:
            self.setStyleSheet(
                "#time_block { "
                "background: #F7F8FB; border: 1px solid #ECEDF2; "
                "border-radius: 10px; "
                "}"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._block.id)
        super().mousePressEvent(event)
