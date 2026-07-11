"""
Keyboard Macro Application - Main Entry Point

A Windows desktop keyboard macro application with:
- Real-time keyboard input recording (scan-code based, layout independent)
- Precise playback with speed control (0.25x ~ 10x)
- Multiple macro management (save/load/import/export JSON)
- Global hotkey control (Ctrl+Shift+F7/F8/F9/F10)
- Loop playback (single, multi-loop, infinite)
- Visual timeline preview
- System tray support

Requirements: Windows 10+, Python 3.8+, PyQt5, keyboard
Run as Administrator for full keyboard hook support.
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow


APP_NAME = "键盘宏"
APP_VERSION = "1.0.0"


def check_admin():
    """Check if running with admin privileges (needed for keyboard hooks)."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def main():
    # High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Set default font
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # Check admin privileges
    if not check_admin():
        print("[警告] 未以管理员身份运行，键盘钩子可能无法正常工作。")
        print("[警告] 部分按键可能无法捕获，请以管理员身份运行以获得完整功能。")

    # Create and show main window
    window = MainWindow()
    window.show()

    print(f"[{APP_NAME} v{APP_VERSION}] 程序已启动。")
    print(f"[{APP_NAME}] 热键说明:")
    print(f"  录制 开始/停止: Ctrl+Shift+F7 / Ctrl+Shift+F8")
    print(f"  回放 开始/停止: Ctrl+Shift+F9 / Ctrl+Shift+F10")
    print(f"[{APP_NAME}] 关闭窗口将最小化到系统托盘。")

    exit_code = app.exec_()

    # Cleanup
    print(f"[{APP_NAME}] 正在关闭...")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
