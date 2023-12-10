# Livox雷达使用及点云数据处理

***

## Livox雷达使用及点云数据获取
1. 安装Livox-SDK
> 1. 安装相应的依赖库  
>> sudo apt install cmake pkg-config libapr1-dev libboost-atomic-dev libboost-system-dev  
> 2. 从GitHub克隆Livox-SDK/Livox-SDK存储库  
>> git clone https://github.com/Livox-SDK/Livox-SDK.git  
> 3. 在build目录下编译并安装Livox-SDK  
>> cd Livox-SDK/build  
>> cmake ..  
>> make  
>> sudo make install  

2. 安装Livox ROS Driver驱动
> 1. 从github克隆livox_ros_driver软件包  
>> git clone https://github.com/Livox-SDK/livox_ros_driver.git ws_livox / src
> 2. 编译livox_ros_driver软件包
>> cd ws_livox  
>> catkin_make  
> 
> 3.软件包环境更新  
>> source ./devel/setup.sh

3. **设置静态IP**！！！  
> sudo ifconfig <id> 192.168.1.50

4. 采集点云数据
> * 通过Livox-SDK采集lvx格式的点云数据（具体操作请阅读Livox-SDK中的README） 
> * 使用ROS launch文件加载驱动采集到bag格式的点云数据
>   * 通过ROS将bag文件转pcd文件

5. 其他
> 可以考虑魔改Livox-SDK直接将点云数据x y z tag输出（该方案笔者已经基本实现，待之后优化）
***  

## 点云数据处理

### 点云数据预处理
1. 获得三维坐标XYZ的点云数据
2. 点云组帧
> 将多个点云数据包叠加到同一帧上，让这一帧上的点云数据能包含上万个点云，以便后续感知和定位流程的处理  
3. 外参变化
> 点云数据通过解析得到的点云坐标系属于激光雷达坐标系，实际应用中，需要将坐标系转化成相机坐标系。相机与激光雷达的相对姿态与位移是固定不变，所以可以通过旋转或者平移，将两个三维坐标系统统一到一个三维坐标系（全局坐标系或世界坐标系）。
4. 滤波处理
> 对点云进行滤波处理：  
> * 噪点是指对模型处理无用的点云数据
> * 离群点是指远离主观测区域的点云数据（一般情况下，噪点包含离群点）
> 使用各种滤波算法进行滤波处理（具体操作自行查找）

### 感知数据处理
#### 基于传统方法的感知数据处理
1. 地面点云分割
> 对地面点云进行过滤处理（一般采用传统算法来进行地面点云分割）
2. 目标物的点云分割
> 将目标物点云根据空间、几何和纹理等特征进行有效地分割、分块，从而便于对目标物进行单独处理
3. 目标物聚类分析
> 将点云图中各个已分割的点云聚类成若干个整体，即把具有相似程度较高的点云组成一组，以便降低后续模型的计算量
4. 匹配与跟踪
> 点云数据的匹配与跟踪并未使用，之后可以尝试  
#### 基于深度学习的感知数据处理
> 之后尝试

**尝试综合应用AI算法和传统算法**，来进行感知数据处理。

### 定位功能层面的处理
1. 特征处理
2. 地图匹配
3. 位姿优化  

***
## （未完待补充）
