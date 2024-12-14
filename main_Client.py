import ctypes
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import logging
import threading
import win32com.client

# 设置窗口居中
def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

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
    
    run_in_thread(task)

def parse_vm_status(vm_status):
    lines = vm_status.strip().split('\n')
    names = []
    states = []
    for line in lines[2:]:
        parts = line.split()
        names.append(parts[0])
        states.append(parts[1])
    return names, states

def update_vm_list(names, states):
    vm_list.delete(0, tk.END)
    for name, state in zip(names, states):
        display_text = f"{name} {state}"
        vm_list.insert(tk.END, display_text)

# 定义启动虚拟机的工作函数
def start_vm_process(vm_name):
    try:
        subprocess.run(["PowerShell", "Start-VM", "-Name", vm_name], check=True)
        logging.info(f"虚拟机 {vm_name} 已启动。")
    except subprocess.CalledProcessError as e:
        logging.error(f"启动虚拟机 {vm_name} 失败: {e}")

# 定义关闭虚拟机的工作函数
def stop_vm_process(vm_name):
    try:
        # 使用 PowerShell 强制关闭虚拟机
        subprocess.run(["powershell", "-Command", f"Stop-VM -Name '{vm_name}' -Force"], check=True)
        logging.info(f"虚拟机 {vm_name} 已强制关闭。")
    except subprocess.CalledProcessError as e:
        logging.error(f"强制关闭虚拟机 {vm_name} 失败: {e}")
        messagebox.showerror("错误", f"强制关闭虚拟机 {vm_name} 失败。\n{e}")

# 修改 start_vm 函数
def start_vm():
    selected = vm_list.curselection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.get(selected[0])
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分
    
    run_in_thread(start_vm_process, vm_name)
    
    messagebox.showinfo("启动中", f"虚拟机 {vm_name} 正在启动。")
    refresh_vm_status()

# 修改 stop_vm 函数
def stop_vm():
    selected = vm_list.curselection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.get(selected[0])
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分

    # 弹出确认对话框
    confirm = messagebox.askyesno("确认", f"确定要强制关闭虚拟机 {vm_name} 吗？")
    if not confirm:
        return
    stop_vm_process(vm_name)
    messagebox.showinfo("关闭中", f"虚拟机 {vm_name} 正在强制关闭。")
    refresh_vm_status()

# 打开虚拟机远程连接
def open_vm_connect():
    selected = vm_list.curselection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.get(selected[0])
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分

    try:
        # 使用 vmconnect.exe 打开特定虚拟机的远程连接界面
        subprocess.run(["vmconnect.exe", "localhost", vm_name], check=True)
        logging.info(f"已打开虚拟机 {vm_name} 的远程连接界面。")
    except subprocess.CalledProcessError as e:
        logging.error(f"无法打开虚拟机 {vm_name} 的远程连接界面: {e}")
        messagebox.showerror("错误", f"无法打开虚拟机 {vm_name} 的远程连接界面。\n{e}")

def open_hyper_v_manager():
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.Run("mmc virtmgmt.msc")
        logging.info("已打开 Hyper-V 管理器。")
    except subprocess.CalledProcessError as e:
        logging.error(f"无法打开 Hyper-V 管理器: {e}")
        messagebox.showerror("错误", "无法打开 Hyper-V 管理器。")
    except Exception as e:
        logging.error(f"无法打开 Hyper-V 管理器: {e}")
        messagebox.showerror("错误", "无法打开 Hyper-V 管理器。\n请确保已开启 Hyper-V。")

def run_in_thread(target, *args):
    thread = threading.Thread(target=target, args=args)
    thread.start()

# 判断是否拥有管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False
    
# 获取管理员权限
def get_administrator_privileges():
    confirm = messagebox.askyesno("确认", "您确定要以管理员权限重新运行吗？")
    if confirm:
        ctypes.windll.shell32.ShellExecuteW(None,"runas", sys.executable, __file__, None, 1)
        exit()

# 查看GPU虚拟化状态
def check_gpu_virtualization_status():
    selected = vm_list.curselection()
    if not selected:
        return False
    display_text = vm_list.get(selected[0])
    vm = display_text.split(" ", 1)[0]  
    try:
        # PowerShell 命令
        command = f'powershell.exe Get-VMGpuPartitionAdapter -VMName {vm}'
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            raise Exception(result.stderr)
        
        status = result.stdout.strip()
        # 解析输出并提取值
        gpu_info = {}
        for line in status.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                gpu_info[key.strip()] = value.strip()
        
        logging.info(f"获取的 GPU 虚拟化状态: {gpu_info}")
        return gpu_info
    except Exception as e:
        logging.error(f"获取 GPU 虚拟化状态失败: {e}")
        return None

# 设置 GPU 虚拟化
def set_gpu_virtualization():
    gpu_info = check_gpu_virtualization_status()
    if gpu_info is False:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    elif gpu_info is None:
        messagebox.showerror("错误", "无法获取 GPU 虚拟化状态。")
        return
    GPU_window = tk.Toplevel(root)
    GPU_window.title("GPU虚拟化")
    GPU_window.resizable(False, False)

    # 创建标签和输入框
    tk.Label(GPU_window, text="MinPartitionVRAM：").grid(row=0, column=0, sticky="e")
    min_vram_var = tk.StringVar(value=gpu_info.get("MinPartitionVRAM", ""))
    tk.Entry(GPU_window, textvariable=min_vram_var).grid(row=0, column=1, sticky="w")

    tk.Label(GPU_window, text="MaxPartitionVRAM：").grid(row=1, column=0, sticky="e")
    max_vram_var = tk.StringVar(value=gpu_info.get("MaxPartitionVRAM", ""))
    tk.Entry(GPU_window, textvariable=max_vram_var).grid(row=1, column=1, sticky="w")

    tk.Label(GPU_window, text="OptimalPartitionVRAM：").grid(row=2, column=0, sticky="e")
    optimal_vram_var = tk.StringVar(value=gpu_info.get("OptimalPartitionVRAM", ""))
    tk.Entry(GPU_window, textvariable=optimal_vram_var).grid(row=2, column=1, sticky="w")

    # 保存和取消按钮
    def save_gpu_settings():
        selected = vm_list.curselection()
        if not selected:
            messagebox.showwarning("警告", "请选择一个虚拟机。")
            return
        display_text = vm_list.get(selected[0])
        vm_name = display_text.split(" ", 1)[0]
        min_vram = min_vram_var.get()
        max_vram = max_vram_var.get()
        optimal_vram = optimal_vram_var.get()
        # 获取其他参数的值

        try:
            # 构建 PowerShell 命令
            ps_command = f'Set-VMGpuPartitionAdapter -VMName "{vm_name}" -MinPartitionVRAM {min_vram} -MaxPartitionVRAM {max_vram} -OptimalPartitionVRAM {optimal_vram}'
            # 执行 PowerShell 命令
            subprocess.run(["powershell.exe", ps_command], check=True)
            messagebox.showinfo("成功", "GPU 虚拟化设置已保存。")
            GPU_window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"设置 GPU 虚拟化失败：{e}")

    def cancel():
        GPU_window.destroy()

    tk.Button(GPU_window, text="保存", command=save_gpu_settings).grid(row=3, column=0, pady=15)
    tk.Button(GPU_window, text="取消", command=cancel).grid(row=3, column=1)

    center_window(GPU_window)

def exit():
    root.destroy()
    sys.exit()

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

# 创建状态框架
status_frame = tk.Frame(root)
status_frame.pack(fill=tk.BOTH, expand=True, padx=15)  # 左边空出15db左右的空间

# 添加提示标签
name_hint_label = tk.Label(status_frame, text="名称:", justify=tk.LEFT, anchor="nw")
name_hint_label.grid(row=0, column=0, sticky="w")
name_hint_label = tk.Label(status_frame, text="状态", justify=tk.LEFT, anchor="nw")
name_hint_label.grid(row=0, column=0, sticky="e")
name_hint_label = tk.Label(status_frame, text="工具", justify=tk.LEFT, anchor="n")
name_hint_label.grid(row=0, column=1, sticky="")

# 创建虚拟机状态列表框
vm_list = tk.Listbox(status_frame)
vm_list.grid(row=1, column=0, rowspan=4, sticky="nsew")

# 添加刷新按钮
refresh_button = tk.Button(status_frame, text="刷新", command=lambda:run_in_thread(refresh_vm_status))
refresh_button.grid(row=5, column=0)

# 获取虚拟机状态并显示在列表框中
vm_status = show_vm_status()
names, states = parse_vm_status(vm_status)
update_vm_list(names, states)

# 添加启动和关闭按钮到 status_frame 中
start_button = tk.Button(status_frame, text="启动", command=lambda:run_in_thread(start_vm))
start_button.grid(row=5, column=0, padx=5, pady=5, sticky="w")

stop_button = tk.Button(status_frame, text="关闭", command=lambda:run_in_thread(stop_vm))
stop_button.grid(row=5, column=0, padx=5, pady=5, sticky="e")

# 添加设置和关闭 GPU 虚拟化按钮到 status_frame 中
set_gpu_button = tk.Button(status_frame, text="GPU 虚拟化", command=lambda:run_in_thread(set_gpu_virtualization))
set_gpu_button.grid(row=1, column=1, padx=5, pady=5, sticky="e")

Remote_connection_button = tk.Button(status_frame, text="打开远程连接", command=lambda:run_in_thread(open_vm_connect))
Remote_connection_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

settings_button = tk.Button(status_frame, text="Hyper-V管理器", command=lambda: run_in_thread(open_hyper_v_manager))
settings_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

# 添加取消按钮
save_button = tk.Button(status_frame, text="打开日志文件夹", command=open_config_folder)
save_button.grid(row=7, column=0, padx=5, pady=10, sticky="w")

# 添加取消按钮
save_button = tk.Button(status_frame, text="取消", command=exit)
save_button.grid(row=7, column=1, padx=5, pady=10, sticky="ew")

# 设置窗口居中
center_window(root)

# 主循环
root.mainloop()