"""任务管理组件 - 侧栏风格"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QCheckBox, QFrame, QLineEdit, QComboBox,
    QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.models.task import Task, Priority
from src.core.task_manager import TaskManager

ACCENT = "#4F5BD5"
DANGER = "#EF4444"
SUCCESS = "#22C55E"
ORANGE = "#F59E0B"
TEXT_MUTED = "#8A8F9C"
TEXT_SECONDARY = "#6B7280"
TEXT_PRIMARY = "#1F2430"
SURFACE_BG = "#F7F8FB"


class TaskItemWidget(QFrame):
    """任务列表项（自定义委托，避免 QListWidgetItem 限制）"""

    delete_requested = Signal(str)
    check_changed = Signal(str, bool)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("task_item")

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 10, 12, 10)

        # 复选框
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._task.completed)
        self._checkbox.stateChanged.connect(
            lambda state: self.check_changed.emit(
                self._task.id, state == Qt.Checked
            )
        )
        layout.addWidget(self._checkbox)

        # 任务标题
        self._title_label = QLabel(self._task.title)
        self._title_label.setWordWrap(False)
        layout.addWidget(self._title_label, 1)

        # 优先级标签
        priority_text = {Priority.HIGH: "高", Priority.MEDIUM: "中", Priority.LOW: "低"}
        priority_colors = {
            Priority.HIGH: (DANGER, "#FEF2F2"),
            Priority.MEDIUM: (ORANGE, "#FFFBEB"),
            Priority.LOW: (SUCCESS, "#ECFDF5"),
        }
        p_label = QLabel(priority_text.get(self._task.priority, "中"))
        p_fg, p_bg = priority_colors.get(self._task.priority, (TEXT_SECONDARY, SURFACE_BG))
        p_label.setObjectName("priority_chip")
        p_label.setStyleSheet(
            f"color: {p_fg}; background: {p_bg}; "
            f"font-weight: 700; font-size: 10px; "
            f"padding: 2px 8px; border-radius: 6px;"
        )
        layout.addWidget(p_label)

        # 时长
        dur = QLabel(f"{self._task.estimated_minutes}m")
        dur.setObjectName("duration_label")
        dur.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(dur)

        # 删除按钮
        del_btn = QPushButton("×")
        del_btn.setFixedSize(22, 22)
        del_btn.setObjectName("danger_button")
        del_btn.setStyleSheet(
            f"background: transparent; color: #C6CBD3; "
            f"border: none; font-size: 15px; font-weight: 700; "
            f"padding: 0; border-radius: 11px;"
        )
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._task.id))
        layout.addWidget(del_btn)

        self._apply_style()

    def _apply_style(self):
        if self._task.completed:
            self.setStyleSheet(
                "#task_item { "
                f"background: #FAFAFA; border: 1px solid #F0F0F0; "
                "border-radius: 10px; opacity: 0.7; "
                "}"
            )
            self._title_label.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 13px; text-decoration: line-through;"
            )
        else:
            self.setStyleSheet(
                "#task_item { "
                "background: #F7F8FB; border: 1px solid #ECEDF2; "
                "border-radius: 10px; "
                "}"
            )
            self._title_label.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
            )


class TaskManagerWidget(QWidget):
    """任务管理组件"""

    tasks_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._task_widgets: dict[str, TaskItemWidget] = {}
        self._init_ui()
        self._load_tasks()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 卡片容器
        card = QFrame()
        card.setObjectName("task_card")

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # ---- 卡片头部 ----
        header = QFrame()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #ECEDF2;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title = QLabel("任务管理")
        title.setObjectName("task_title")
        font = QFont()
        font.setPointSize(15)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        header_layout.addWidget(title)

        self._stats_label = QLabel()
        self._stats_label.setObjectName("task_stats")
        header_layout.addWidget(self._stats_label)

        header_layout.addStretch()
        card_layout.addWidget(header)

        # ---- 任务列表（可滚动）----
        scroll = QScrollArea()
        scroll.setObjectName("task_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "#task_scroll { border: none; background: transparent; }"
        )

        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(8)
        self._list_layout.setContentsMargins(14, 12, 14, 12)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        card_layout.addWidget(scroll, 1)

        # ---- 底部按钮栏 ----
        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #ECEDF2;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 10, 14, 10)
        footer_layout.setSpacing(8)

        add_btn = QPushButton("+ 添加任务")
        add_btn.setObjectName("primary_button")
        add_btn.setStyleSheet(
            f"QPushButton {{ "
            f"background: {ACCENT}; color: #FFFFFF; "
            f"border: none; border-radius: 8px; "
            f"padding: 8px 16px; font-size: 13px; font-weight: 600; "
            f"}} "
            f"QPushButton:hover {{ background: #3D4AB8; }}"
        )
        add_btn.clicked.connect(self._show_add_task_dialog)
        footer_layout.addWidget(add_btn)

        optimize_btn = QPushButton("优化安排")
        optimize_btn.setObjectName("secondary_button")
        optimize_btn.setStyleSheet(
            f"QPushButton {{ "
            f"background: #F0F2F5; color: #4B5563; "
            f"border: 1px solid #E3E5EC; border-radius: 8px; "
            f"padding: 8px 16px; font-size: 13px; font-weight: 600; "
            f"}} "
            f"QPushButton:hover {{ background: #E5E7EB; }}"
        )
        optimize_btn.clicked.connect(self._optimize_schedule)
        footer_layout.addWidget(optimize_btn)

        clear_btn = QPushButton("清已完成")
        clear_btn.setObjectName("secondary_button")
        clear_btn.setStyleSheet(
            f"QPushButton {{ "
            f"background: #F0F2F5; color: #4B5563; "
            f"border: 1px solid #E3E5EC; border-radius: 8px; "
            f"padding: 8px 16px; font-size: 13px; font-weight: 600; "
            f"}} "
            f"QPushButton:hover {{ background: #E5E7EB; }}"
        )
        clear_btn.clicked.connect(self._clear_completed)
        footer_layout.addWidget(clear_btn)

        card_layout.addWidget(footer)

        layout.addWidget(card)

    def _load_tasks(self):
        """加载任务列表"""
        # 清除旧 widgets
        for w in list(self._task_widgets.values()):
            w.deleteLater()
        self._task_widgets.clear()

        # 从布局中移除 stretch
        stretch_item = self._list_layout.takeAt(self._list_layout.count() - 1)

        tasks = self._task_manager.get_tasks()
        for task in tasks:
            self._add_task_widget(task)

        # 重新添加 stretch
        self._list_layout.addStretch()

        self._update_stats()

    def _add_task_widget(self, task: Task):
        """添加单个任务 widget"""
        widget = TaskItemWidget(task)
        widget.delete_requested.connect(self._on_task_delete)
        widget.check_changed.connect(self._on_task_check_changed)

        # 插入到 stretch 之前
        self._list_layout.insertWidget(
            self._list_layout.count() - 1, widget
        )
        self._task_widgets[task.id] = widget

    def _update_stats(self):
        """更新统计"""
        stats = self._task_manager.get_task_stats()
        self._stats_label.setText(
            f"完成 {stats['completed']}/{stats['total']}"
        )

    def _show_add_task_dialog(self):
        dialog = AddTaskDialog(self)
        dialog.task_added.connect(self._on_task_added)
        dialog.exec()

    def _on_task_added(self, title: str, minutes: int, priority: Priority):
        self._task_manager.add_task(title, minutes, priority)
        self._load_tasks()
        self.tasks_changed.emit()

    def _on_task_check_changed(self, task_id: str, checked: bool):
        task = self._task_manager.get_task_by_id(task_id)
        if task:
            task.completed = checked
            self._task_manager.update_task(task_id, completed=checked)
            # 重新加载以更新样式
            self._load_tasks()
            self.tasks_changed.emit()

    def _on_task_delete(self, task_id: str):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个任务吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._task_manager.delete_task(task_id)
            self._load_tasks()
            self.tasks_changed.emit()

    def _optimize_schedule(self):
        self.tasks_changed.emit()

    def _clear_completed(self):
        reply = QMessageBox.question(
            self, "确认清除", "确定要清除所有已完成的任务吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._task_manager.clear_completed_tasks()
            self._load_tasks()
            self.tasks_changed.emit()

    def refresh(self):
        self._load_tasks()


class AddTaskDialog(QDialog):
    """添加任务对话框"""

    task_added = Signal(str, int, Priority)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("添加任务")
        self.setModal(True)
        self.resize(400, 250)

        layout = QFormLayout(self)

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("请输入任务标题")
        layout.addRow("任务标题:", self._title_input)

        self._duration_input = QSpinBox()
        self._duration_input.setRange(5, 480)
        self._duration_input.setValue(30)
        self._duration_input.setSuffix(" 分钟")
        layout.addRow("预计时长:", self._duration_input)

        self._priority_input = QComboBox()
        self._priority_input.addItems(["高", "中", "低"])
        layout.addRow("优先级:", self._priority_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_ok(self):
        title = self._title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "警告", "请输入任务标题")
            return

        duration = self._duration_input.value()
        priority_map = {
            "高": Priority.HIGH, "中": Priority.MEDIUM, "低": Priority.LOW
        }
        priority = priority_map.get(
            self._priority_input.currentText(), Priority.MEDIUM
        )

        self.task_added.emit(title, duration, priority)
        self.accept()
