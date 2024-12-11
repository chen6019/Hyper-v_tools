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
        update_vm_list(names, states)
    
    threading.Thread(target=task).start()

def parse_vm_status(vm_status):
    lines = vm_status.strip().split('\n')
    names = []
    states = []
    for line in lines[2:]:  # 跳过前两行表头
        parts = line.split()
        names.append(parts[0])
        states.append(parts[1])
    return names, states

def update_vm_list(names, states):
    vm_list.delete(0, tk.END)
    for name, state in zip(names, states):
        vm_list.insert(tk.END, f"{name}: {state}")

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
root.wm_minsize(350, 650)  # 将宽度设置为600，高度设置为600

# 添加提示标签
name_hint_label = tk.Label(status_frame, text="名称:    状态", justify=tk.LEFT, anchor="nw")
name_hint_label.grid(row=0, column=0, sticky="w")

# 创建虚拟机状态列表框
vm_list = tk.Listbox(status_frame)
vm_list.grid(row=1, column=0, rowspan=4, pady=10, sticky="nsew")

# 添加刷新按钮
refresh_button = tk.Button(status_frame, text="刷新", command=refresh_vm_status)
refresh_button.grid(row=0, column=1, sticky="w")

# 获取虚拟机状态并显示在列表框中
vm_status = show_vm_status()
names, states = parse_vm_status(vm_status)
update_vm_list(names, states)

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