# 雷达使用教程
> lidar_id: 3GGDJ7V00100511  

***

## 点云数据获取
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

## 基于深度图的点云聚类方法
1. 扫描线补偿
> 
2. 地面点移除
>
3. 深度图生成
> 
4. 领域搜索与阈值设计
> 

***

## 基于ROS的Livox驱动使用
> 订阅Livox雷达的ROS驱动点云节点，通过一个线程不断接收雷达点云信息。由于Livox雷达基于非重复式扫描设计，设计一个队列来接收。  
> 该队列存储的是投影到相机平面上点云（在投影相机平面外的点云则去除）的像素平面坐标数组，每个队列对应一张深度图，实际上便为各个投影点在相机坐标系的z坐标矩阵。  
> 更新策略上，在点云离队时，根据pop出的投影点像素平面坐标数组，将深度图上其所有投影点位置的值置为nan，新点云加入时...

***

## 相机雷达标定
1. 环境配置
> 1.1. 安装环境和驱动（Livox_SDK，livox_ros_driver）。  
> 1.2. 安装依赖库（PCL,Eigen,Ceres-solver）。  
> 1.3. 下载源码，准备编译  
>> git clone https://github.com/Livox-SDK/livox_camera_lidar_calibration.git  
>> cd camera_lidar_calibration  
>> catkin_make  
>> source devel/setup.bash  
> 
> 1.4. 程序节点概括  
> * cameraCalib - 标定相机内参  
> * pcdTransfer - 将雷达点云rosbag转换成PCD文件  
> * cornerPhoto - 获得照片角点  
> * getExt1 - 计算外参节点１，只优化外参  
> * getExt2 - 计算外参节点２，同时优化内参和外参  
> * projectCloud - 把雷达点云投影到照片上  
> * colorLidar - 雷达点云着色  
2. 相机内参标定  
> 2.1. 准备20张以上的照片数据，各个角度和位置都要覆盖，拍摄的时候不要距离太近(3米左右)。  
> 2.2. 获得照片数据后，配置cameraCalib.launch中对应的路径和参数，默认是把照片数据放在data/camera/photos下，然后在data/camera/in.txt中写入所有需要使用的照片名称。  
> 2.3. roslaunch camera_lidar_calibration cameraCalib.launch  
> 2.4. 标定结果中会保存在data/camera/result.txt中，包括重投影误差，内参矩阵和畸变纠正参数。  
> 2.5. 内参结果：一个3x3的内参矩阵，一个1x5的畸变纠正参数k1, k2, p1, p2, k3。  
3. 标定准备  
> 3.1. 使用标定板的四个角点来作为目标物。标定场景最好选择一个较为空旷的环境，这样方便识别标定板，并且保证雷达到标定板有３米以上。需要选取至少10个左右不同的角度和距离来摆放标定板(参考相机内参的标定物摆放)，左右位置和不同的偏向角度最好都有采集数据。  
> 3.2. 连接雷达： 
>> roslaunch livox_ros_driver livox_lidar_rviz.launch(检查标定板角点是否在点云中，输入点云可视化的命令查看点云)  
>> roslaunch livox_ros_driver livox_lidar_msg.launch(需要录制rosbag时输入另一个命令)  
>
> 3.3. 连接相机  
> 3.4. 采集照片和点云数量  
>> 1. 拍摄照片  
>> 2. 运行指令录制点云：rosbag record /livox/lidar  
>> 3. 每个位置保存一张照片和10s左右的rosbag即可。  
>> 4. 数据采集完成后，将照片放在data/photo文件夹下; 雷达rosbag放在data/lidar文件夹下。  
>
4. 标定数据获取  
> 4.1. 参数设置：首先需要把步骤２得到的内参和畸变纠正参数以下图的格式保存在data/parameters/intrinsic.txt文件下。distortion下面对应５个畸变纠正参数，按顺序是k1和k2 (RadialDistortion)，p1和p2 (TangentialDistortion)，最后一个是k3，一般默认是０。  
> 4.2. 获得照片中的角点坐标：
>> 1. 配置cornerPhoto.launch文件中的照片路径，运行:roslaunch camera_lidar_calibration cornerPhoto.launch.  
>> 2. 程序会在UI中打开对应的照片。在这个UI界面上只要把鼠标移到标定板的各个角上，窗口左下角就会显示对应的坐标数据。确定一个顺序，一般从左上角的角点开始，逆时针旋转按顺序记录下四个角点坐标。  
>> 3. 记录完毕后选中显示的图片按任意键，进入坐标输入流程。把记录下的四个坐标”x y”按顺序输入，x和y中间要有空格(比如: “635 487”)，输入完成后输入”0 0”即可结束输入流程(如下图例所示)。程序会算出四个更精确的float类型坐标显示出来，并保存在data/corner_photo.txt中。然后按任意键结束整个流程。  
>> 4. 更改cornerPhoto.launch文件中的照片路径，重复上述流程，直至获得所有照片的角点坐标。  
>
> 4.3. 获得雷达点云中的角点坐标:  
>> 1. 检查pcdTransfer.launch文件中的rosbag路径，设置rosbag的数量，并将rosbag以0.bag, 1.bag...命名。  
>> 2. 运行指令将rosbag批量转化成PCD文件，PCD文件默认保存在data/pcdFiles文件夹中：roslaunch camera_lidar_calibration pcdTransfer.launch。  
>> 3. 使用pcl_viewer打开PCD文件，按住shift+左键点击即可获得对应的点坐标。注意和照片采用相同的角点顺序：pcl_viewer -use_point_picking xx.pcd。  
>> 4. 将xyz角点坐标按如下格式保存在data/corner_lidar.txt中，将所有PCD文件中雷达点云的角点坐标保存下来。  
5. 外参计算  
> 5.1. 参数设置：外参计算节点会读取data/corner_photo.txt和data/corner_lidar.txt中的标定数据来计算外参，数据需要保存成特定的格式才能被外参计算节点正确读取。参考以下格式，每行数据只有超过10个字母程序才会将其读取为计算的参数，比如下图用来编号的１２３４，lidar0和0.bmp这些标题不会被读取为计算参数。程序读到空行就会停止读取参数开始计算，所以保存时不要空行。  
> 5.2. 外参计算getExt1节点:roslaunch camera_lidar_calibration getExt1.launch.  外参结果以齐次矩阵的格式保存到data/parameters/extrinsic.txt下。  
> 5.3. 外参计算getExt２节点:roslaunch camera_lidar_calibration getExt2.launch. 如果经过验证getExt2计算的结果确实更好，那么把新的内参更新在data/parameters/intrinsic.txt中。  
6. 结果验证与相关应用  
> 6.1. 投影点云到照片:在projectCloud.launch文件中配置点云和照片的路径后，运行指令，将rosbag中一定数量的点投影到照片上并且保存成新的照片。  
>> roslaunch camera_lidar_calibration projectCloud.launch.  
> 
> 6.2. 点云着色:在colorLidar.launch文件中配置点云和照片的路径，运行指令，可以在rviz中检查着色的效果。  
>> roslaunch camera_lidar_calibration colorLidar.launch.  



