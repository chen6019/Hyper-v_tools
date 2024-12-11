import tkinter as tk
from tkinter import messagebox



# 查看虚拟机状态
def show_vm_status():
    # TODO: 获取并显示虚拟机的运行状态（名称、CPU、内存占用等），需另启线程
    pass

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


# 创建主窗口
root = tk.Tk()
root.title("Hyper-V 管理工具")
status_frame = tk.Frame(root)
status_frame.pack(fill=tk.BOTH, expand=True)
show_vm_status()

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
