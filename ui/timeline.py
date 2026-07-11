"""
Timeline visualization widget.
Displays recorded key events on a visual timeline.
"""

from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QPainterPath
)
from core.macro import KeyEvent, Macro


# Color palette for different key categories
COLORS = {
    'modifier': QColor(231, 76, 60),       # Red for modifiers
    'letter': QColor(52, 152, 219),          # Blue for letters
    'digit': QColor(46, 204, 113),           # Green for digits
    'function': QColor(155, 89, 182),        # Purple for F-keys
    'special': QColor(241, 196, 15),         # Yellow for special keys
    'space': QColor(149, 165, 166),          # Gray for space/enter/etc
    'default': QColor(52, 73, 94),           # Dark blue-gray
}

KEY_CATEGORIES = {
    'modifier': {'shift', 'ctrl', 'alt', 'win', 'left shift', 'right shift',
                 'left ctrl', 'right ctrl', 'left alt', 'right alt', 'alt gr',
                 'left windows', 'right windows'},
    'function': {f'f{i}' for i in range(1, 13)},
    'special': {'esc', 'escape', 'tab', 'caps lock', 'num lock', 'scroll lock',
                'print screen', 'pause', 'insert', 'delete', 'home', 'end',
                'page up', 'page down'},
    'space': {'space', 'enter', 'backspace', 'up', 'down', 'left', 'right'},
}


def get_key_color(key_name: str) -> QColor:
    """Get the color for a key based on its category."""
    key_lower = key_name.lower()
    for category, keys in KEY_CATEGORIES.items():
        if key_lower in keys:
            return COLORS[category]
    if key_lower.isdigit():
        return COLORS['digit']
    if len(key_lower) == 1 and key_lower.isalpha():
        return COLORS['letter']
    return COLORS['default']


class TimelineWidget(QWidget):
    """Visual timeline of keyboard events."""

    clicked = pyqtSignal(float)  # Emit time position on click

    PADDING_LEFT = 60
    PADDING_RIGHT = 20
    PADDING_TOP = 30
    PADDING_BOTTOM = 30
    TRACK_HEIGHT = 28
    TRACK_SPACING = 4
    MIN_TRACK_WIDTH = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._events: list = []
        self._duration: float = 0.0
        self._playback_pos: float = -1.0  # -1 = not playing
        self._scroll_offset: int = 0
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(True)

    def set_events(self, events: list):
        """Set the events to display."""
        self._events = events
        self._duration = events[-1].timestamp if events else 0.0
        self._playback_pos = -1.0
        self.update()

    def set_playback_position(self, pos: float):
        """Set the current playback position (seconds). -1 to clear."""
        self._playback_pos = pos
        self.update()

    def clear(self):
        """Clear all events."""
        self._events = []
        self._duration = 0.0
        self._playback_pos = -1.0
        self.update()

    def _get_time_range(self) -> tuple:
        """Get (start_time, end_time) for the timeline."""
        if not self._events:
            return (0.0, 1.0)
        return (0.0, max(self._duration, 0.1))

    def _time_to_x(self, t: float) -> float:
        """Convert time to x coordinate."""
        start, end = self._get_time_range()
        duration = end - start
        if duration <= 0:
            return self.PADDING_LEFT
        available_width = self.width() - self.PADDING_LEFT - self.PADDING_RIGHT
        return self.PADDING_LEFT + (t - start) / duration * available_width

    def _x_to_time(self, x: float) -> float:
        """Convert x coordinate to time."""
        start, end = self._get_time_range()
        duration = end - start
        available_width = self.width() - self.PADDING_LEFT - self.PADDING_RIGHT
        if available_width <= 0:
            return 0.0
        return start + (x - self.PADDING_LEFT) / available_width * duration

    def _group_events_by_key(self) -> dict:
        """Group events by key name to assign tracks."""
        tracks = {}
        track_idx = 0
        for event in self._events:
            if event.event_type != 'down':
                continue
            key = event.key_name
            if key not in tracks:
                tracks[key] = track_idx
                track_idx += 1
        return tracks

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        bg_color = QColor(248, 249, 250)
        painter.fillRect(self.rect(), bg_color)

        if not self._events:
            painter.setPen(QColor(150, 150, 150))
            font = QFont("Microsoft YaHei", 10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无录制事件")
            return

        # Draw time axis
        self._draw_time_axis(painter)

        # Group events by key
        key_tracks = self._group_events_by_key()

        # Draw key events
        self._draw_events(painter, key_tracks)

        # Draw playback position indicator
        if self._playback_pos >= 0:
            self._draw_playback_indicator(painter)

    def _draw_time_axis(self, painter: QPainter):
        """Draw the time axis with labels."""
        start, end = self._get_time_range()
        duration = end - start

        # Axis line
        y = self.PADDING_TOP - 10
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(self.PADDING_LEFT, y, self.width() - self.PADDING_RIGHT, y)

        # Tick marks and labels
        num_ticks = max(5, int(duration / 0.5))
        num_ticks = min(num_ticks, 20)
        font = QFont("Consolas", 8)
        painter.setFont(font)
        painter.setPen(QColor(120, 120, 120))

        for i in range(num_ticks + 1):
            t = start + duration * i / num_ticks
            x = self._time_to_x(t)

            # Tick mark
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawLine(int(x), y - 3, int(x), y + 3)

            # Label
            label = f"{t:.2f}s"
            painter.setPen(QColor(100, 100, 100))
            fm = QFontMetrics(font)
            label_width = fm.horizontalAdvance(label)
            painter.drawText(int(x - label_width / 2), y - 6, label)

        # Vertical grid lines
        painter.setPen(QPen(QColor(230, 230, 230), 1, Qt.DotLine))
        for i in range(1, num_ticks + 1):
            t = start + duration * i / num_ticks
            x = self._time_to_x(t)
            painter.drawLine(int(x), self.PADDING_TOP, int(x), self.height() - self.PADDING_BOTTOM)

    def _draw_events(self, painter: QPainter, key_tracks: dict):
        """Draw key event blocks on the timeline."""
        # Find the corresponding release for each press
        pressed_keys = {}  # key_name -> press_time

        for event in self._events:
            track_idx = key_tracks.get(event.key_name, 0)
            y = self.PADDING_TOP + track_idx * (self.TRACK_HEIGHT + self.TRACK_SPACING)

            if y + self.TRACK_HEIGHT > self.height() - self.PADDING_BOTTOM:
                continue  # Skip if out of bounds

            x_start = self._time_to_x(event.timestamp)

            if event.event_type == 'down':
                pressed_keys[event.key_name] = event.timestamp
                # Draw a narrow marker for press
                color = get_key_color(event.key_name)
                rect = QRect(int(x_start), y, max(self.MIN_TRACK_WIDTH, 6), self.TRACK_HEIGHT - 4)

                # Gradient fill
                gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                gradient.setColorAt(0, color.lighter(130))
                gradient.setColorAt(1, color)
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(color.darker(120), 1))
                painter.drawRoundedRect(rect, 3, 3)

                # Key label
                label = event.key_name.upper()[:8]
                font = QFont("Microsoft YaHei", 7, QFont.Bold)
                painter.setFont(font)
                painter.setPen(QColor(255, 255, 255))
                fm = QFontMetrics(font)
                if fm.horizontalAdvance(label) < rect.width() - 4:
                    painter.drawText(rect, Qt.AlignCenter, label)

            elif event.event_type == 'up' and event.key_name in pressed_keys:
                press_time = pressed_keys.pop(event.key_name)
                x_press = self._time_to_x(press_time)
                x_release = self._time_to_x(event.timestamp)
                width = max(int(x_release - x_press), self.MIN_TRACK_WIDTH)

                color = get_key_color(event.key_name)
                rect = QRect(int(x_press), y, width, self.TRACK_HEIGHT - 4)

                # Gradient fill
                gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                gradient.setColorAt(0, color.lighter(150))
                gradient.setColorAt(1, color.lighter(120))
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(color.darker(110), 1))
                painter.drawRoundedRect(rect, 3, 3)

                # Key label
                label = event.key_name.upper()[:10]
                font = QFont("Microsoft YaHei", 7, QFont.Bold)
                painter.setFont(font)
                painter.setPen(QColor(255, 255, 255))
                fm = QFontMetrics(font)
                if fm.horizontalAdvance(label) < rect.width() - 4:
                    painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_playback_indicator(self, painter: QPainter):
        """Draw the current playback position indicator."""
        x = self._time_to_x(self._playback_pos)

        # Vertical line
        painter.setPen(QPen(QColor(231, 76, 60), 2))
        painter.drawLine(int(x), self.PADDING_TOP - 5, int(x), self.height() - self.PADDING_BOTTOM)

        # Triangle marker at top
        path = QPainterPath()
        path.moveTo(int(x) - 6, self.PADDING_TOP - 8)
        path.lineTo(int(x) + 6, self.PADDING_TOP - 8)
        path.lineTo(int(x), self.PADDING_TOP - 2)
        path.closeSubpath()
        painter.setBrush(QBrush(QColor(231, 76, 60)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._events:
            t = self._x_to_time(event.x())
            self.clicked.emit(t)
