#! /bin/bash
source ~/.bashrc
sleep 5
roslaunch livox_ros_driver livox_lidar.launch publish_freq:=60
sleep 5
cd /home/zk/zk/
conda activate 608
python main.py