"""
Generate the application icon (app_icon.ico) using PyQt5.
Run this before building the EXE with PyInstaller.

Usage: python gen_icon.py
"""

import sys
import struct

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QRect, QBuffer, QByteArray
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPolygon
)


def create_icon_pixmap(size: int = 256) -> QPixmap:
    """Create the application icon as a QPixmap."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Dark rounded rect background
    p.setBrush(QColor('#2c3e50'))
    p.setPen(Qt.NoPen)
    margin = size // 10
    p.drawRoundedRect(margin, margin, size - 2 * margin, size - 2 * margin,
                      size // 8, size // 8)

    # Keyboard keys area
    p.setBrush(QColor('#ecf0f1'))
    inner_margin = size // 8
    inner_rect = QRect(inner_margin, size // 4,
                       size - 2 * inner_margin, size // 2)
    p.drawRoundedRect(inner_rect, size // 25, size // 25)

    # Draw key grid
    p.setBrush(QColor('#2c3e50'))
    key_size = size // 12
    spacing = key_size + size // 18
    start_x = inner_rect.x() + size // 12
    start_y = inner_rect.y() + size // 12

    for row in range(3):
        for col in range(5):
            x = start_x + col * spacing
            y = start_y + row * spacing
            p.drawRoundedRect(x, y, key_size, key_size, 3, 3)

    # Red record dot (top-right)
    p.setBrush(QColor('#e74c3c'))
    dot_size = size // 10
    p.drawEllipse(size - dot_size * 2, dot_size // 2, dot_size, dot_size)

    # Green play triangle (bottom-right)
    p.setBrush(QColor('#27ae60'))
    triangle = QPolygon()
    t_size = size // 12
    t_x = size - t_size * 2
    t_y = size - t_size * 2
    triangle.setPoints(3,
                        t_x, t_y,
                        t_x, t_y + t_size,
                        t_x + t_size, t_y + t_size // 2)
    p.drawPolygon(triangle)

    p.end()
    return pix


def save_ico(pixmap: QPixmap, filepath: str, sizes=None):
    """Save a QPixmap as a multi-size ICO file."""
    if sizes is None:
        sizes = [256, 128, 64, 48, 32, 16]

    pixmaps = []
    for s in sizes:
        scaled = pixmap.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmaps.append(scaled)

    with open(filepath, 'wb') as f:
        # ICO header
        f.write(struct.pack('<HHH', 0, 1, len(pixmaps)))

        # Calculate offset
        offset = 6 + 16 * len(pixmaps)

        # Directory entries
        image_data_list = []
        for pm in pixmaps:
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QBuffer.WriteOnly)
            pm.save(buf, 'PNG')
            data = ba.data()
            image_data_list.append(data)

            w = pm.width()
            h = pm.height()
            w_byte = 0 if w >= 256 else w
            h_byte = 0 if h >= 256 else h

            f.write(struct.pack('<BBBBHHII',
                                w_byte, h_byte, 0, 0,
                                1, 32,
                                len(data), offset))
            offset += len(data)

        # Image data
        for data in image_data_list:
            f.write(data)


def main():
    app = QApplication(sys.argv)

    pixmap = create_icon_pixmap(256)
    save_ico(pixmap, 'app_icon.ico')
    print(f'Icon saved: app_icon.ico ({pixmap.width()}x{pixmap.height()})')

    app.quit()


if __name__ == '__main__':
    main()
