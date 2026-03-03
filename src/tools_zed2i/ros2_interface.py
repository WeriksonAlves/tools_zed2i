# src/tools_zed2i/ros2_interface.py
from __future__ import annotations

import threading
from typing import Optional

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Image  # type: ignore

from .config import ZED2iConfig, ROSConfig
from .image_manager import ImageManager
from .state import ZED2iState


class ZED2iNode(Node):
    """
    Low-level ROS2 node for ZED2i integration.

    For this first validation step, this node:
    - Subscribes to left/right/stereo image topics depending on config.
    - Forwards messages to ImageManager.
    """

    def __init__(
        self,
        config: ZED2iConfig,
        state: ZED2iState,
        image_manager: ImageManager,
    ) -> None:
        super().__init__(f"{config.camera.name}_node")
        self._config = config
        self._state = state
        self._image_manager = image_manager

        self._qos = self._build_qos_profile(config.ros)

        self._sub_left: Optional[object] = None
        self._sub_right: Optional[object] = None
        self._sub_stereo: Optional[object] = None

    @staticmethod
    def _build_qos_profile(ros_cfg: ROSConfig) -> QoSProfile:
        reliability_map = {
            "reliable": ReliabilityPolicy.RELIABLE,
            "best_effort": ReliabilityPolicy.BEST_EFFORT,
        }
        durability_map = {
            "volatile": DurabilityPolicy.VOLATILE,
            "transient_local": DurabilityPolicy.TRANSIENT_LOCAL,
        }

        reliability = reliability_map.get(
            ros_cfg.qos_reliability.lower(),
            ReliabilityPolicy.RELIABLE,
        )
        durability = durability_map.get(
            ros_cfg.qos_durability.lower(),
            DurabilityPolicy.VOLATILE,
        )

        return QoSProfile(
            depth=ros_cfg.qos_depth,
            reliability=reliability,
            durability=durability,
        )

    # --------- Subscription control ---------

    def enable_image_subscriptions(self) -> None:
        """
        Create subscriptions for enabled image streams.
        """
        images_cfg = self._config.images

        if images_cfg.use_left and self._sub_left is None:
            self.get_logger().info(f"Subscribing to left image: {images_cfg.left_topic}")
            self._sub_left = self.create_subscription(
                Image,
                images_cfg.left_topic,
                self._left_callback,
                self._qos,
            )

        if images_cfg.use_right and self._sub_right is None:
            self.get_logger().info(
                f"Subscribing to right image: {images_cfg.right_topic}",
            )
            self._sub_right = self.create_subscription(
                Image,
                images_cfg.right_topic,
                self._right_callback,
                self._qos,
            )

        if images_cfg.use_stereo and self._sub_stereo is None:
            self.get_logger().info(
                f"Subscribing to stereo image: {images_cfg.stereo_topic}",
            )
            self._sub_stereo = self.create_subscription(
                Image,
                images_cfg.stereo_topic,
                self._stereo_callback,
                self._qos,
            )

    def disable_image_subscriptions(self) -> None:
        """
        Destroy existing image subscriptions.
        """
        if self._sub_left is not None:
            self.get_logger().info("Disabling left image subscription.")
            self.destroy_subscription(self._sub_left)
            self._sub_left = None

        if self._sub_right is not None:
            self.get_logger().info("Disabling right image subscription.")
            self.destroy_subscription(self._sub_right)
            self._sub_right = None

        if self._sub_stereo is not None:
            self.get_logger().info("Disabling stereo image subscription.")
            self.destroy_subscription(self._sub_stereo)
            self._sub_stereo = None

    # --------- Callbacks ---------

    def _left_callback(self, msg: Image) -> None:
        self._state.increment_frame_counter()
        self._image_manager.update_left(msg)

    def _right_callback(self, msg: Image) -> None:
        self._state.increment_frame_counter()
        self._image_manager.update_right(msg)

    def _stereo_callback(self, msg: Image) -> None:
        self._state.increment_frame_counter()
        self._image_manager.update_stereo(msg)


class ROS2Interface:
    """
    Wrapper around rclpy initialization, executor and node lifecycle.

    This class runs the ROS2 executor in a separate thread to avoid blocking
    the main application.
    """

    def __init__(
        self,
        config: ZED2iConfig,
        state: ZED2iState,
        image_manager: ImageManager,
    ) -> None:
        self._config = config
        self._state = state
        self._image_manager = image_manager

        self._node: Optional[ZED2iNode] = None
        self._executor: Optional[SingleThreadedExecutor] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """
        Initialize rclpy, create the node and start spinning in a new thread.
        """
        with self._lock:
            if self._node is not None:
                return

            rclpy.init()
            self._node = ZED2iNode(
                config=self._config,
                state=self._state,
                image_manager=self._image_manager,
            )
            self._executor = SingleThreadedExecutor()
            self._executor.add_node(self._node)

            self._thread = threading.Thread(
                target=self._spin,
                name="ZED2iROS2Thread",
                daemon=True,
            )
            self._thread.start()
            self._state.mark_ros_running()

    def _spin(self) -> None:
        """
        Spin the executor in a dedicated thread.
        """
        assert self._executor is not None
        try:
            self._executor.spin()
        except Exception as exc:  # pragma: no cover - defensive
            if self._node is not None:
                self._node.get_logger().error(f"Executor error: {exc}")
            self._state.set_error(str(exc))
        finally:
            with self._lock:
                if self._executor is not None:
                    self._executor.shutdown()
                    self._executor = None
                if self._node is not None:
                    self._node.destroy_node()
                    self._node = None
                rclpy.shutdown()
                self._state.mark_ros_stopped()

    def stop(self) -> None:
        """
        Stop the executor and join the thread.
        """
        with self._lock:
            if self._executor is not None:
                self._executor.shutdown()
            if self._thread is not None:
                self._thread.join(timeout=2.0)
                self._thread = None

    # --------- Convenience methods used by ZED2i facade ---------

    def enable_image_subscriptions(self) -> None:
        with self._lock:
            if self._node is None:
                raise RuntimeError("ROS2 node is not initialized.")
            self._node.enable_image_subscriptions()

    def disable_image_subscriptions(self) -> None:
        with self._lock:
            if self._node is None:
                return
            self._node.disable_image_subscriptions()