# src/tools_zed2i/image_manager.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Optional

from .config import ImageStreamsConfig


@dataclass
class ImageManager:
    """
    Manage incoming image streams from ZED2i.

    For now this class:
    - Stores the last left/right/stereo messages (sensor_msgs.msg.Image).
    - Provides simple getters so the user can access the latest frames.
    - Has a stub for saving images to disk.
    """
    config: ImageStreamsConfig
    _last_left: Optional[object] = field(default=None, init=False)
    _last_right: Optional[object] = field(default=None, init=False)
    _last_stereo: Optional[object] = field(default=None, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def update_left(self, msg: object) -> None:
        with self._lock:
            self._last_left = msg

    def update_right(self, msg: object) -> None:
        with self._lock:
            self._last_right = msg

    def update_stereo(self, msg: object) -> None:
        with self._lock:
            self._last_stereo = msg

    def get_last_left(self) -> Optional[object]:
        with self._lock:
            return self._last_left

    def get_last_right(self) -> Optional[object]:
        with self._lock:
            return self._last_right

    def get_last_stereo(self) -> Optional[object]:
        with self._lock:
            return self._last_stereo

    def ensure_output_dir(self) -> None:
        """
        Create the output directory if recording is enabled.
        """
        if not self.config.record:
            return

        output_dir: Path = self.config.output_dir
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

    def save_placeholder_frame(self, frame_index: int) -> Optional[Path]:
        """
        Placeholder implementation for saving frames.

        For now this only creates a small text file so we can validate
        that the recording logic and directory handling work correctly.
        """
        if not self.config.record:
            return None

        self.ensure_output_dir()
        filename = f"{self.config.filename_prefix}{frame_index:06d}.txt"
        output_path = self.config.output_dir / filename

        with output_path.open("w", encoding="utf-8") as f:
            f.write("# Placeholder for image frame.\n")

        return output_path
