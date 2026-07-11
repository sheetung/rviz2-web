from geometry_msgs.msg import PoseStamped

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
