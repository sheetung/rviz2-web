export const ROS_TOPICS = {
  laserScan: '',
  pointCloud: '',
  inflatedMap: '',
  odom: '',
  pose: '',
  expectedControl: '',
  initialPose: '',
  goalMarker: '',
  expSfc: '',
  path: '',
  expTraj: '',
  backupTraj: '',
  cmdVel: ''
}

export const getDefaultVisualizationTopics = () => [
  { topic: ROS_TOPICS.pointCloud, type: 'sensor_msgs/msg/PointCloud2' },
  { topic: ROS_TOPICS.odom, type: 'nav_msgs/msg/Odometry' },
  { topic: ROS_TOPICS.goalMarker, type: 'visualization_msgs/msg/MarkerArray' },
  { topic: ROS_TOPICS.expSfc, type: 'visualization_msgs/msg/MarkerArray' },
  { topic: ROS_TOPICS.path, type: 'nav_msgs/msg/Path' },
  { topic: ROS_TOPICS.expTraj, type: 'visualization_msgs/msg/MarkerArray' },
  { topic: ROS_TOPICS.backupTraj, type: 'visualization_msgs/msg/MarkerArray' },
  { topic: ROS_TOPICS.inflatedMap, type: 'sensor_msgs/msg/PointCloud2' }
].filter(item => item.topic)

export const getPositionTopics = () => [
  { topic: ROS_TOPICS.odom, type: 'nav_msgs/msg/Odometry' }
].filter(item => item.topic)
