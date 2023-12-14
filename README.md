## 24赛季雷达站
#### 1.背景
24赛季雷达站将基于原先代码的框架下，并借鉴华南虎的方案：使用神经网络识别车辆，再配合激光雷达获取深度图对目标进行定位。（未完

#### 2.功能
* 识别、分类、定位图中的敌我机器人。
* 获取并分析裁判系统信息，并加以处理利用。
* 对重点区域进行着重观测，实现飞坡预警、打符倒计时等辅助功能。

#### 3.环境
1. 软件环境：Ubuntu20.04、cuda、cudnn、tensorRT（未完
2. 硬件环境：主机（**RTX4080**）、Livox激光雷达、MV-SUA630C工业相机

#### 4.项目文件架构
（未完

#### 5.项目框架
（未完

#### 6.整体思路
设置多个独立运行的模块以及一条主线：相机模块（实时获取彩色图）、激光雷达模块（实时扫描获取获取深度信息）、深度图制作模块（实时获取深度信息并制作深度图）、UI模块（搞个好看的）。  

主线即主线程，从对应的模块获取信息，结合信息用于算法计算：同时读取彩色图与深度图进行目标检测、分类与追踪，随后定位所有目标到小地图上的位置，然后综合位置与裁判系统的信息，输入行为树进行决策，将信息展示在UI上。  
  
* 目标检测  
> 使用YOLOv8进行目标检测。
* 目标分类
> 将目标检测到的ROI区域裁减出来作为输入，再次进行神经网络（未定）检测装甲板。
  
**使用tensorRT进行推理加速**  
* 目标跟踪
> （未定

* 小地图映射
> 1. 三层透视变换法（备用方案）
> 2. 激光雷达k聚类映射法

* 决策
> 实现飞坡预警、打符倒计时等辅助功能。

* UI设计
> （搞个好看的

#### 7.改进





