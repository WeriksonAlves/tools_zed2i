# src/tools_zed2i/state.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ZED2iState:
    """
    Container for internal state and flags.

    This is intentionally simple and focused on readability and testability.
    """
    initialized: bool = False
    ros_running: bool = False
    pointcloud_stream_enabled: bool = False
    frame_counter: int = 0
    last_error: str | None = None

    def mark_initialized(self) -> None:
        self.initialized = True

    def mark_stopped(self) -> None:
        self.initialized = False
        self.ros_running = False
        self.pointcloud_stream_enabled = False

    def mark_ros_running(self) -> None:
        self.ros_running = True

    def mark_ros_stopped(self) -> None:
        self.ros_running = False

    def increment_frame_counter(self) -> None:
        self.frame_counter += 1

    def set_error(self, message: str) -> None:
        self.last_error = message
