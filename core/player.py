"""
Keyboard player module.
Replays recorded key events with precise timing, speed control, and loop support.
Uses scan codes for layout-independent playback.
"""

import time
import threading
import keyboard
from typing import Callable, Optional, List
from .macro import KeyEvent, Macro


class KeyboardPlayer:
    """Plays back recorded keyboard macros."""

    def __init__(self):
        self._is_playing = False
        self._stop_flag = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._progress_callback: Optional[Callable[[float, float, int, int], None]] = None
        self._state_callback: Optional[Callable[[str], None]] = None
        self._key_callback: Optional[Callable[[KeyEvent], None]] = None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def set_callbacks(
        self,
        progress: Optional[Callable[[float, float, int, int], None]] = None,
        state: Optional[Callable[[str], None]] = None,
        key: Optional[Callable[[KeyEvent], None]] = None,
    ):
        """Set callbacks for progress updates, state changes, and key events.

        Progress callback: (current_time, total_time, current_loop, total_loops)
        State callback: 'playing', 'stopped', 'paused', 'finished'
        Key callback: KeyEvent currently being played
        """
        self._progress_callback = progress
        self._state_callback = state
        self._key_callback = key

    def play(self, macro: Macro, speed: float = 1.0, loop_count: int = 1):
        """Start playing a macro in a background thread.

        Args:
            macro: The macro to play.
            speed: Playback speed multiplier (e.g. 0.5, 1.0, 2.0, 5.0).
            loop_count: Number of times to loop (1 = single play).
        """
        if self._is_playing:
            self.stop()

        self._is_playing = True
        self._stop_flag.clear()

        self._thread = threading.Thread(
            target=self._play_thread,
            args=(macro.events, speed, max(1, loop_count)),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Stop playback."""
        if not self._is_playing:
            return

        self._stop_flag.set()
        self._is_playing = False

        if self._state_callback:
            self._state_callback('stopped')

        # Release all keys to prevent stuck keys
        try:
            keyboard.release('shift')
            keyboard.release('ctrl')
            keyboard.release('alt')
            keyboard.release('left windows')
            keyboard.release('right windows')
        except Exception:
            pass

    def _play_thread(self, events: List[KeyEvent], speed: float, loop_count: int):
        """Internal playback thread."""
        if not events:
            self._is_playing = False
            if self._state_callback:
                self._state_callback('finished')
            return

        if self._state_callback:
            self._state_callback('playing')

        total_duration = events[-1].timestamp

        for loop_idx in range(loop_count):
            if self._stop_flag.is_set():
                break

            prev_time = 0.0

            for i, event in enumerate(events):
                if self._stop_flag.is_set():
                    break

                # Calculate delay: time difference from previous event, adjusted by speed
                delay = (event.timestamp - prev_time) / speed
                if delay > 0:
                    # Sleep in small increments to allow responsive stopping
                    self._interruptible_sleep(delay)

                if self._stop_flag.is_set():
                    break

                # Simulate the key event using scan code for layout independence
                self._send_event(event)

                if self._key_callback:
                    try:
                        self._key_callback(event)
                    except Exception:
                        pass

                prev_time = event.timestamp

                # Progress callback
                if self._progress_callback:
                    try:
                        self._progress_callback(
                            event.timestamp,
                            total_duration,
                            loop_idx + 1,
                            loop_count,
                        )
                    except Exception:
                        pass

            # Pause between loops (0.5s gap)
            if loop_idx < loop_count - 1 and not self._stop_flag.is_set():
                self._interruptible_sleep(0.5 / speed)

        self._is_playing = False

        if not self._stop_flag.is_set():
            if self._state_callback:
                self._state_callback('finished')

    def _interruptible_sleep(self, duration: float, check_interval: float = 0.01):
        """Sleep that can be interrupted by stop_flag. Checks every check_interval seconds."""
        elapsed = 0.0
        while elapsed < duration:
            if self._stop_flag.is_set():
                return
            sleep_time = min(check_interval, duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time

    def _send_event(self, event: KeyEvent):
        """Send a single key event using scan code for layout independence."""
        try:
            if event.scan_code and event.scan_code > 0:
                # Use scan code for layout-independent playback
                # keyboard.press/release accept scan codes with is_extended flag
                is_extended = (event.scan_code >= 0x100)

                if event.event_type == 'down':
                    keyboard.press(event.scan_code)
                else:
                    keyboard.release(event.scan_code)
            else:
                # Fallback to key name if no scan code
                if event.event_type == 'down':
                    keyboard.press(event.key_name)
                else:
                    keyboard.release(event.key_name)
        except Exception as e:
            # Try fallback with key name
            try:
                if event.event_type == 'down':
                    keyboard.press(event.key_name)
                else:
                    keyboard.release(event.key_name)
            except Exception:
                pass
