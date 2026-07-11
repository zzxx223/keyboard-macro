"""
Global hotkey manager.
Registers system-wide hotkeys for controlling record/playback.
Uses the `keyboard` library for low-level global hotkey support.
"""

import threading
import keyboard
from typing import Callable, Optional


# Default hotkey bindings (chosen to minimize conflicts with common macro keys)
DEFAULT_HOTKEYS = {
    'record_start': 'ctrl+shift+f7',
    'record_stop': 'ctrl+shift+f8',
    'play_start': 'ctrl+shift+f9',
    'play_stop': 'ctrl+shift+f10',
}

# Alternative simple F-key hotkeys (for users who prefer simpler bindings)
SIMPLE_HOTKEYS = {
    'record_start': 'f7',
    'record_stop': 'f8',
    'play_start': 'f9',
    'play_stop': 'f10',
}


class GlobalHotkeyManager:
    """Manages global hotkey registration and callbacks."""

    def __init__(self):
        self._hotkeys: dict = {}        # action -> hotkey_string
        self._callbacks: dict = {}       # action -> callback
        self._registered: dict = {}      # action -> registered handle
        self._lock = threading.Lock()
        self._enabled = False

    @property
    def hotkeys(self) -> dict:
        """Get current hotkey bindings."""
        return dict(self._hotkeys)

    def set_hotkey(self, action: str, hotkey: str):
        """Set a hotkey for an action. Re-registers if enabled."""
        with self._lock:
            old = self._hotkeys.get(action)
            if old and self._enabled:
                try:
                    keyboard.remove_hotkey(old)
                except (KeyError, ValueError):
                    pass
                self._registered.pop(action, None)

            self._hotkeys[action] = hotkey
            self._callbacks.setdefault(action, None)

            if self._enabled and self._callbacks.get(action):
                self._register_action(action)

    def set_callback(self, action: str, callback: Callable):
        """Set the callback for an action."""
        with self._lock:
            self._callbacks[action] = callback
            if self._enabled and action in self._hotkeys:
                self._register_action(action)

    def enable(self):
        """Enable all registered hotkeys."""
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            for action in self._hotkeys:
                if self._callbacks.get(action):
                    self._register_action(action)

    def disable(self):
        """Disable all hotkeys."""
        with self._lock:
            if not self._enabled:
                return
            for action, hotkey in list(self._registered.items()):
                try:
                    keyboard.remove_hotkey(hotkey)
                except (KeyError, ValueError):
                    pass
            self._registered.clear()
            self._enabled = False

    def _register_action(self, action: str):
        """Register a single action's hotkey."""
        hotkey = self._hotkeys.get(action)
        callback = self._callbacks.get(action)
        if not hotkey or not callback:
            return

        # Remove old registration if exists
        if action in self._registered:
            try:
                keyboard.remove_hotkey(self._registered[action])
            except (KeyError, ValueError):
                pass

        try:
            handle = keyboard.add_hotkey(hotkey, callback, suppress=False)
            self._registered[action] = hotkey
        except Exception as e:
            print(f"Failed to register hotkey '{hotkey}' for action '{action}': {e}")

    def is_hotkey_key(self, key_name: str, event_type: str = 'down') -> bool:
        """Check if a key name is part of any registered hotkey.
        Used by the recorder to filter out hotkey keys from recordings.
        """
        key_lower = key_name.lower()
        for hotkey_str in self._hotkeys.values():
            parts = [p.strip().lower() for p in hotkey_str.split('+')]
            if key_lower in parts:
                return True
        return False

    def get_hotkey_keys(self) -> set:
        """Get a set of all key names used in hotkey combinations."""
        keys = set()
        for hotkey_str in self._hotkeys.values():
            parts = [p.strip().lower() for p in hotkey_str.split('+')]
            keys.update(parts)
        return keys

    def cleanup(self):
        """Clean up all registered hotkeys."""
        self.disable()
        keyboard.unhook_all()
