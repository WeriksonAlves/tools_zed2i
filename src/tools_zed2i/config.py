# src/tools_zed2i/config.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class CameraConfig:
    """Camera-related configuration loaded from YAML."""
    name: str
    namespace: str


@dataclass
class ImageStreamsConfig:
    """
    Configuration for ZED2i image streams.

    Defines which streams are active and their topics.
    """
    use_left: bool
    use_right: bool
    use_stereo: bool

    left_topic: str
    right_topic: str
    stereo_topic: str

    record: bool
    output_dir: Path
    filename_prefix: str


@dataclass
class ProcessingConfig:
    """Point cloud processing configuration (reserved for future use)."""
    enable_downsampling: bool
    voxel_size: float
    max_range: float


@dataclass
class IOConfig:
    """Input/output configuration for point cloud handling (future use)."""
    save_to_disk: bool
    output_dir: Path
    filename_prefix: str


@dataclass
class ROSConfig:
    """ROS-related configuration (QoS etc.)."""
    qos_depth: int
    qos_reliability: str
    qos_durability: str


@dataclass
class ZED2iConfig:
    """
    Top-level configuration container for the ZED2i toolkit.

    For this first validation step we focus on:
    - camera
    - images
    - ros
    """
    camera: CameraConfig
    images: ImageStreamsConfig
    processing: ProcessingConfig
    io: IOConfig
    ros: ROSConfig

    # --------- YAML loading helpers ---------

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> ZED2iConfig:
        """
        Load configuration from a YAML file, applying presets if present.

        Parameters
        ----------
        yaml_path : str or Path
            Path to the YAML configuration file.

        Returns
        -------
        ZED2iConfig
            Parsed configuration object.
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.is_file():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with yaml_path.open("r", encoding="utf-8") as f:
            raw: Dict[str, Any] = yaml.safe_load(f)

        if raw is None:
            raise ValueError(f"Empty configuration file: {yaml_path}")

        base_cfg = cls._apply_presets(raw)

        camera_cfg = cls._parse_camera(base_cfg.get("camera", {}))
        images_cfg = cls._parse_images(base_cfg.get("images", {}))
        processing_cfg = cls._parse_processing(base_cfg.get("processing", {}))
        io_cfg = cls._parse_io(base_cfg.get("io", {}))
        ros_cfg = cls._parse_ros(base_cfg.get("ros", {}))

        return cls(
            camera=camera_cfg,
            images=images_cfg,
            processing=processing_cfg,
            io=io_cfg,
            ros=ros_cfg,
        )

    @staticmethod
    def _apply_presets(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply presets defined under 'presets' and listed in 'active_presets'
        (or 'pc_preset' / 'hw_preset' for compatibility).
        """
        base_cfg: Dict[str, Any] = dict(raw)

        presets = base_cfg.get("presets", {}) or {}
        if not isinstance(presets, dict):
            presets = {}

        active = (
            base_cfg.get("active_presets")
            or base_cfg.get("pc_preset")
            or base_cfg.get("hw_preset")
        )

        if active is None or active == "":
            return base_cfg

        if isinstance(active, str):
            active_list: List[str] = [
                item.strip() for item in active.split(",") if item.strip()
            ]
        elif isinstance(active, list):
            active_list = [str(item).strip() for item in active if str(item).strip()]
        else:
            raise ValueError(
                "active_presets must be a string or a list of strings, "
                f"got type: {type(active)}",
            )

        base_cfg.pop("presets", None)
        base_cfg.pop("active_presets", None)
        base_cfg.pop("pc_preset", None)
        base_cfg.pop("hw_preset", None)

        for preset_name in active_list:
            preset_cfg = presets.get(preset_name)
            if preset_cfg is None or not isinstance(preset_cfg, dict):
                continue
            ZED2iConfig._deep_update(base_cfg, preset_cfg)

        return base_cfg

    @staticmethod
    def _deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Recursively update a nested dictionary in-place.
        """
        for key, value in updates.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ZED2iConfig._deep_update(base[key], value)
            else:
                base[key] = value

    # --------- Section parsers ---------

    @staticmethod
    def _parse_camera(data: Dict[str, Any]) -> CameraConfig:
        return CameraConfig(
            name=str(data.get("name", "zed2i")),
            namespace=str(data.get("namespace", "")),
        )

    @staticmethod
    def _parse_images(data: Dict[str, Any]) -> ImageStreamsConfig:
        output_dir_str = data.get("output_dir", "./data/images")
        output_dir = Path(str(output_dir_str)).expanduser()

        return ImageStreamsConfig(
            use_left=bool(data.get("use_left", True)),
            use_right=bool(data.get("use_right", False)),
            use_stereo=bool(data.get("use_stereo", False)),
            left_topic=str(
                data.get(
                    "left_topic",
                    "/zed2i/zed_node/left/image_rect_color",
                ),
            ),
            right_topic=str(
                data.get(
                    "right_topic",
                    "/zed2i/zed_node/right/image_rect_color",
                ),
            ),
            stereo_topic=str(
                data.get(
                    "stereo_topic",
                    "/zed2i/zed_node/rgb/image_rect_color",
                ),
            ),
            record=bool(data.get("record", False)),
            output_dir=output_dir,
            filename_prefix=str(data.get("filename_prefix", "zed_")),
        )

    @staticmethod
    def _parse_processing(data: Dict[str, Any]) -> ProcessingConfig:
        return ProcessingConfig(
            enable_downsampling=bool(data.get("enable_downsampling", False)),
            voxel_size=float(data.get("voxel_size", 0.05)),
            max_range=float(data.get("max_range", 30.0)),
        )

    @staticmethod
    def _parse_io(data: Dict[str, Any]) -> IOConfig:
        output_dir_str = data.get("output_dir", "./data/ply")
        output_dir = Path(str(output_dir_str)).expanduser()
        return IOConfig(
            save_to_disk=bool(data.get("save_to_disk", False)),
            output_dir=output_dir,
            filename_prefix=str(data.get("filename_prefix", "zed_frame_")),
        )

    @staticmethod
    def _parse_ros(data: Dict[str, Any]) -> ROSConfig:
        return ROSConfig(
            qos_depth=int(data.get("qos_depth", 5)),
            qos_reliability=str(data.get("qos_reliability", "reliable")),
            qos_durability=str(data.get("qos_durability", "volatile")),
        )
