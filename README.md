# Hyper-V Tools
### 两个版本(虚拟机客户端和实体客户端)
## 实体机:
#### 功能:
一.查看虚拟机状态
>1.会有多个虚拟机
>2.运行状态

二.开启和关闭虚拟机
>1.启动
>2.关闭
>>API or Powershell

三.打开虚拟机设置
>1.打开系统自带的虚拟机设置界面
>>对应虚拟机名字
>>API or Powershell

四.设置GPU虚拟化
>1.设置GPU虚拟化(不同GPU类型驱动路径不同)
>>需要先查询是否支持GPU虚拟化
>>1.虚拟机名称
>>2.内存最大,最小值
>>
>2.实体机GPU驱动更新时自动更新虚拟机GPU驱动

五.删除GPU虚拟化
>1.虚拟机名称

#### 设置
一.开机自启
二.设置GPU类型和型号
>AMD
>NVIDA
>Inter

三.两个路径(GPU驱动保存位置,配置文件位置)
>用API选择

四.关于本项目
>项目链接(GitHub)
>[https://github.com/yourusername/Hyper-v_tools](https://github.com/yourusername/Hyper-v_tools)

## 虚拟机:
#### 功能:
1.查看虚拟化GPU状态
>API or Powershell
2.自动同步粘贴剪切板里的GPU驱动到配置目录
3.自动更新GPU驱动
>1.是否删除原文件

#### 设置
一.开机自启

三.两个路径(GPU驱动保存位置,配置文件位置)
>用API选择

四.关于本项目
>项目链接(GitHub)
>[https://github.com/yourusername/Hyper-v_tools](https://github.com/yourusername/Hyper-v_tools)
