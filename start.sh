#! /bin/bash
source ~/.bashrc
sleep 2
roslaunch livox_ros_driver livox_lidar.launch publish_freq:=60 &
sleep 2
gnome-terminal -- /bin/bash -c "source ~/.bashrc; ./start_main.sh"