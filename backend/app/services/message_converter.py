"""
ROS2 消息与字典的双向转换
处理消息序列化（ROS→dict）和反序列化（dict→ROS）
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rosbridge import RosbridgeService

logger = logging.getLogger(__name__)


class MessageConverter:
    """ROS2 消息与 Python 字典的双向转换器"""

    def __init__(self, service: RosbridgeService):
        self._svc = service

    def to_dict(self, msg) -> dict:
        """将 ROS 消息转换为字典"""
        try:
            import numpy as np
            from builtin_interfaces.msg import Time, Duration
            from geometry_msgs.msg import (
                Point,
                Pose,
                PoseWithCovariance,
                Quaternion,
            )
            from sensor_msgs.msg import PointCloud2, Image, CompressedImage
            from std_msgs.msg import Header

            # 特殊处理点云数据
            if isinstance(msg, PointCloud2):
                return self.process_pointcloud(msg)

            # 特殊处理图像数据
            if isinstance(msg, Image):
                return self.process_image(msg)

            # 特殊处理压缩图像数据
            if isinstance(msg, CompressedImage):
                return self.process_compressed_image(msg)

            if hasattr(msg, "__slots__"):
                result = {}
                for slot in msg.__slots__:
                    value = getattr(msg, slot)
                    field_name = slot.removeprefix("_")

                    # 处理时间类型
                    if isinstance(value, Time):
                        result[field_name] = {
                            "sec": int(value.sec),
                            "nanosec": int(value.nanosec),
                        }
                    elif isinstance(value, Duration):
                        result[field_name] = {
                            "sec": int(value.sec),
                            "nanosec": int(value.nanosec),
                        }
                    # 处理Header
                    elif isinstance(value, Header):
                        result[field_name] = {
                            "stamp": {
                                "sec": int(value.stamp.sec),
                                "nanosec": int(value.stamp.nanosec),
                            },
                            "frame_id": str(value.frame_id),
                        }
                    # 处理几何类型
                    elif isinstance(value, Point):
                        result[field_name] = {
                            "x": float(value.x),
                            "y": float(value.y),
                            "z": float(value.z),
                        }
                    elif isinstance(value, Quaternion):
                        result[field_name] = {
                            "x": float(value.x),
                            "y": float(value.y),
                            "z": float(value.z),
                            "w": float(value.w),
                        }
                    elif isinstance(value, Pose):
                        result[field_name] = {
                            "position": {
                                "x": float(value.position.x),
                                "y": float(value.position.y),
                                "z": float(value.position.z),
                            },
                            "orientation": {
                                "x": float(value.orientation.x),
                                "y": float(value.orientation.y),
                                "z": float(value.orientation.z),
                                "w": float(value.orientation.w),
                            },
                        }
                    elif isinstance(value, PoseWithCovariance):
                        result[field_name] = {
                            "pose": {
                                "position": {
                                    "x": float(value.pose.position.x),
                                    "y": float(value.pose.position.y),
                                    "z": float(value.pose.position.z),
                                },
                                "orientation": {
                                    "x": float(value.pose.orientation.x),
                                    "y": float(value.pose.orientation.y),
                                    "z": float(value.pose.orientation.z),
                                    "w": float(value.pose.orientation.w),
                                },
                            },
                            "covariance": (
                                [float(c) for c in value.covariance]
                                if hasattr(value, "covariance")
                                else []
                            ),
                        }
                    # 处理numpy数组
                    elif isinstance(value, np.ndarray):
                        if value.dtype == np.uint8:
                            result[field_name] = value.tolist()
                        else:
                            result[field_name] = value.astype(float).tolist()
                    # 处理bytes类型（点云数据等）
                    elif isinstance(value, bytes):
                        # 对于大型bytes数据，使用Base64编码
                        if len(value) > 1000:
                            import base64

                            result[field_name] = base64.b64encode(value).decode("ascii")
                            result[f"{field_name}_encoding"] = "base64"
                        else:
                            result[field_name] = list(value)  # 小数据直接转换为数组
                    # 处理嵌套消息
                    elif hasattr(value, "__slots__"):
                        result[field_name] = self.to_dict(value)
                    # 处理列表
                    elif isinstance(value, list):
                        result[field_name] = [
                            (
                                self.to_dict(item)
                                if hasattr(item, "__slots__")
                                else (
                                    float(item)
                                    if isinstance(item, (int, float, np.number))
                                    else item
                                )
                            )
                            for item in value
                        ]
                    # 处理基本数值类型
                    elif isinstance(value, (int, float, np.number)):
                        result[field_name] = (
                            float(value)
                            if isinstance(value, (float, np.floating))
                            else int(value)
                        )
                    # 处理字符串和其他类型
                    else:
                        result[field_name] = str(value) if value is not None else None

                return result
            else:
                return {"data": str(msg)}
        except Exception as e:
            logger.error(f"Failed to convert message to dict: {e}")
            return {"error": str(e), "message_type": type(msg).__name__}

    def from_dict(self, msg_class, data: dict):
        """将字典递归转换为ROS消息实例（按公开属性名赋值，兼容私有__slots__）。"""
        try:
            msg = msg_class()

            def assign_by_public_fields(obj, value_dict):
                if not isinstance(value_dict, dict):
                    return
                for key, val in value_dict.items():
                    if not hasattr(obj, key):
                        raise ValueError(f"{type(obj).__name__} 不包含消息字段 {key}")
                    current_attr = getattr(obj, key)

                    # 嵌套消息对象
                    if hasattr(current_attr, "__slots__") and isinstance(val, dict):
                        assign_by_public_fields(current_attr, val)
                        continue

                    # 若需要新建子对象（极少情况）
                    if isinstance(val, dict) and hasattr(
                        type(current_attr), "__slots__"
                    ):
                        try:
                            sub = type(current_attr)()
                            assign_by_public_fields(sub, val)
                            setattr(obj, key, sub)
                            continue
                        except Exception:
                            pass

                    # 列表/数组字段（如covariance）
                    if isinstance(val, list):
                        # 特殊处理协方差：必须是长度36的float序列
                        if key == "covariance":
                            if len(val) != 36:
                                raise ValueError("covariance 必须包含 36 个数值")
                            floats = [float(x) for x in val]
                            try:
                                setattr(obj, key, floats)
                            except Exception as error:
                                raise ValueError(
                                    f"无法设置 {type(obj).__name__}.{key}"
                                ) from error
                            continue

                        # 其他列表，尽量转float（数值型）后设置
                        try:
                            coerced = [
                                float(x) if isinstance(x, (int, float)) else x
                                for x in val
                            ]
                            setattr(obj, key, coerced)
                        except Exception as error:
                            raise ValueError(
                                f"无法设置 {type(obj).__name__}.{key}"
                            ) from error
                        continue

                    # 基本类型
                    try:
                        if isinstance(current_attr, float) and isinstance(
                            val, (int, float)
                        ):
                            val = float(val)
                        setattr(obj, key, val)
                    except Exception as error:
                        raise ValueError(
                            f"无法设置 {type(obj).__name__}.{key}"
                        ) from error

            # 顶层赋值（包含header/pose等）
            assign_by_public_fields(msg, data)
            return msg
        except Exception as e:
            logger.error(
                f"Failed to build message {msg_class.__name__}: {e}", exc_info=True
            )
            return None

    def process_pointcloud(self, pointcloud_msg) -> dict:
        """处理点云数据，保留完整 PointCloud2 二进制数据"""
        try:
            # 解析点云字段
            fields = []
            for field in pointcloud_msg.fields:
                fields.append(
                    {
                        "name": field.name,
                        "offset": field.offset,
                        "datatype": field.datatype,
                        "count": field.count,
                    }
                )

            # 基本信息
            result = {
                "header": self.to_dict(pointcloud_msg.header),
                "height": pointcloud_msg.height,
                "width": pointcloud_msg.width,
                "fields": fields,
                "is_bigendian": pointcloud_msg.is_bigendian,
                "point_step": pointcloud_msg.point_step,
                "row_step": pointcloud_msg.row_step,
                "is_dense": pointcloud_msg.is_dense,
            }

            # 处理点云数据
            if len(pointcloud_msg.data) > 0:
                max_bytes = self._svc.settings.ros_pointcloud_max_bytes
                if len(pointcloud_msg.data) > max_bytes:
                    return {
                        **result,
                        "error": (
                            f"PointCloud2 数据为 {len(pointcloud_msg.data)} 字节，"
                            f"超过上限 {max_bytes} 字节"
                        ),
                        "data": [],
                        "data_encoding": "array",
                    }
                logger.debug(
                    "Processing pointcloud data - Total bytes: %s, Point step: %s",
                    len(pointcloud_msg.data),
                    pointcloud_msg.point_step,
                )

                total_points = pointcloud_msg.width * pointcloud_msg.height

                logger.debug(
                    "Pointcloud info - Width: %s, Height: %s, Total points: %s",
                    pointcloud_msg.width,
                    pointcloud_msg.height,
                    total_points,
                )

                # 对于大型数据使用Base64编码，小型数据直接传输。这里不做点采样，避免地图在前端显示成被截断/抽稀。
                if len(pointcloud_msg.data) > 10000:  # 大于10KB使用Base64
                    import base64

                    result["data"] = base64.b64encode(pointcloud_msg.data).decode(
                        "ascii"
                    )
                    result["data_encoding"] = "base64"
                    logger.debug(
                        "Full pointcloud transmission - %s bytes, %s points, Base64 encoded",
                        len(pointcloud_msg.data),
                        total_points,
                    )
                else:
                    result["data"] = list(pointcloud_msg.data)
                    result["data_encoding"] = "array"
                    logger.debug(
                        "Full pointcloud transmission - %s bytes, %s points, as array",
                        len(pointcloud_msg.data),
                        total_points,
                    )

                result["sampled"] = False
                result["original_points"] = total_points
                result["sample_step"] = 1
            else:
                result["data"] = []
                result["data_encoding"] = "array"
                result["sampled"] = False
                logger.warning("Pointcloud data is empty")

            return result

        except Exception as e:
            logger.error(f"Failed to process pointcloud data: {e}")
            return {
                "header": self.to_dict(pointcloud_msg.header),
                "error": str(e),
                "data": [],
            }

    def process_image(self, image_msg) -> dict:
        """处理图像数据，进行压缩优化"""
        try:
            result = {
                "header": self.to_dict(image_msg.header),
                "height": image_msg.height,
                "width": image_msg.width,
                "encoding": image_msg.encoding,
                "is_bigendian": image_msg.is_bigendian,
                "step": image_msg.step,
            }

            data_size = len(image_msg.data)
            max_bytes = self._svc.settings.ros_image_max_bytes
            if data_size > max_bytes:
                result["error"] = (
                    f"Image 数据为 {data_size} 字节，超过上限 {max_bytes} 字节"
                )
                result["data"] = []
                result["data_encoding"] = "array"
            elif data_size > 10_000:
                import base64

                result["data"] = base64.b64encode(image_msg.data).decode("ascii")
                result["data_encoding"] = "base64"
            else:
                result["data"] = list(image_msg.data)
                result["data_encoding"] = "array"

            return result

        except Exception as e:
            logger.error(f"Failed to process image data: {e}")
            return {
                "header": self.to_dict(image_msg.header),
                "error": str(e),
                "data": [],
            }

    def process_compressed_image(self, image_msg) -> dict:
        """处理压缩图像数据"""
        try:
            result = {
                "header": self.to_dict(image_msg.header),
                "format": image_msg.format,
                "compressed": True,
            }

            data_size = len(image_msg.data)
            max_bytes = self._svc.settings.ros_image_max_bytes
            if data_size > max_bytes:
                result["error"] = (
                    f"CompressedImage 数据为 {data_size} 字节，"
                    f"超过上限 {max_bytes} 字节"
                )
                result["data"] = []
                result["data_encoding"] = "array"
            elif data_size > 10000:
                import base64

                result["data"] = base64.b64encode(image_msg.data).decode("ascii")
                result["data_encoding"] = "base64"
            else:
                result["data"] = list(image_msg.data)
                result["data_encoding"] = "array"

            return result

        except Exception as e:
            logger.error(f"Failed to process compressed image data: {e}")
            return {
                "header": self.to_dict(image_msg.header),
                "error": str(e),
                "data": [],
            }
