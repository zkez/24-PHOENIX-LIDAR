# ROS

***

#### ROS概念
> ROS是通讯机制、工具通讯包、机器人高层技能以及机器人生态系统的集合体。  

#### ROS设计目标
> 分布式：ROS是进程（也称为Nodes节点）的分布式框架，ROS中的进程可分布于不同主机，不同主机协同工作，从而分散计算压力。  
> 松耦合：ROS中功能模块封装于独立的功能包或元功能包（储存在src），便于分享，功能包内的模块以节点（node）为单位运行，以ROS标准的IO作为接口，开发者不需要关注模块内部实现，只要了解接口规则就能实现复用,实现了模块间点对点的松耦合连接。  
> 精简：ROS被设计为尽可能精简，以便为ROS编写的代码可以与其他机器人软件框架一起使用。
> 丰富的组件化工具包：ROS可采用组件化方式集成一些工具和软件到系统中并作为一个组件直接使用，如RVIZ（3D可视化工具），开发者根据ROS定义的接口在其中显示机器人模型等，组件还包括仿真环境和消息查看工具等。  

### 一键安装ROS
> wget http://fishros.com/install -O fishros && bash fishros


## 编写ROS程序
* 先创建一个工作空间
* 再创建一个功能包
* 编辑源文件
* 编辑配置文件
* 编译并执行  
**只要会调用已写好的功能包，使其适配即可完成功能的实现**  

1. 创建工作空间并初始化
> mkdir -p ~/catkin_ws/src  
> cd ~/catkin_ws  
> catkin_make  
2. 进入src创建ros包并添加依赖  
> cd ~/catkin_ws/src
> catkin_create_pkg 自定义ROS包名 std_msgs rospy roscpp
>> 在工作空间下生成一个功能包，该功能包依赖于 roscpp、rospy 与 std_msgs，其中roscpp是使用C++实现的库，而rospy则是使用python实现的库，std_msgs是标准消息库。  

***

#### Hello World实现（python版本）
1. 进入ros包添加scripts目录并编辑python文件
> cd ros包  
> mkdir scripts  
> * 指定解释器  
> * 1. 导包  
> * 2. 编写主入口
> * 3. 初始化ROS节点
> * 4. 输出日志Hello World  

'''python  
    #!/usr/bin/env python  # 指定解释器  
    #coding=utf-8  # 指定编码格式  
    import rospy  # 导包  
    if __name__ == '__main__':  # 主入口  
        rospy.init_node('hello_world')  # 初始化ROS节点  
        rospy.loginfo('Hello World')  # 输出日志Hello World  
'''  

2. 为python文件添加可执行权限  
> chmod +x hello_world.py  

3. 编辑ros包下的CMakeLists.txt文件  
> catkin_install_python(PROGRAMS scripts/hello_world.py DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})  

4. 进入工作空间目录并编译  
> cd ~/catkin_ws  
> catkin_make  

5. 进入工作空间目录并执行  
> roscore  
> cd ~/catkin_ws  
> source ./devel/setup.bash  
> rosrun ros包名 hello_world.py  

***  

#### launch文件
> launch文件是ROS中的一种配置文件，用于启动多个节点，配置节点的参数，配置节点的命名空间，配置节点的日志级别等。  
> **频繁使用!**  

#### 自定义的工作空间
    |--- build:编译空间，用于存放CMake和catkin的缓存信息、配置信息和其他中间文件。

    |--- devel:开发空间，用于存放编译后生成的目标文件，包括头文件、动态&静态链接库、可执行文件等。

    |--- src: 源码

        |-- package：功能包(ROS基本单元)包含多个节点、库与配置文件，包名所有字母小写，只能由字母、数字与下划线组成
    
            |-- CMakeLists.txt 配置编译规则，比如源文件、依赖项、目标文件
    
            |-- package.xml 包信息，比如:包名、版本、作者、依赖项...(以前版本是 manifest.xml)
    
            |-- scripts 存储python文件
    
            |-- src 存储C++源文件
    
            |-- include 头文件
    
            |-- msg 消息通信格式文件
    
            |-- srv 服务通信格式文件
    
            |-- action 动作格式文件
    
            |-- launch 可一次性运行多个节点 
    
            |-- config 配置信息
    
        |-- CMakeLists.txt: 编译的基本配置  

#### ROS文件系统相关命令  
1. 增加  
> catkin_create_pkg <包名> [依赖项]  
> sudo apt install ros-<版本>-<包名>  
2. 删除  
> sudo apt purge ros-<版本>-<包名>  
3. 查找  
> rospack list  
> rospack find <包名>  
> roscd <包名>  
> rosls <包名>  
> apt search ros-<版本>-<包名>  
4. 修改  
> rosed <包名>  
5. 执行  
> roscore  
> rosrun <包名> <节点名>  
> roslaunch <包名> <launch文件名>  

#### ROS计算图  
> rosrun rqt_graph rqt_graph | rqt_graph  

***  

## ROS通信机制  
1. 话题通信（发布订阅模式）
2. 服务通信（请求响应模式）  
3. 参数服务器（参数共享模式）  

### 话题通信  
> 基于发布订阅模式：以发布订阅的方式实现不同节点之间数据交互的通信模式。，用于不断更新的、少逻辑处理的数据传输场景。  

> **0.Talker注册**  
> Talker启动后，会通过RPC在 ROS Master 中注册自身信息，其中包含所发布消息的话题名称。ROS Master 会将节点的注册信息加入到注册表中。  
> **1.Listener注册**  
> Listener启动后，也会通过RPC在 ROS Master 中注册自身信息，包含需要订阅消息的话题名。ROS Master 会将节点的注册信息加入到注册表中。  
> **2.ROS Master实现信息匹配**  
> ROS Master 会根据注册表中的信息匹配Talker 和 Listener，并通过 RPC 向 Listener 发送 Talker 的 RPC 地址信息。  
> **3.Listener向Talker发送请求**  
> Listener 根据接收到的 RPC 地址，通过 RPC 向 Talker 发送连接请求，传输订阅的话题名称、消息类型以及通信协议(TCP/UDP)。  
> **4.Talker确认请求**  
> Talker 接收到 Listener 的请求后，也是通过 RPC 向 Listener 确认连接信息，并发送自身的 TCP 地址信息。  
> **5.Listener与Talker建立连接**  
> Listener 根据步骤4 返回的消息使用 TCP 与 Talker 建立网络连接。  
> **6.Talker向Listener发送消息**  
> 连接建立后，Talker 开始向 Listener 发布消息。  

#### 话题通信的实现（python版本）  
> 例子：编写发布订阅实现，要求发布方以10HZ(每秒10次)的频率发布文本消息，订阅方订阅消息并将消息内容打印输出。  
**流程**  
1. 编写发布方实现。
2. 编写订阅方实现。
3. 为python文件添加可执行权限。  
4. 编辑配置文件。  
5. 编译并执行。  

##### 发布者py文件实现  
'''python  
    #! /usr/bin/env  python  
    #-*-coding:UTF-8-*-  
    # 导包  
    import rospy  
    from std_msgs.msg import String  # 发布消息的类型(导包)  
    """  
    使用python实现消息发布  
        1.导包  
        2.初始化ros节点  
        3.创建发布者对象  
        4.编写发布逻辑并发布数据  
    """  
    if __name__=="__main__":  #编写主入口  
         # 2.初始化ros节点：  
         rospy.init_node("sandai")#传入节点名称,发布者名称  
         # 3.创建发布者对象：  
         pub=rospy.Publisher("che",String,queue_size=10)  # 话题名称，发布数据类型，队列长度  
         # 4 .编写发布逻辑并发布数据  
        # 创建数据  
         msg=String()  
        # 使用循环发布数据  
         while not rospy.is_shutdown():  
            msg.data="hello"  
        # 发布数据  
            pub.publish(msg)  
'''  

##### 订阅者py文件实现  
'''python  
    #! /usr/bin/env python   # shebang行不能错，易错  
    #-*-coding:UTF-8-*-  
    # 1.导包  
    import rospy  
    from std_msgs.msg import String  
    """  
        订阅流程：  
            1.导包  
            2.初始化ros节点  
            3.创建订阅者对象  
            4.回调函数处理数据  
            5.spin()  
    """  
    # 回调函数中传入msg  
    def doMsg(msg):rospy.loginfo("我的订阅到的数据：%s",msg.data)  
    if __name__=="__main__":  
            # 1.导包  
            # 2.初始化ros节点  
            rospy.init_node("huahua")  
            # 3.创建订阅者对象  
            sub=rospy.Subscriber("che",String,doMsg,queue_size=10)  
            # 4.回调函数处理数据  
            # 5.spin()  
            rospy.spin()   
'''

**建议自己手敲一遍**  

***  

#### 话题通信自定义msg  
1. 定义msg文件：在功能包src中新建msg文件夹，并新建msg后缀的文件!(注意文件创建的位置）  
2. 编辑配置文件：编辑package.xml文件；编辑CMakeLists.txt文件（层层包含）。    
    
