"""
Main application window.
Provides full GUI for macro management, recording, and playback control.
"""

import time
import json
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QComboBox,
    QSpinBox, QLineEdit, QTextEdit, QProgressBar, QStatusBar,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QCheckBox,
    QToolBar, QAction, QFrame, QSizePolicy, QMenu, QStyle
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap, QPainter

from core.macro import Macro, MacroManager, KeyEvent
from core.recorder import KeyboardRecorder
from core.player import KeyboardPlayer
from core.hotkeys import GlobalHotkeyManager, DEFAULT_HOTKEYS
from ui.timeline import TimelineWidget
from ui.tray import SystemTray


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals for cross-thread communication
    recording_event = pyqtSignal(object)  # KeyEvent
    playback_progress = pyqtSignal(float, float, int, int)
    playback_state = pyqtSignal(str)
    playback_key = pyqtSignal(object)  # KeyEvent

    def __init__(self):
        super().__init__()
        self.setWindowTitle("键盘宏 - 键盘宏录制回放工具")
        self.setMinimumSize(1000, 650)

        # Core components
        storage_dir = os.path.join(os.path.expanduser("~"), ".keyboard_macro", "macros")
        self.macro_manager = MacroManager(storage_dir)
        self.recorder = KeyboardRecorder()
        self.player = KeyboardPlayer()
        self.hotkey_mgr = GlobalHotkeyManager()

        # State
        self._current_macro: Macro = None
        self._is_recording = False
        self._is_playing = False
        self._speed = 1.0
        self._loop_count = 1
        self._macros: list = []

        # Build UI
        self._build_ui()
        self._connect_signals()
        self._load_macros()
        self._setup_hotkeys()

        # System tray
        self._tray = SystemTray(self)
        self._connect_tray()
        self._tray.show()

        # Apply styling
        self._apply_style()

    def _build_ui(self):
        """Build the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self._build_toolbar()
        main_layout.addWidget(self._toolbar)

        # Control panel
        self._build_control_panel()
        main_layout.addWidget(self._control_frame)

        # Main content area (splitter)
        splitter = QSplitter(Qt.Horizontal)
        self._build_macro_list(splitter)
        self._build_detail_panel(splitter)
        splitter.setSizes([280, 720])
        main_layout.addWidget(splitter, 1)

        # Status bar
        self._build_status_bar()

    def _build_toolbar(self):
        """Build the main toolbar."""
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setIconSize(QSize(24, 24))

        # Record button
        self._act_record = QAction("录制", self)
        self._act_record.setToolTip("开始录制 (Ctrl+Shift+F7)")
        self._act_record.triggered.connect(self._on_record_toggle)
        self._toolbar.addAction(self._act_record)

        # Stop button
        self._act_stop = QAction("停止", self)
        self._act_stop.setToolTip("停止录制/回放")
        self._act_stop.triggered.connect(self._on_stop_all)
        self._toolbar.addAction(self._act_stop)

        self._toolbar.addSeparator()

        # Play button
        self._act_play = QAction("回放", self)
        self._act_play.setToolTip("开始回放 (Ctrl+Shift+F9)")
        self._act_play.triggered.connect(self._on_play_toggle)
        self._toolbar.addAction(self._act_play)

        self._toolbar.addSeparator()

        # Speed selector
        speed_label = QLabel("  速度: ")
        self._toolbar.addWidget(speed_label)
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "3x", "5x", "10x"])
        self._speed_combo.setCurrentText("1x")
        self._speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self._toolbar.addWidget(self._speed_combo)

        # Loop count
        loop_label = QLabel("  循环: ")
        self._toolbar.addWidget(loop_label)
        self._loop_spin = QSpinBox()
        self._loop_spin.setRange(1, 9999)
        self._loop_spin.setValue(1)
        self._loop_spin.valueChanged.connect(self._on_loop_changed)
        self._toolbar.addWidget(self._loop_spin)

        # Infinite loop checkbox
        self._infinite_check = QCheckBox("无限")
        self._infinite_check.stateChanged.connect(self._on_infinite_toggled)
        self._toolbar.addWidget(self._infinite_check)

        self._toolbar.addSeparator()

        # New macro
        self._act_new = QAction("新建", self)
        self._act_new.triggered.connect(self._on_new_macro)
        self._toolbar.addAction(self._act_new)

        # Save
        self._act_save = QAction("保存", self)
        self._act_save.triggered.connect(self._on_save_macro)
        self._toolbar.addAction(self._act_save)

        # Delete
        self._act_delete = QAction("删除", self)
        self._act_delete.triggered.connect(self._on_delete_macro)
        self._toolbar.addAction(self._act_delete)

        self._toolbar.addSeparator()

        # Import/Export
        self._act_import = QAction("导入", self)
        self._act_import.triggered.connect(self._on_import_macro)
        self._toolbar.addAction(self._act_import)

        self._act_export = QAction("导出", self)
        self._act_export.triggered.connect(self._on_export_macro)
        self._toolbar.addAction(self._act_export)

    def _build_control_panel(self):
        """Build the recording/playback control panel."""
        self._control_frame = QFrame()
        self._control_frame.setMaximumHeight(60)
        self._control_frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self._control_frame)
        layout.setContentsMargins(12, 8, 12, 8)

        # Status indicator
        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 4px 12px;
            }
        """)
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1000)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("未回放")
        self._progress_bar.setMaximumWidth(300)
        layout.addWidget(self._progress_bar, 1)

        # Time display
        self._time_label = QLabel("00:00.00 / 00:00.00")
        self._time_label.setStyleSheet("font-family: Consolas; font-size: 12px; color: #7f8c8d;")
        layout.addWidget(self._time_label)

    def _build_macro_list(self, parent):
        """Build the macro list panel."""
        group = QGroupBox("宏列表")
        layout = QVBoxLayout(group)

        self._macro_list = QListWidget()
        self._macro_list.setAlternatingRowColors(True)
        self._macro_list.currentRowChanged.connect(self._on_macro_selected)
        self._macro_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._macro_list.customContextMenuRequested.connect(self._on_macro_context_menu)
        layout.addWidget(self._macro_list)

        # Macro count label
        self._count_label = QLabel("共 0 个宏")
        self._count_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        layout.addWidget(self._count_label)

        group.setLayout(layout)
        parent.addWidget(group)

    def _build_detail_panel(self, parent):
        """Build the detail/timeline panel."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # Macro info group
        info_group = QGroupBox("宏详情")
        info_layout = QFormLayout(info_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("宏名称...")
        info_layout.addRow("名称:", self._name_edit)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("描述（可选）...")
        info_layout.addRow("描述:", self._desc_edit)

        # Stats row
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        self._stat_keys = QLabel("按键: 0")
        self._stat_duration = QLabel("时长: 0.00秒")
        self._stat_events = QLabel("事件: 0")
        for w in [self._stat_keys, self._stat_duration, self._stat_events]:
            w.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            stats_layout.addWidget(w)
        stats_layout.addStretch()
        info_layout.addRow("统计:", stats_widget)

        self._name_edit.textChanged.connect(self._on_macro_edited)
        self._desc_edit.textChanged.connect(self._on_macro_edited)

        layout.addWidget(info_group)

        # Timeline group
        timeline_group = QGroupBox("按键时间轴预览")
        timeline_layout = QVBoxLayout(timeline_group)
        self._timeline = TimelineWidget()
        timeline_layout.addWidget(self._timeline)
        layout.addWidget(timeline_group, 1)

        parent.addWidget(container)

    def _build_status_bar(self):
        """Build the status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._sb_status = QLabel("就绪")
        self._status_bar.addWidget(self._sb_status, 1)

        self._sb_hotkeys = QLabel("热键: 录制=Ctrl+Shift+F7  回放=Ctrl+Shift+F9  停止=Ctrl+Shift+F8/F10")
        self._sb_hotkeys.setStyleSheet("color: #95a5a6; font-size: 10px;")
        self._status_bar.addPermanentWidget(self._sb_hotkeys)

    def _connect_signals(self):
        """Connect signals to handlers."""
        self.recording_event.connect(self._on_recording_event)
        self.playback_progress.connect(self._on_playback_progress)
        self.playback_state.connect(self._on_playback_state)
        self.playback_key.connect(self._on_playback_key)

    def _connect_tray(self):
        """Connect tray signals."""
        self._tray.record_toggled.connect(self._on_record_toggle)
        self._tray.play_toggled.connect(self._on_play_toggle)
        self._tray.show_window.connect(self._show_from_tray)
        self._tray.quit_app.connect(self._quit_app)

    def _setup_hotkeys(self):
        """Set up global hotkeys."""
        self.hotkey_mgr.set_callback('record_start', lambda: self._on_record_toggle())
        self.hotkey_mgr.set_callback('record_stop', lambda: self._on_record_toggle())
        self.hotkey_mgr.set_callback('play_start', lambda: self._on_play_toggle())
        self.hotkey_mgr.set_callback('play_stop', lambda: self._on_play_toggle())

        for action, hotkey in DEFAULT_HOTKEYS.items():
            self.hotkey_mgr.set_hotkey(action, hotkey)

        self.hotkey_mgr.enable()

    def _load_macros(self):
        """Load all macros from storage."""
        self._macros = self.macro_manager.load_all()
        self._refresh_macro_list()

    def _refresh_macro_list(self):
        """Refresh the macro list widget."""
        self._macro_list.clear()
        for macro in self._macros:
            item = QListWidgetItem()
            display = f"{macro.name}\n  {macro.key_count} 次按键  |  {macro.duration:.2f}秒  |  循环 {macro.loop_count} 次"
            item.setText(display)
            item.setData(Qt.UserRole, macro)
            self._macro_list.addItem(item)

        self._count_label.setText(f"共 {len(self._macros)} 个宏")

        if self._macros and self._macro_list.currentRow() < 0:
            self._macro_list.setCurrentRow(0)

    def _get_selected_macro(self) -> Macro:
        """Get the currently selected macro."""
        item = self._macro_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def _on_macro_selected(self, row):
        """Handle macro selection."""
        macro = self._get_selected_macro()
        if macro:
            self._current_macro = macro
            self._name_edit.blockSignals(True)
            self._desc_edit.blockSignals(True)
            self._name_edit.setText(macro.name)
            self._desc_edit.setText(macro.description)
            self._name_edit.blockSignals(False)
            self._desc_edit.blockSignals(False)
            self._loop_spin.setValue(macro.loop_count)
            self._timeline.set_events(macro.events)
            self._update_stats(macro)
        else:
            self._timeline.clear()
            self._name_edit.clear()
            self._desc_edit.clear()

    def _update_stats(self, macro: Macro):
        """Update the statistics display."""
        self._stat_keys.setText(f"按键: {macro.key_count}")
        self._stat_duration.setText(f"时长: {macro.duration:.2f}秒")
        self._stat_events.setText(f"事件: {len(macro.events)}")

    # === Recording ===

    def _on_record_toggle(self):
        """Toggle recording state."""
        if self._is_playing:
            self._on_stop_all()
            return

        if self._is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording keyboard input."""
        self._is_recording = True
        self.recorder.start(callback=self.recording_event.emit, suppress=False)
        self._status_label.setText("录制中...")
        self._status_label.setStyleSheet("""
            QLabel {
                font-size: 14px; font-weight: bold;
                color: white; background-color: #e74c3c;
                padding: 4px 12px; border-radius: 4px;
            }
        """)
        self._sb_status.setText("正在录制 - 请按键...")
        self._act_record.setText("停止录制")
        self._tray.set_recording(True)
        self._tray.show_message("录制", "键盘录制已开始，按 Ctrl+Shift+F8 停止。")

    def _stop_recording(self):
        """Stop recording and save the macro."""
        self._is_recording = False
        events = self.recorder.stop()

        # Filter out hotkey keys from recording
        hotkey_keys = self.hotkey_mgr.get_hotkey_keys()
        filtered_events = []
        for e in events:
            if e.key_name.lower() not in hotkey_keys:
                filtered_events.append(e)

        if not filtered_events:
            self._status_label.setText("就绪")
            self._status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold;
                    color: #2c3e50; padding: 4px 12px;
                }
            """)
            self._sb_status.setText("录制取消 - 未捕获到按键事件")
            self._act_record.setText("录制")
            self._tray.set_idle()
            return

        # Create new macro
        macro = Macro(
            name=f"宏_{time.strftime('%H%M%S')}",
            events=filtered_events,
        )
        self._current_macro = macro
        self._macros.append(macro)
        self.macro_manager.save_macro(macro)

        # Update UI
        self._refresh_macro_list()
        self._macro_list.setCurrentRow(self._macro_list.count() - 1)

        self._status_label.setText("就绪")
        self._status_label.setStyleSheet("""
            QLabel {
                font-size: 14px; font-weight: bold;
                color: #2c3e50; padding: 4px 12px;
            }
        """)
        self._sb_status.setText(f"已录制 {macro.key_count} 次按键，时长 {macro.duration:.2f}秒")
        self._act_record.setText("录制")
        self._tray.set_idle()
        self._tray.show_message("录制完成",
                                f"已捕获 {macro.key_count} 次按键，时长 {macro.duration:.2f}秒")

    # === Playback ===

    def _on_play_toggle(self):
        """Toggle playback state."""
        if self._is_recording:
            self._stop_recording()
            return

        if self._is_playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        """Start playing back the selected macro."""
        macro = self._get_selected_macro()
        if not macro or not macro.events:
            self._sb_status.setText("未选中宏或宏为空")
            return

        self._is_playing = True
        loop = 99999 if self._infinite_check.isChecked() else self._loop_spin.value()

        # Set up callbacks
        self.player.set_callbacks(
            progress=self.playback_progress.emit,
            state=self.playback_state.emit,
            key=self.playback_key.emit,
        )

        self.player.play(macro, speed=self._speed, loop_count=loop)

        self._status_label.setText("回放中...")
        self._status_label.setStyleSheet("""
            QLabel {
                font-size: 14px; font-weight: bold;
                color: white; background-color: #27ae60;
                padding: 4px 12px; border-radius: 4px;
            }
        """)
        self._sb_status.setText(f"正在回放「{macro.name}」，速度 {self._speed}x")
        self._act_play.setText("停止回放")
        self._tray.set_playing(True)

    def _stop_playback(self):
        """Stop playback."""
        self.player.stop()
        self._is_playing = False
        self._on_playback_state('stopped')

    def _on_playback_progress(self, current_time, total_time, current_loop, total_loops):
        """Handle playback progress updates."""
        if total_time > 0:
            progress = int(current_time / total_time * 1000)
        else:
            progress = 0
        self._progress_bar.setValue(progress)

        loop_str = f"第 {current_loop}/{total_loops} 轮" if total_loops < 9999 else f"第 {current_loop} 轮"
        self._progress_bar.setFormat(f"{loop_str} - {progress/10:.0f}%")

        # Update time display
        self._time_label.setText(f"{self._format_time(current_time)} / {self._format_time(total_time)}")

        # Update timeline position
        self._timeline.set_playback_position(current_time)

    def _on_playback_state(self, state):
        """Handle playback state changes."""
        if state in ('finished', 'stopped'):
            self._is_playing = False
            self._status_label.setText("就绪")
            self._status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold;
                    color: #2c3e50; padding: 4px 12px;
                }
            """)
            self._progress_bar.setValue(0)
            self._progress_bar.setFormat("未回放")
            self._time_label.setText("00:00.00 / 00:00.00")
            self._timeline.set_playback_position(-1)
            self._act_play.setText("回放")
            self._tray.set_idle()
            state_map = {'finished': '已完成', 'stopped': '已停止'}
            self._sb_status.setText(f"回放{state_map.get(state, state)}")
        elif state == 'playing':
            self._sb_status.setText("回放已开始")

    def _on_playback_key(self, event):
        """Handle individual key playback events (for visual feedback)."""
        pass  # Could highlight keys on a virtual keyboard here

    def _on_recording_event(self, event: KeyEvent):
        """Handle a recorded key event."""
        # Update timeline in real-time during recording
        current_events = self.recorder.events
        self._timeline.set_events(current_events)
        self._sb_status.setText(f"录制中: {event.key_name} ({event.event_type}) @ {event.timestamp:.3f}秒")

    # === Control handlers ===

    def _on_stop_all(self):
        """Stop all active operations."""
        if self._is_recording:
            self._stop_recording()
        if self._is_playing:
            self._stop_playback()

    def _on_speed_changed(self, text):
        """Handle speed change."""
        speed_str = text.replace('x', '')
        try:
            self._speed = float(speed_str)
        except ValueError:
            self._speed = 1.0

    def _on_loop_changed(self, value):
        self._loop_count = value

    def _on_infinite_toggled(self, state):
        self._loop_spin.setEnabled(state == 0)

    def _on_new_macro(self):
        """Create a new empty macro."""
        macro = Macro(name=f"新宏 {len(self._macros) + 1}")
        self._macros.append(macro)
        self.macro_manager.save_macro(macro)
        self._refresh_macro_list()
        self._macro_list.setCurrentRow(self._macro_list.count() - 1)
        self._name_edit.setFocus()
        self._name_edit.selectAll()

    def _on_save_macro(self):
        """Save the current macro."""
        macro = self._get_selected_macro()
        if not macro:
            return

        macro.name = self._name_edit.text().strip() or "未命名"
        macro.description = self._desc_edit.text().strip()
        macro.loop_count = self._loop_spin.value()
        macro.playback_speed = self._speed

        self.macro_manager.save_macro(macro)
        self._refresh_macro_list()
        self._sb_status.setText(f"已保存「{macro.name}」")

    def _on_delete_macro(self):
        """Delete the selected macro."""
        macro = self._get_selected_macro()
        if not macro:
            return

        reply = QMessageBox.question(
            self, "删除宏",
            f"确定要删除「{macro.name}」吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.macro_manager.delete_macro(macro.name)
            self._macros.remove(macro)
            self._refresh_macro_list()
            self._sb_status.setText(f"已删除「{macro.name}」")

    def _on_import_macro(self):
        """Import a macro from a JSON file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入宏", "", "JSON 文件 (*.json)"
        )
        if path:
            macro = self.macro_manager.import_macro(path)
            if macro:
                self._macros.append(macro)
                self.macro_manager.save_macro(macro)
                self._refresh_macro_list()
                self._macro_list.setCurrentRow(self._macro_list.count() - 1)
                self._sb_status.setText(f"已导入「{macro.name}」")
            else:
                QMessageBox.warning(self, "导入失败", "无法从文件导入宏。")

    def _on_export_macro(self):
        """Export the selected macro to a JSON file."""
        macro = self._get_selected_macro()
        if not macro:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出宏", f"{macro.name}.json", "JSON 文件 (*.json)"
        )
        if path:
            self.macro_manager.export_macro(macro, path)
            self._sb_status.setText(f"已导出到 {path}")

    def _on_macro_edited(self):
        """Handle macro name/description edits."""
        macro = self._get_selected_macro()
        if macro:
            macro.name = self._name_edit.text().strip() or "未命名"
            macro.description = self._desc_edit.text().strip()

    def _on_macro_context_menu(self, pos):
        """Show context menu for macro list."""
        item = self._macro_list.itemAt(pos)
        if not item:
            return

        macro = item.data(Qt.UserRole)
        menu = QMenu(self)

        act_play = menu.addAction("回放")
        act_play.triggered.connect(lambda: self._start_playback())

        act_edit = menu.addAction("重命名")
        act_edit.triggered.connect(lambda: self._name_edit.setFocus())

        menu.addSeparator()

        act_export = menu.addAction("导出...")
        act_export.triggered.connect(self._on_export_macro)

        act_delete = menu.addAction("删除")
        act_delete.triggered.connect(self._on_delete_macro)

        menu.exec_(self._macro_list.mapToGlobal(pos))

    # === Tray ===

    def _show_from_tray(self):
        """Show window from tray."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self):
        """Quit the application."""
        self._on_stop_all()
        self.hotkey_mgr.cleanup()
        QApplication.quit()

    # === Window events ===

    def closeEvent(self, event):
        """Minimize to tray on close instead of quitting."""
        event.ignore()
        self.hide()
        self._tray.show_message(
            "键盘宏",
            "程序已最小化到系统托盘，双击托盘图标恢复窗口。"
        )

    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS.ss."""
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m:02d}:{s:05.2f}"

    def _apply_style(self):
        """Apply application-wide styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QToolBar {
                background-color: #2c3e50;
                border: none;
                padding: 4px;
                spacing: 4px;
            }
            QToolBar QLabel {
                color: #ecf0f1;
            }
            QToolBar QComboBox, QToolBar QSpinBox, QToolBar QCheckBox {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QToolBar QComboBox::drop-down {
                border: none;
            }
            QToolBar QComboBox QAbstractItemView {
                background-color: #34495e;
                color: #ecf0f1;
                selection-background-color: #3498db;
            }
            QToolBar QAction {
                color: #ecf0f1;
            }
            QStatusBar {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QStatusBar QLabel {
                color: #ecf0f1;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3498db;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)

        # Style toolbar actions
        for action in self._toolbar.actions():
            widget = self._toolbar.widgetForAction(action)
            if widget:
                widget.setStyleSheet("""
                    QToolButton {
                        color: #ecf0f1;
                        background-color: transparent;
                        border: 1px solid transparent;
                        border-radius: 4px;
                        padding: 4px 10px;
                        font-size: 12px;
                    }
                    QToolButton:hover {
                        background-color: #34495e;
                        border: 1px solid #3498db;
                    }
                    QToolButton:pressed {
                        background-color: #2c3e50;
                    }
                """)
