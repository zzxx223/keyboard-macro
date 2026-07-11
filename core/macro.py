"""
Macro data model and manager.
Handles macro storage, loading, import/export (JSON).
"""

import json
import time
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class KeyEvent:
    """Represents a single keyboard event (key press or release)."""
    key_name: str           # Human-readable key name (e.g. 'a', 'shift', 'ctrl+alt+del')
    scan_code: int          # Hardware scan code (layout-independent)
    event_type: str         # 'down' (press) or 'up' (release)
    timestamp: float        # Relative time from recording start (seconds)
    is_modifier: bool = False  # Whether this key is a modifier (ctrl, shift, alt, win)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'KeyEvent':
        return cls(
            key_name=d['key_name'],
            scan_code=d['scan_code'],
            event_type=d['event_type'],
            timestamp=d['timestamp'],
            is_modifier=d.get('is_modifier', False),
        )


@dataclass
class Macro:
    """A recorded macro containing a sequence of key events."""
    name: str
    events: List[KeyEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    description: str = ""
    loop_count: int = 1         # Default loop count
    playback_speed: float = 1.0  # Default playback speed multiplier

    @property
    def duration(self) -> float:
        """Total duration of the macro in seconds."""
        if not self.events:
            return 0.0
        return self.events[-1].timestamp

    @property
    def key_count(self) -> int:
        """Number of key press events."""
        return sum(1 for e in self.events if e.event_type == 'down')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'events': [e.to_dict() for e in self.events],
            'created_at': self.created_at,
            'description': self.description,
            'loop_count': self.loop_count,
            'playback_speed': self.playback_speed,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Macro':
        return cls(
            name=d['name'],
            events=[KeyEvent.from_dict(e) for e in d.get('events', [])],
            created_at=d.get('created_at', time.time()),
            description=d.get('description', ''),
            loop_count=d.get('loop_count', 1),
            playback_speed=d.get('playback_speed', 1.0),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'Macro':
        return cls.from_dict(json.loads(json_str))


class MacroManager:
    """Manages saving, loading, importing, and exporting macros."""

    # JSON format version for forward compatibility
    FORMAT_VERSION = "1.0"

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _macro_path(self, macro_name: str) -> str:
        """Get the file path for a macro."""
        safe_name = "".join(c for c in macro_name if c not in r'\/:*?"<>|') or "untitled"
        return os.path.join(self.storage_dir, f"{safe_name}.json")

    def save_macro(self, macro: Macro) -> str:
        """Save a macro to storage. Returns the file path."""
        path = self._macro_path(macro.name)
        data = {
            'format_version': self.FORMAT_VERSION,
            'macro': macro.to_dict(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def load_macro(self, macro_name: str) -> Optional[Macro]:
        """Load a macro from storage by name."""
        path = self._macro_path(macro_name)
        if not os.path.exists(path):
            return None
        return self.load_from_file(path)

    def load_from_file(self, file_path: str) -> Optional[Macro]:
        """Load a macro from a specific file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'macro' in data:
                return Macro.from_dict(data['macro'])
            return Macro.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading macro from {file_path}: {e}")
            return None

    def delete_macro(self, macro_name: str) -> bool:
        """Delete a macro from storage."""
        path = self._macro_path(macro_name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_macros(self) -> List[str]:
        """List all saved macro names."""
        macros = []
        if os.path.exists(self.storage_dir):
            for f in os.listdir(self.storage_dir):
                if f.endswith('.json'):
                    macros.append(f[:-5])  # Remove .json extension
        return sorted(macros)

    def load_all(self) -> List[Macro]:
        """Load all macros from storage."""
        macros = []
        for name in self.list_macros():
            macro = self.load_macro(name)
            if macro:
                macros.append(macro)
        return macros

    def export_macro(self, macro: Macro, file_path: str) -> str:
        """Export a macro to a JSON file. Returns the file path."""
        data = {
            'format_version': self.FORMAT_VERSION,
            'exported_at': time.time(),
            'macro': macro.to_dict(),
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def import_macro(self, file_path: str) -> Optional[Macro]:
        """Import a macro from a JSON file."""
        return self.load_from_file(file_path)
