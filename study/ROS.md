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
> * wget http://fishros.com/install -O fishros && bash fishros  

> * 基于ubuntu22.04使用docker配置ros-noetic版本:  
```
1. docker pull ubuntu:20.04  
2. docker run -it --name ros -v --net=host ubuntu:20.04 /bin/bash  
3. apt-get update  
4. apt-get install -y lsb-release gnupg2  
5. sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'  
6. apt-get install -y curl  
7. curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc  
8. apt-get update  
9. apt-get install ros-noetic-desktop  
10. echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc  
11. source ~/.bashrc  
12. apt-get install -y python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool  
13. apt-get install pip  
14. pip install rosdepc  
15. rosdepc init  
16. rosdepc update  
17. roscore(验证是否成功)  
```

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

```  
    #!/usr/bin/env python  # 指定解释器  
    #coding=utf-8  # 指定编码格式  
    import rospy  # 导包  
    if __name__ == '__main__':  # 主入口  
        rospy.init_node('hello_world')  # 初始化ROS节点  
        rospy.loginfo('Hello World')  # 输出日志Hello World  
```  

2. 为python文件添加可执行权限  
> chmod +x hello_world.py  

3. 编辑ros包下的CMakeLists.txt文件  
> catkin_install_python(PROGRAMS scr ipts/hello_world.py DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})  

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
```  
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
```  

##### 订阅者py文件实现  
```  
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
```

**建议自己手敲一遍**  

***  

#### 话题通信自定义msg  
1. 定义msg文件：在功能包src中新建msg文件夹，并新建msg后缀的文件!(注意文件创建的位置）  
2. 编辑配置文件：编辑package.xml文件；编辑CMakeLists.txt文件（层层包含）。     

***

### 服务通信  
> 基于请求响应模式：以请求响应的方式实现不同节点之间数据交互的通信模式，用于少量数据的传输场景。
>> 具体流程（举例）：  
>> master    管理者  （114平台）  
>> Server/talker       服务端	（服务公司）  
>> Client/listener     客户端	（我）  
>> 1. 保洁公司在114平台注册自身信息，提交地址  
>> 2. 我需要访问114平台，注册自己想要的服务（疏通下水道） 
>> 3. 114平台进行话题匹配并将服务端的连接方式响应给客户端（电话号码） 
>> 4. 我打电话给保洁公司  
>> 5. 保洁公司说可以  

#### 服务通信自定义srv  
> 定义srv实现流程与自定义msg实现流程类似。  
> 1. 按照固定格式创建srv文件  
> 2. 编辑配置文件  
> 3. 编译生成中间文件  

#### 服务通信自定义srv调用（python版本）  
> 流程：
> 1. 编写服务端实现。  
> 2. 编写客户端实现。  
> 3. 为python文件添加可执行权限。  
> 4. 编辑配置文件。  
> 5. 编译并执行。  
#### 服务端实现  
```  
    #! /usr/bin/env python
    #coding=utf-8
    import rospy
    #from plumbing_server_client.srv import AddInts,AddIntsRequest,AddIntsResponse
    #也可以直接替换成*
    from plumbing_server_client.srv import *
    # 服务端解析客户端请求，产生响应
    # 具体流程：
    #     1 导包；_srv 两种方式都能成功
    #     2 初始化ros节点
    #     3 创建服务端对象
    #     4 处理请求，产生响应
    #     5 处理逻辑（回调函数）
    #     6 spin()
    
    #回调函数参数：封装了请求request数据
    #返回值：响应数据response
    def doNum(request):
        #1 解析提交的两个整数
        num1=request.num1
        num2=request.num2
        #2 进行求和
        sum=num1+num2
        #3 将结果封装进响应对象
        response=AddIntsResponse()#类型
        response.sum=sum
        rospy.loginfo("服务器解析的数据 num1=%d.num2=%d,相应的结果:sum=%d",num1,num2,sum)
        return response
     
        
          
    if __name__=="__main__":
    #     2 初始化ros节点
        rospy.init_node("heishui")
    #     3 创建服务端对象
        server=rospy.Service("addInts",AddInts,doNum)
        rospy.loginfo("服务器已经启动了！")
    #     4 处理请求，产生响应
    #     5 处理逻辑（回调函数）
    #     6 spin()
        rospy.spin()
```  

#### 客户端实现  
```  
    #! /usr/bin/env python
    #coding=utf-8
    
    # 客户端 组织并提交请求，处理服务端响应
    # 具体流程：
    #     1 导包；_srv
    #     2 初始化ros节点
    #     3 创建客户端对象
    #     4 组织请求的数据，并发送请求
    #     5 处理响应
    # 不需要spin 因为是主动提出
    
    import rospy
    from plumbing_server_client.srv import *
    
    if __name__=="__main__":
    #     2 初始化ros节点
        rospy.init_node("erhei")
    #     3 创建客户端对象
        client=rospy.ServiceProxy("addInts",AddInts)
    #     4 组织请求的数据，并发送请求
        response=client.call(12,34)
    #     5 处理响应  
        rospy.loginfo("响应的数据：%d",response.sum)
```  

***  

#### 参数服务器  
> 基于参数共享模式：以参数共享的方式实现不同节点之间数据交互的通信模式，用于少量数据的传输场景。
> 流程：  
> 1. Talker 设置参数：Talker 通过 RPC 向参数服务器发送参数(包括参数名与参数值)，ROS Master 将参数保存到参数列表中。  
> 2. Listener 获取参数：Listener 通过 RPC 向参数服务器请求参数，ROS Master 从参数列表中获取参数并返回给 Listener。  
> 3. ROS Master 向 Listener 发送参数值：ROS Master 根据步骤2请求提供的参数名查找参数值，并将查询结果通过 RPC 发送给 Listener。  
> * **参数服务器不是为高性能而设计的，因此最好用于存储静态的非二进制的简单数据**  

##### 参数操作（python）  
1. 增 改  
```
    #!  /usr/bin/env python
    #coding=utf-8
    # 演示参数的新增与修改
    #     需求：在参数服务器中设置机器人的属性，型号，半径
    #     实现：
    #     rospy.set_param()
        
    import rospy
    
    if __name__=="__main__":
        rospy.init_node("param_set_p")
        
        #新增参数
        rospy.set_param("type_p","xiaohaungche")
        rospy.set_param("radius_p",0.15)
     
     
       #覆盖参数
        rospy.set_param("radius_p",0.3)
```  
2. 查  
```
    #! /usr/bin/env python
    #coding=utf-8
    
    # 演示参数的查询
    # 查询的相关实现比较多
            # get_param当键存在时，返回对应的值，不存在返回默认值
            
            # get_param_cached与上类似，只是效率高
            
            # get_param_names获取所有的参数的键的集合
            
            # has_param判断是否包含某个键
            
            # search_param查找某个键，并返回完整的键名
    
    import rospy
    if __name__=="__main__":
        rospy.init_node("get_param_p")
        
        #1. get_param
        radius=rospy.get_param("radius_p",0.5)
        radius2=rospy.get_param("radius_p_xxx",0.5)
        rospy.loginfo("radius=%.2f",radius)
        rospy.loginfo("radius2=%.2f",radius2)
        
        #2. # get_param_cached  效率比上面这个高
        radius3=rospy.get_param_cached("radius_p",0.5)
        radius4=rospy.get_param_cached("radius_p_xxx",0.5)
        rospy.loginfo("radius3=%.2f",radius3)
        rospy.loginfo("radius4=%.2f",radius4)
        
        #3.get_param_names
        names= rospy.get_param_names()
        for name in names:#遍历
            rospy.loginfo("name=%s",name)
            
        #4. has_param
        flag1=rospy.has_param("radius_p")
        if flag1:
            rospy.loginfo("radius_p 存在")
        else:
            rospy.loginfo("radius_p 不存在")
        flag2=rospy.has_param("radius_pxx")
        if flag2:
            rospy.loginfo("radius_pxx 存在")
        else:
            rospy.loginfo("radius_pxx 不存在")
            
        #5. search_param 查找是否存在，存在返回键名
        key=rospy.search_param("radius_p")
        rospy.loginfo("k=%s",key)
```  
3. 删  
```
    #! /usr/bin/env python
    #coding=utf-8
    import rospy
    
    if __name__=="__main__":
        rospy.init_node("del_param_p")
        #使用try 捕获一下异常
        try:
            #删除参数
            rospy.delete_param("radius_p")
        except Exception as e:
            rospy.loginfo("被删除的参数不存在")
```  

***  

### ROS常用命令  
> rosnode :  操作节点  
> rostopic : 操作话题  
> rosservice : 操作服务  
> rosparam : 操作参数   
> rosmsg : 操作msg消息  
> rossrv : 操作srv消息  
1. rosnode  
* rosnode ping：测试到节点的连接状态  
* rosnode list：列出活动节点  
* rosnode info：打印节点信息  
* rosnode machine：列出指定设备上的节点  
* rosnode kill：杀死某个节点  
* rosnode cleanup：清除无用节点  
2. rostopic  
* rostopic bw     显示主题使用的带宽  
* rostopic delay  显示带有 header 的主题延迟  
* rostopic echo   打印消息到屏幕  （自定义消息需要先到工作空间下）  
* rostopic find   根据类型查找主题  
* rostopic hz     显示主题的发布频率  
* rostopic info   显示主题相关信息  
* rostopic list   显示所有活动状态下的主题  
* rostopic pub    将数据发布到主题  
* rostopic type   打印主题类型  
3. 剩余自行查找相关命令  

***  



