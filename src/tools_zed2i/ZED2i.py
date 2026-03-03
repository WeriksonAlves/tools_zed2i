# src/tools_zed2i/ZED2i.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import ZED2iConfig
from .image_manager import ImageManager
from .ros2_interface import ROS2Interface
from .state import ZED2iState


class ZED2i:
    """
    High-level facade for ZED2i integration.

    For this validation step, it focuses on image streams (left/right/stereo)
    running on top of a ROS2 interface in a background thread.
    """

    def __init__(
        self,
        config: ZED2iConfig,
        ros2_interface: Optional[ROS2Interface] = None,
    ) -> None:
        self._config = config
        self._state = ZED2iState()
        self._image_manager = ImageManager(config=config.images)

        self._ros = ros2_interface or ROS2Interface(
            config=config,
            state=self._state,
            image_manager=self._image_manager,
        )

    # --------- Construction helpers ---------

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> ZED2i:
        """
        Create a ZED2i instance from a YAML configuration file.
        """
        config = ZED2iConfig.from_yaml(yaml_path)
        return cls(config=config)

    # --------- Lifecycle management ---------

    def start(self) -> None:
        """
        Start ROS2 interface (non-blocking) and mark the system as initialized.
        """
        self._ros.start()
        self._state.mark_initialized()

    def stop(self) -> None:
        """
        Stop ROS2 interface and mark the system as stopped.
        """
        self._ros.stop()
        self._state.mark_stopped()

    # --------- Image streaming control ---------

    def start_image_streams(self) -> None:
        """
        Enable configured image subscriptions.
        """
        self._ros.enable_image_subscriptions()
        self._state.pointcloud_stream_enabled = True  # reuse flag name for now

    def stop_image_streams(self) -> None:
        """
        Disable image subscriptions.
        """
        self._ros.disable_image_subscriptions()
        self._state.pointcloud_stream_enabled = False

    # --------- Data access ---------

    def get_last_left_image(self):
        """Return the last left image message (or None)."""
        return self._image_manager.get_last_left()

    def get_last_right_image(self):
        """Return the last right image message (or None)."""
        return self._image_manager.get_last_right()

    def get_last_stereo_image(self):
        """Return the last stereo/combined image message (or None)."""
        return self._image_manager.get_last_stereo()

    def save_placeholder_frame(self, frame_index: int) -> Optional[Path]:
        """
        Save a placeholder frame to disk if recording is enabled.

        This is only for validating that the recording path and flags work.
        """
        return self._image_manager.save_placeholder_frame(frame_index)

    # --------- Introspection helpers ---------

    @property
    def state(self) -> ZED2iState:
        """Return the internal state object (read-only usage recommended)."""
        return self._state

    @property
    def config(self) -> ZED2iConfig:
        """Return the configuration associated with this instance."""
        return self._config
