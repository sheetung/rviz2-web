from types import SimpleNamespace
from unittest.mock import Mock

from geometry_msgs.msg import Pose, PoseStamped, PoseWithCovarianceStamped, Twist

from app.services.message_converter import MessageConverter
from app.services.rosbridge import RosbridgeService


def test_ros_message_slots_are_exposed_as_public_field_names():
    message = PoseStamped()
    message.header.frame_id = "map"
    message.pose.position.x = 1.5

    service = object.__new__(RosbridgeService)
    result = service._message_to_dict(message)

    assert result["header"]["frame_id"] == "map"
    assert result["pose"]["position"]["x"] == 1.5
    assert all(not key.startswith("_") for key in result)
    assert all(not key.startswith("_") for key in result["header"])
    assert all(not key.startswith("_") for key in result["pose"])


def test_pose_stamped_dictionary_preserves_all_position_axes():
    service = object.__new__(RosbridgeService)
    result = service._dict_to_message(
        PoseStamped,
        {
            "header": {"frame_id": "world"},
            "pose": {
                "position": {"x": 16, "y": 0, "z": 0.6},
                "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            },
        },
    )

    assert result.pose.position.x == 16.0
    assert result.pose.position.y == 0.0
    assert result.pose.position.z == 0.6


def test_integer_json_values_are_coerced_for_other_ros_float_fields():
    service = object.__new__(RosbridgeService)

    pose = service._dict_to_message(
        Pose,
        {
            "position": {"x": 1, "y": 0, "z": -2},
            "orientation": {"x": 0, "y": 0, "z": 0, "w": 1},
        },
    )
    twist = service._dict_to_message(
        Twist,
        {
            "linear": {"x": 2, "y": 0, "z": -1},
            "angular": {"x": 0, "y": 0, "z": 1},
        },
    )
    initial_pose = service._dict_to_message(
        PoseWithCovarianceStamped,
        {
            "pose": {
                "pose": {
                    "position": {"x": 16, "y": 0, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0, "w": 1},
                },
                "covariance": [0] * 36,
            }
        },
    )

    assert (pose.position.x, pose.position.y, pose.position.z) == (1.0, 0.0, -2.0)
    assert (pose.orientation.x, pose.orientation.w) == (0.0, 1.0)
    assert (twist.linear.x, twist.linear.y, twist.linear.z) == (2.0, 0.0, -1.0)
    assert (twist.angular.x, twist.angular.z) == (0.0, 1.0)
    assert initial_pose.pose.pose.position.x == 16.0
    assert initial_pose.pose.pose.position.y == 0.0
    assert all(isinstance(value, float) for value in initial_pose.pose.covariance)


def test_unknown_ros_message_field_fails_conversion():
    service = object.__new__(RosbridgeService)

    assert service._dict_to_message(Pose, {"not_a_pose_field": 1}) is None


def test_compressed_image_size_limit_is_enforced():
    fake_service = SimpleNamespace(
        settings=SimpleNamespace(ros_image_max_bytes=4),
    )
    converter = MessageConverter(fake_service)
    converter.to_dict = Mock(return_value={"frame_id": "camera"})
    image = SimpleNamespace(
        header=object(),
        format="jpeg",
        data=b"12345",
    )

    result = converter.process_compressed_image(image)

    assert result["data"] == []
    assert "超过上限" in result["error"]
