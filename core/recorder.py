"""
Keyboard recorder module.
Uses the `keyboard` library to hook into low-level keyboard events.
Records key press/release with scan codes for layout independence.
"""

import time
import threading
import keyboard
from typing import Callable, Optional, List
from .macro import KeyEvent, Macro

# Modifier key scan codes and names for detection
MODIFIER_KEYS = {
    'shift', 'left shift', 'right shift',
    'ctrl', 'left ctrl', 'right ctrl',
    'alt', 'left alt', 'right alt', 'alt gr',
    'windows', 'left windows', 'right windows',
}

# Normalize key names: keyboard library uses lowercase names
MODIFIER_NAMES_NORMALIZED = {
    'left shift': 'shift', 'right shift': 'shift',
    'left ctrl': 'ctrl', 'right ctrl': 'ctrl',
    'left alt': 'alt', 'right alt': 'alt', 'alt gr': 'alt',
    'left windows': 'win', 'right windows': 'win',
}


class KeyboardRecorder:
    """Records keyboard events in real-time."""

    def __init__(self):
        self._is_recording = False
        self._events: List[KeyEvent] = []
        self._start_time: float = 0.0
        self._hook = None
        self._lock = threading.Lock()
        self._callback: Optional[Callable] = None
        # Keys to suppress during recording (prevent them from reaching other apps)
        self._suppress_keys = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def events(self) -> List[KeyEvent]:
        with self._lock:
            return list(self._events)

    def start(self, callback: Optional[Callable[[KeyEvent], None]] = None, suppress: bool = False):
        """Start recording keyboard events."""
        if self._is_recording:
            return

        self._is_recording = True
        self._events = []
        self._start_time = time.time()
        self._callback = callback
        self._suppress_keys = suppress

        # Hook all keyboard events
        self._hook = keyboard.hook(self._on_event, suppress=suppress)

    def stop(self) -> List[KeyEvent]:
        """Stop recording and return the recorded events."""
        if not self._is_recording:
            return []

        self._is_recording = False

        if self._hook:
            keyboard.unhook(self._hook)
            self._hook = None

        with self._lock:
            events = list(self._events)
            self._events = []

        return events

    def _on_event(self, event):
        """Callback for keyboard events."""
        if not self._is_recording:
            return

        # Skip the stop recording hotkey itself
        key_name = event.name.lower() if event.name else ''
        event_type = event.event_type  # 'down' or 'up'

        # Normalize modifier names
        normalized_name = MODIFIER_NAMES_NORMALIZED.get(key_name, key_name)
        is_modifier = normalized_name in MODIFIER_KEYS or key_name in MODIFIER_KEYS

        ke = KeyEvent(
            key_name=normalized_name,
            scan_code=event.scan_code if hasattr(event, 'scan_code') else 0,
            event_type=event_type,
            timestamp=time.time() - self._start_time,
            is_modifier=is_modifier,
        )

        with self._lock:
            self._events.append(ke)

        # Notify callback
        if self._callback:
            try:
                self._callback(ke)
            except Exception:
                pass

    def get_macro(self, name: str = "New Macro") -> Macro:
        """Create a Macro from the current recording."""
        return Macro(name=name, events=self.events)

    def clear(self):
        """Clear recorded events without stopping."""
        with self._lock:
            self._events = []
