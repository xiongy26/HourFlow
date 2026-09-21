"""主窗口 - 紧凑模式默认 + 全功能展开"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QLabel, QMessageBox,
    QPushButton, QFrame, QSplitter, QStackedWidget,
    QProgressBar
)
from PySide6.QtCore import Signal, QTimer, Qt, QSize
from PySide6.QtGui import QAction, QCloseEvent, QPixmap, QPainter, QColor, QIcon, QPen, QFont
from datetime import datetime

from src.ui.widgets.countdown_widget import CountdownWidget
from src.ui.widgets.time_viz_widget import TimeVizWidget
from src.ui.widgets.schedule_widget import ScheduleWidget
from src.ui.widgets.task_manager_widget import TaskManagerWidget, AddTaskDialog
from src.ui.widgets.settings_dialog import SettingsDialog
from src.core.config_manager import ConfigManager
from src.core.task_manager import TaskManager
from src.services.reminder_service import ReminderService

ACCENT = "#4F5BD5"
TEXT_MUTED = "#8A8F9C"
TEXT_SECONDARY = "#6B7280"


def create_default_icon() -> QIcon:
    """创建默认图标（HourFlow 品牌时钟标志）"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(6, 6, 52, 52)

    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(13, 13, 38, 38)

    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.NoPen)
    painter.save()
    painter.translate(32, 32)
    painter.rotate(-45)
    painter.drawRoundedRect(-2, -14, 4, 15, 2, 2)
    painter.rotate(120)
    painter.drawRoundedRect(-2, -10, 4, 11, 2, 2)
    painter.restore()
    painter.drawEllipse(29, 29, 6, 6)

    painter.end()
    return QIcon(pixmap)


class CompactRingWidget(QWidget):
    """紧凑模式进度环（小尺寸版，跟展开状态同款视觉）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._color = QColor(ACCENT)

    def set_progress(self, value: float):
        self._progress = min(max(value, 0.0), 100.0)
        self.update()

    def set_color(self, color_str: str):
        self._color = QColor(color_str)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height())
        cx, cy = size // 2, size // 2
        radius = cx - 4
        pen_width = 4

        # 背景环
        painter.setPen(QPen(QColor("#ECEDF2"), pen_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # 进度环
        if self._progress > 0:
            painter.setPen(QPen(self._color, pen_width))
            painter.setBrush(Qt.NoBrush)
            start_angle = 90 * 16
            span_angle = int(-360 * self._progress / 100 * 16)
            painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                           start_angle, span_angle)

        # 中心小图标（时钟感）
        painter.setPen(QPen(self._color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(cx - 4, cy - 4, 8, 8)
        painter.drawLine(cx, cy - 2, cx, cy)
        painter.drawLine(cx, cy, cx + 2, cy + 1)


class MainWindow(QMainWindow):
    """主窗口 - 紧凑模式默认展开"""

    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._task_manager = TaskManager()
        self._reminder_service = None
        self._is_compact = True  # 默认紧凑模式
        self._init_ui()
        self._init_tray()
        self._init_reminder()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("HourFlow")
        self.setMinimumSize(680, 56)
        self.resize(680, 56)

        self._apply_opacity()

        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        # 紧凑头部（始终显示）
        self._compact_bar = self._create_compact_bar()
        self._main_layout.addWidget(self._compact_bar)

        # 完整内容区（隐藏，展开时显示）
        self._full_content = self._create_full_content()
        self._full_content.hide()
        self._main_layout.addWidget(self._full_content, 1)

        # 菜单栏（展开时才显示）
        self._menu_bar_widget = self.menuBar()
        self._create_menu_bar()
        self._menu_bar_widget.hide()  # 默认折叠，隐藏菜单栏

        # 启动紧凑模式时钟
        self._compact_timer = QTimer(self)
        self._compact_timer.timeout.connect(self._update_compact_clock)
        self._compact_timer.start(1000)
        self._update_compact_clock()

        # 完整视图统计更新
        timer = QTimer(self)
        timer.timeout.connect(self._update_stats)
        timer.start(60000)

    def _create_compact_bar(self) -> QWidget:
        """创建紧凑模式头部"""
        bar = QFrame()
        bar.setObjectName("header_bar")
        bar.setFixedHeight(56)
        bar.setStyleSheet("""
            #header_bar {
                background: #FFFFFF;
                border-bottom: 1px solid #ECEDF2;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(12)

        # Logo
        logo_label = QLabel("⏱")
        logo_label.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(logo_label)

        # 品牌名
        brand = QLabel("HourFlow")
        brand.setObjectName("app_brand")
        brand.setStyleSheet("font-size: 14px; font-weight: 700; color: #1F2430;")
        layout.addWidget(brand)

        layout.addSpacing(8)

        # 进度环（紧凑版）
        self._compact_ring = CompactRingWidget()
        self._compact_ring.setFixedSize(36, 36)
        layout.addWidget(self._compact_ring)

        # 进度百分比
        self._compact_progress_label = QLabel("0%")
        self._compact_progress_label.setStyleSheet(
            "font-size: 11px; color: #8A8F9C; font-weight: 600;"
        )
        layout.addWidget(self._compact_progress_label)

        layout.addSpacing(8)

        # 倒计时（醒目显示）
        self._compact_countdown = QLabel("00:00")
        self._compact_countdown.setStyleSheet(
            "font-size: 26px; font-weight: 800; "
            "color: #4F5BD5; font-family: 'SF Mono', Consolas, monospace;"
        )
        layout.addWidget(self._compact_countdown)

        # 单位
        unit = QLabel("时:分")
        unit.setStyleSheet("font-size: 11px; color: #8A8F9C;")
        layout.addWidget(unit)

        layout.addSpacing(8)

        # 日期时间
        self._compact_datetime = QLabel()
        self._compact_datetime.setStyleSheet(
            "font-size: 12px; color: #6B7280;"
        )
        layout.addWidget(self._compact_datetime)

        layout.addSpacing(4)

        # 展开/收起按钮
        self._toggle_btn = QPushButton("↗ 展开")
        self._toggle_btn.setObjectName("secondary_button")
        self._toggle_btn.setFixedHeight(30)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background: #F0F2F5;
                color: #4B5563;
                border: 1px solid #E3E5EC;
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
        """)
        self._toggle_btn.clicked.connect(self._toggle_view)
        layout.addWidget(self._toggle_btn)

        return bar

    def _create_full_content(self) -> QWidget:
        """创建完整功能内容区"""
        widget = QWidget()

        # 使用 QStackedWidget 方便管理标签页
        self._view_stack = QStackedWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view_stack)

        # ---- 全功能视图 ----
        full_view = QWidget()
        full_layout = QVBoxLayout(full_view)
        full_layout.setSpacing(0)
        full_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        # 左侧
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        full_layout.addWidget(splitter)
        self._view_stack.addWidget(full_view)

        return widget

    def _create_left_panel(self) -> QWidget:
        """左侧主内容区"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 7, 14)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        self._countdown_widget = CountdownWidget()
        self._countdown_widget.setMinimumWidth(380)
        top_row.addWidget(self._countdown_widget, 2)

        self._time_viz_widget = TimeVizWidget()
        self._time_viz_widget.setMinimumWidth(240)
        self._time_viz_widget.setMaximumWidth(320)
        top_row.addWidget(self._time_viz_widget, 1)

        layout.addLayout(top_row)

        self._schedule_widget = ScheduleWidget()
        self._schedule_widget.add_task_clicked.connect(self._show_add_task_dialog)
        layout.addWidget(self._schedule_widget, 1)

        return panel

    def _create_right_panel(self) -> QWidget:
        """右侧任务管理侧栏"""
        panel = QFrame()
        panel.setObjectName("sidebar_panel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(0)
        layout.setContentsMargins(7, 14, 14, 14)

        self._task_widget = TaskManagerWidget()
        self._task_widget.tasks_changed.connect(self._on_tasks_changed)
        layout.addWidget(self._task_widget)

        return panel

    def _on_tasks_changed(self):
        """任务变更后刷新今日计划"""
        self._schedule_widget.refresh()

    def _toggle_view(self):
        """切换紧凑/完整视图"""
        self._is_compact = not self._is_compact

        if self._is_compact:
            # 收起为紧凑模式
            self._full_content.hide()
            self._compact_bar.show()
            self._menu_bar_widget.hide()
            self._toggle_btn.setText("↗ 展开")
            self.setMinimumSize(680, 56)
            self.resize(680, 56)
        else:
            # 展开为完整视图
            self._full_content.show()
            self._menu_bar_widget.show()
            self.setMinimumSize(1000, 650)
            self.resize(1200, 720)
            self._toggle_btn.setText("↙ 收起")

    def _update_compact_clock(self):
        """更新紧凑模式的时钟和倒计时"""
        now = datetime.now()
        self._compact_datetime.setText(
            now.strftime("%m/%d %H:%M")
        )

        # 更新倒计时
        work_end_hour, work_end_minute = self._parse_work_time()
        lunch_enabled = self._config.is_lunch_break_enabled()
        lunch_start = self._config.get_lunch_break_start()
        lunch_end = self._config.get_lunch_break_end()

        from src.utils.time_utils import calculate_time_remaining, format_countdown
        remaining_seconds = calculate_time_remaining(
            work_end_hour, work_end_minute,
            lunch_enabled, lunch_start, lunch_end
        )
        countdown = format_countdown(remaining_seconds, show_seconds=False)
        self._compact_countdown.setText(countdown)

        # 动态颜色：快下班了变红/橙
        if remaining_seconds <= 0:
            color = "#22C55E"
        elif remaining_seconds < 1800:
            color = "#EF4444"
        elif remaining_seconds < 3600:
            color = "#F59E0B"
        else:
            color = ACCENT

        self._compact_countdown.setStyleSheet(
            f"font-size: 26px; font-weight: 800; "
            f"color: {color}; font-family: 'SF Mono', Consolas, monospace;"
        )

        # 更新进度条
        from src.utils.time_utils import calculate_work_progress
        progress = calculate_work_progress(
            self._config.get_work_start_time(),
            self._config.get_work_end_time(),
            lunch_enabled, lunch_start, lunch_end
        )
        self._compact_progress_label.setText(f"{progress:.0f}%")
        self._compact_ring.set_progress(progress)
        self._compact_ring.set_color(color)

    def _parse_work_time(self):
        """解析下班时间"""
        work_end = self._config.get_work_end_time()
        parts = work_end.split(":")
        return int(parts[0]), int(parts[1])

    def _create_menu_bar(self):
        """创建菜单栏"""
        self._menu_bar_widget.clear()
        file_menu = self._menu_bar_widget.addMenu("文件")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self._menu_bar_widget.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_tray(self):
        """初始化系统托盘"""
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(create_default_icon())
        self._tray.setToolTip("HourFlow")

        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

        self._countdown_widget.time_updated.connect(self._update_tray_tooltip)

    def _update_tray_tooltip(self, countdown: str, current_time: str):
        self._tray.setToolTip(f"HourFlow\n下班倒计时: {countdown}")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def _init_reminder(self):
        if self._config.is_sedentary_reminder_enabled():
            self._reminder_service = ReminderService(
                self._config.get_sedentary_interval()
            )
            self._reminder_service.start(self._on_reminder_triggered)

    def _on_reminder_triggered(self):
        tip = ReminderService.get_random_tip()
        QMessageBox.information(
            self, "休息提醒",
            f"您已经连续工作{self._config.get_sedentary_interval()}分钟了！\n\n💡 {tip}"
        )

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _show_add_task_dialog(self):
        dialog = AddTaskDialog(self)
        dialog.task_added.connect(self._on_task_added)
        dialog.exec()

    def _on_task_added(self, title: str, minutes: int, priority):
        self._task_manager.add_task(title, minutes, priority)
        self._schedule_widget.refresh()

    def _on_settings_changed(self):
        if self._reminder_service:
            self._reminder_service.stop()

        if self._config.is_sedentary_reminder_enabled():
            self._reminder_service = ReminderService(
                self._config.get_sedentary_interval()
            )
            self._reminder_service.start(self._on_reminder_triggered)

        self._apply_opacity()
        self._update_compact_clock()

    def _apply_opacity(self):
        opacity = self._config.get_window_opacity()
        if opacity == 0:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setStyleSheet("QMainWindow { background: transparent; }")
        else:
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setStyleSheet("")
            self.setWindowOpacity(opacity)

    def _show_about(self):
        QMessageBox.about(
            self, "关于 HourFlow",
            "HourFlow v1.0\n桌面时间管理助手\n\n"
            "帮助你建立清晰的时间感知，高效完成每日任务。\n\n"
            "功能特点：\n"
            "• 下班倒计时与进度可视化\n"
            "• 智能时间块分配\n"
            "• 久坐提醒\n"
            "• 今日计划时间轴"
        )

    def _update_stats(self):
        pass

    def closeEvent(self, event: QCloseEvent):
        if self._config.is_minimize_to_tray():
            self.hide()
            event.ignore()
        else:
            if self._reminder_service:
                self._reminder_service.stop()
            event.accept()
