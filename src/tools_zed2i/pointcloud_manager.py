# src/tools_zed2i/pointcloud_manager.py
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

from .config import ProcessingConfig


@dataclass
class PointCloudManager:
    """
    Manage incoming point clouds from ROS2.

    Responsibilities:
    - Store the last received cloud (raw message or converted structure).
    - Apply basic processing (downsampling, range filtering) in future
        versions.
    - Provide methods to access and save the current cloud.
    """
    config: ProcessingConfig
    _last_cloud: Optional[object] = field(default=None, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def update_from_msg(self, msg: object) -> None:
        """
        Update internal state from a new PointCloud2 message.

        For now this method stores the raw message. Later we can convert it
        to numpy/Open3D using a dedicated converter.
        """
        with self._lock:
            self._last_cloud = msg

    def get_last_cloud(self) -> Optional[object]:
        """
        Return the last stored point cloud (may be None if no data received).
        """
        with self._lock:
            return self._last_cloud

    def save_current_cloud(self, output_path=None):
        """
        Save the current cloud to disk.

        This is intentionally a stub for now. Later we will implement:
        - PointCloud2 -> numpy / Open3D
        - Write to PLY/PCD
        """
        # TODO: implement PLY saving logic here
        raise NotImplementedError("save_current_cloud is not implemented yet.")
