"""HourFlow · 主入口文件"""
import sys
import signal
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow, create_default_icon
from src.core.config_manager import ConfigManager


def load_stylesheet(app: QApplication):
    """加载 QSS 样式表"""
    style_paths = [
        Path(__file__).parent / "resources" / "styles" / "style.qss",
        Path(__file__).parent / "src" / "ui" / "styles" / "style.qss",
    ]
    for path in style_paths:
        if path.exists():
            try:
                app.setStyleSheet(path.read_text(encoding="utf-8"))
                return
            except Exception:
                pass


def main():
    """主函数"""
    app = QApplication(sys.argv)

    app.setApplicationName("HourFlow")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("HourFlow")

    app._tray_icon = None

    config = ConfigManager()

    window = MainWindow()
    window.setWindowIcon(create_default_icon())

    if hasattr(window, "_tray"):
        app._tray_icon = window._tray

    # 加载自定义样式表
    load_stylesheet(app)

    window.show()

    def signal_handler(signum, frame):
        print("\n正在退出...")
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
