import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import logging
import threading

def show_vm_status():
    # PowerShell 命令获取虚拟机状态
    ps_command = "Get-VM | Select-Object Name, State | Format-Table -AutoSize"
    
    # 调用 PowerShell 命令
    result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
    
    # 返回结果
    return result.stdout

def refresh_vm_status():
    def task():
        vm_status = show_vm_status()
        names, states = parse_vm_status(vm_status)
        name_label.config(text=names)
        state_label.config(text=states)
    
    threading.Thread(target=task).start()

def parse_vm_status(vm_status):
    lines = vm_status.strip().split('\n')
    names = []
    states = []
    for line in lines[2:]:  # 跳过前两行表头
        parts = line.split()
        names.append(parts[0])
        states.append(parts[1])
    return '\n'.join(names), '\n'.join(states)

# 开启和关闭虚拟机
def start_vm():
    # TODO: 启动虚拟机
    pass

def stop_vm():
    # TODO: 关闭虚拟机
    pass

# 打开虚拟机设置
def open_vm_settings():
    # TODO: 打开系统自带的虚拟机设置界面
    pass

# 设置 GPU 虚拟化
def set_gpu_virtualization():
    # TODO: 设置 GPU 虚拟化参数
    pass

# 关闭 GPU 虚拟化
def disable_gpu_virtualization():
    # TODO: 关闭 GPU 虚拟化
    pass

# 打开虚拟磁盘编辑器
def open_disk_editor():
    # TODO: 打开系统自带的虚拟磁盘编辑器
    pass

# 设置界面
def open_settings():
    # TODO: 打开设置界面
    pass

# 打开配置文件夹的函数
def open_config_folder():
    os.startfile(appdata_path)

# 日志和配置文件路径处理
appdata_path = os.path.join(
    os.path.expanduser("~"), "AppData", "Roaming", "Hyper-V_tools"
)

# 如果目录不存在则创建
if not os.path.exists(appdata_path):
    os.makedirs(appdata_path)

log_path = os.path.join(appdata_path, "log.txt")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# 创建主窗口
root = tk.Tk()
root.title("Hyper-V 管理工具")
status_frame = tk.Frame(root)
status_frame.pack(fill=tk.BOTH, expand=True)
root.wm_minsize(350, 450)  # 将宽度设置为600，高度设置为600

# 获取虚拟机状态并显示在标签中
vm_status = show_vm_status()
names, states = parse_vm_status(vm_status)
name_label = tk.Label(status_frame, text=names, justify=tk.LEFT, anchor="w")
name_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
state_label = tk.Label(status_frame, text=states, justify=tk.LEFT, anchor="w")
state_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

refresh_button = tk.Button(status_frame, text="刷新", command=refresh_vm_status)
refresh_button.pack()

# 添加输入框和标签
input_frame = tk.Frame(root)
input_frame.pack(pady=10)
input_label = tk.Label(input_frame, text="虚拟机名称:")
input_label.pack(side=tk.LEFT)
vm_name_entry = tk.Entry(input_frame)
vm_name_entry.pack(side=tk.LEFT)

control_frame = tk.Frame(root)
control_frame.pack()

start_button = tk.Button(control_frame, text="启动虚拟机", command=start_vm)
start_button.grid(row=0, column=0, padx=5, pady=5)

stop_button = tk.Button(control_frame, text="关闭虚拟机", command=stop_vm)
stop_button.grid(row=0, column=1, padx=5, pady=5)

settings_button = tk.Button(root, text="打开虚拟机设置", command=open_vm_settings)
settings_button.pack(padx=5, pady=5)

set_gpu_button = tk.Button(root, text="设置 GPU 虚拟化", command=set_gpu_virtualization)
set_gpu_button.pack(padx=5, pady=5)

disable_gpu_button = tk.Button(root, text="关闭 GPU 虚拟化", command=disable_gpu_virtualization)
disable_gpu_button.pack(padx=5, pady=5)

disk_editor_button = tk.Button(root, text="打开虚拟磁盘编辑器", command=open_disk_editor)
disk_editor_button.pack(padx=5, pady=5)

menubar = tk.Menu(root)
settings_menu = tk.Menu(menubar, tearoff=0)
settings_menu.add_command(label="设置", command=open_settings)
menubar.add_cascade(label="选项", menu=settings_menu)
root.config(menu=menubar)

# 主循环
root.mainloop()