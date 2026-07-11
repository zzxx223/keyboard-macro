"""
System tray icon and context menu.
"""

from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QApplication
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont


def create_tray_icon(active: bool = False) -> QIcon:
    """Create a tray icon programmatically (no external resource files needed)."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Circle background
    if active:
        bg = QColor(231, 76, 60)  # Red when recording/playing
    else:
        bg = QColor(52, 152, 219)  # Blue when idle

    painter.setBrush(bg)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)

    # Keyboard icon (simplified)
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 12, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "K")

    painter.end()
    return QIcon(pixmap)


class SystemTray(QObject):
    """System tray with quick action menu."""

    record_toggled = pyqtSignal()
    play_toggled = pyqtSignal()
    show_window = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(create_tray_icon(False), parent)
        self._tray.setToolTip("键盘宏 - 就绪")

        self._menu = QMenu()
        self._build_menu()

        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)

    def _build_menu(self):
        self._menu.clear()

        # Show window
        action_show = QAction("显示主窗口", self._menu)
        action_show.triggered.connect(self.show_window.emit)
        self._menu.addAction(action_show)

        self._menu.addSeparator()

        # Record toggle
        self._action_record = QAction("开始录制 (Ctrl+Shift+F7)", self._menu)
        self._action_record.triggered.connect(self.record_toggled.emit)
        self._menu.addAction(self._action_record)

        # Play toggle
        self._action_play = QAction("开始回放 (Ctrl+Shift+F9)", self._menu)
        self._action_play.triggered.connect(self.play_toggled.emit)
        self._menu.addAction(self._action_play)

        self._menu.addSeparator()

        # Quit
        action_quit = QAction("退出", self._menu)
        action_quit.triggered.connect(self.quit_app.emit)
        self._menu.addAction(action_quit)

    def show(self):
        self._tray.show()

    def set_recording(self, recording: bool):
        """Update tray state for recording."""
        if recording:
            self._tray.setIcon(create_tray_icon(True))
            self._tray.setToolTip("键盘宏 - 录制中...")
            self._action_record.setText("停止录制 (Ctrl+Shift+F8)")
        else:
            self.set_idle()
            self._action_record.setText("开始录制 (Ctrl+Shift+F7)")

    def set_playing(self, playing: bool):
        """Update tray state for playback."""
        if playing:
            self._tray.setIcon(create_tray_icon(True))
            self._tray.setToolTip("键盘宏 - 回放中...")
            self._action_play.setText("停止回放 (Ctrl+Shift+F10)")
        else:
            self.set_idle()
            self._action_play.setText("开始回放 (Ctrl+Shift+F9)")

    def set_idle(self):
        """Set tray to idle state."""
        self._tray.setIcon(create_tray_icon(False))
        self._tray.setToolTip("键盘宏 - 就绪")

    def show_message(self, title: str, message: str, duration: int = 3000):
        """Show a balloon message from the tray."""
        self._tray.showMessage(title, message, QSystemTrayIcon.Information, duration)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window.emit()
