import ctypes
from email import message
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
        # 使用 vmconnect 打开特定虚拟机的远程连接界面
        subprocess.run(["vmconnect", "localhost", vm_name], check=True)
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

# 在新线程中运行函数
def run_in_thread(target, *args):
    thread = threading.Thread(target=target, args=args)
    thread.start()

# 查看GPU虚拟化状态
def check_gpu_virtualization_status(vm):
    try:
        # PowerShell 命令
        command = f'powershell Get-VMGpuPartitionAdapter -VMName {vm}'
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
    selected = vm_list.curselection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.get(selected[0])
    vm_name = display_text.split(" ", 1)[0]

    # 保存和取消按钮
    def save_gpu_settings():
        gpu_partition = gpu_partition_var.get()
        if gpu_partition == "获取失败或未设置":
            messagebox.showerror("错误", "您还未设置GPU分区")
            GPU_window.destroy()
            return
        low_mem: str = low_mem_var.get() or "1Gb"
        high_mem: str = high_mem_var.get() or "32GB"
        try:
            # 构建 PowerShell 命令
            ps_command = f'''
            $vm = "{vm_name}"
            $gpupath = "{gpu_partition}"
            Add-VMGpuPartitionAdapter -VMName $vm -InstancePath $gpupath
            Set-VMGpuPartitionAdapter -VMName $vm -MinPartitionVRAM 80000000 -MaxPartitionVRAM 100000000 -OptimalPartitionVRAM 100000000 -MinPartitionEncode 80000000 -MaxPartitionEncode 100000000 -OptimalPartitionEncode 100000000 -MinPartitionDecode 80000000 -MaxPartitionDecode 100000000 -OptimalPartitionDecode 100000000 -MinPartitionCompute 80000000 -MaxPartitionCompute 100000000 -OptimalPartitionCompute 100000000
            Set-VM -GuestControlledCacheTypes $true -VMName $vm
            Set-VM -LowMemoryMappedIoSpace {low_mem} -VMName $vm
            Set-VM -HighMemoryMappedIoSpace {high_mem} -VMName $vm
            '''
            # 执行 PowerShell 命令
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            messagebox.showinfo("成功", "GPU 虚拟化设置已保存。")
            GPU_window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"设置 GPU 虚拟化失败：{e}")
            logging.error(f"设置 GPU 虚拟化失败: {e}")

    # 添加查询 GPU 分区的按钮
    def query_gpu_partitions():
        try:
            # 执行 PowerShell 命令获取 GPU 分区信息
            command = 'Get-VMHostPartitionableGpu | Select-Object Name | Format-Table -AutoSize'
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(result.stderr)
            
            # 解析输出获取 Name 值
            gpu_paths = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Name') and not line.startswith('-'):
                    gpu_paths.append(line)

            if not gpu_paths:
                messagebox.showwarning("警告", "未找到可用的 GPU 分区。")
                return

            # 创建选择窗口
            select_window = tk.Toplevel(GPU_window)
            select_window.title("选择 GPU")
            select_window.minsize(400, 300)

            main_frame = tk.Frame(select_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            main_frame.grid_columnconfigure(0, weight=1)
            main_frame.grid_rowconfigure(1, weight=1)

            tk.Label(main_frame, text="请选择要使用的 GPU分区：").grid(row=0, column=0, sticky="w")
            gpu_listbox = tk.Listbox(main_frame)
            gpu_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

            button_frame = tk.Frame(main_frame)
            button_frame.grid(row=2, column=0, sticky="ew", pady=5)
            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)

            for path in gpu_paths:
                gpu_listbox.insert(tk.END, path)

            def on_select():
                selection = gpu_listbox.curselection()
                if selection:
                    selected_gpu = gpu_paths[selection[0]]
                    gpu_partition_var.set(selected_gpu)
                select_window.destroy()

            def open_device_manager():
                try:
                    subprocess.Popen(['cmd', '/c', 'start', 'devmgmt.msc'])
                except Exception as e:
                    messagebox.showerror("错误", f"无法打开设备管理器: {str(e)}")

            # 添加双击事件绑定
            gpu_listbox.bind('<Double-Button-1>', lambda e: on_select())
            tk.Button(main_frame, text="打开设备管理器", command=open_device_manager).grid(row=0, column=0, sticky="e")
            tk.Button(button_frame, text="确定", command=on_select).grid(row=2, column=0, sticky="nw", padx=5, pady=5)
            tk.Button(button_frame, text="取消", command=lambda:select_window.destroy()).grid(row=2, column=0, sticky="ne", padx=5, pady=5)
            center_window(select_window)

        except Exception as e:
            messagebox.showerror("错误", f"查询 GPU 分区失败：{e}")
            logging.error(f"查询 GPU 分区失败: {e}")
    
    def delete():
        confirm = messagebox.askyesno("确认", "您确定要 删除 这个虚拟机的GPU分区吗？")
        if confirm:
            try:
                # PowerShell 命令
                command = f'powershell Remove-VMGpuPartitionAdapter -VMName {vm_name}'
                subprocess.run(["powershell", "-Command", command], check=True)
                messagebox.showinfo("成功", "GPU 分区已删除。")
                GPU_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"删除 GPU 分区失败：{e}")
                logging.error(f"删除 GPU 分区失败: {e}")
                return False
        else:
            messagebox.showinfo("取消","你取消了删除GPU分区!!")
            GPU_window.destroy()

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
            ctypes.windll.shell32.ShellExecuteW(None,"runas", sys.executable, __file__, None, 0)
            exit()
        else:
            messagebox.showinfo("取消","你取消了管理员权限重启!\n可能会设置失败!")
            GPU_window.destroy()
    
    GPU_window = tk.Toplevel(root)
    if is_admin():
        GPU_window.title("GPU 虚拟化(管理员)")
    else:
        GPU_window.title("GPU 虚拟化(低权限)")
    GPU_window.minsize(500, 240)  # 设置最小窗口大小
    # 创建主框架
    main_frame = tk.Frame(GPU_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 配置网格权重
    main_frame.grid_columnconfigure(1, weight=1)  # 使输入框可以水平扩展
    main_frame.grid_rowconfigure(1, weight=1)     # 让列表框可以垂直扩展


    # 标题行
    title_frame = tk.Frame(main_frame)
    title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
    title_frame.grid_columnconfigure(0, weight=1)
    title_frame.grid_columnconfigure(1, weight=1)

    tk.Label(title_frame, text=f"当前虚拟机: {vm_name}").grid(row=0, column=0, sticky="w")
    tk.Button(title_frame, text="获取管理员权限", command=get_administrator_privileges).grid(row=0, column=1, sticky="e")

    # 其他控件使用相对布局
    tk.Label(main_frame, text="GPU 分区路径：").grid(row=1, column=0, sticky="e", pady=5)
    gpu_partition_var = tk.StringVar(value="获取中,请稍候.....")

    tk.Entry(main_frame, textvariable=gpu_partition_var, state='readonly').grid(row=1, column=1, sticky="ew", padx=5)

    # 自动获取 GPU 虚拟化状态并填入 GPU 分区路径
    gpu_status = check_gpu_virtualization_status(vm_name)
    if gpu_status and "InstancePath" in gpu_status:
        gpu_partition_var.set(gpu_status["InstancePath"])
    else:
        gpu_partition_var.set("获取失败或未设置")

    tk.Label(main_frame, text="显存映射一般默认即可").grid(row=2, column=0)
    # 创建按钮但不立即显示
    delete_button = tk.Button(main_frame, text="删除 GPU 分区", command=delete)
    select_button = tk.Button(main_frame, text="选择 GPU 分区", command=query_gpu_partitions)
    
    # 根据条件显示或隐藏按钮
    if gpu_status and "InstancePath" in gpu_status:
        # GPU 已配置，显示删除按钮，隐藏选择按钮
        delete_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")
        select_button.grid_remove()
    else:
        # GPU 未配置，显示选择按钮，隐藏删除按钮
        select_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")
        delete_button.grid_remove()

    # 添加输入框用于设置显存映射空间大小
    tk.Label(main_frame, text="显存映射空间最小:").grid(row=3, column=0, sticky="e")
    low_mem_var = tk.StringVar(value="1Gb")
    tk.Entry(main_frame, textvariable=low_mem_var).grid(row=3, column=1, sticky="w")
    tk.Label(main_frame, text="显存映射空间最大").grid(row=4, column=0, sticky="e")
    high_mem_var = tk.StringVar(value="32GB")
    tk.Entry(main_frame, textvariable=high_mem_var).grid(row=4, column=1, sticky="w")
    tk.Button(main_frame, text="保存", command=save_gpu_settings).grid(row=5, column=0, pady=15)
    tk.Button(main_frame, text="取消", command=lambda:GPU_window.destroy()).grid(row=5, column=1)

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
root.minsize(300, 300)  # 设置最小窗口大小

# 创建状态框架
status_frame = tk.Frame(root)
status_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

# 创建标题框架
title_frame = tk.Frame(status_frame)
title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
title_frame.grid_columnconfigure(0, weight=1)
title_frame.grid_columnconfigure(1, weight=1)

# 添加提示标签到标题框架
tk.Label(title_frame, text="名称:", justify=tk.LEFT).grid(row=0, column=0, sticky="w")
tk.Label(title_frame, text="状态", justify=tk.LEFT).grid(row=0, column=0, sticky="e")
tk.Label(title_frame, text="工具", justify=tk.LEFT).grid(row=0, column=1, sticky="e")

# 配置网格权重
status_frame.grid_columnconfigure(0, weight=3)  # 列表框占更多空间
status_frame.grid_columnconfigure(1, weight=1)  # 按钮占更少空间
status_frame.grid_rowconfigure(1, weight=1)     # 让列表框可以垂直扩展

# 创建虚拟机状态列表框
vm_list = tk.Listbox(status_frame)
vm_list.grid(row=1, column=0, rowspan=4, sticky="nsew", padx=5, pady=5)
# 添加双击事件绑定
vm_list.bind('<Double-Button-1>', lambda e: run_in_thread(set_gpu_virtualization))

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

# 添加按钮
save_button = tk.Button(status_frame, text="打开日志文件夹", command=open_config_folder)
save_button.grid(row=7, column=0, padx=5, pady=10, sticky="w")

# 添加取消按钮
save_button = tk.Button(status_frame, text="关闭", command=exit)
save_button.grid(row=7, column=1, padx=5, pady=10, sticky="ew")

# 设置窗口居中
center_window(root)

# 主循环
root.mainloop()