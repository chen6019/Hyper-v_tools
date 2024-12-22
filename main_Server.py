"""
打包指令:
pyinstaller -F -n Server --noconsole main_Server.py
"""


import ctypes
import json
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox,filedialog
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

# 添加一个通用的创建隐藏终端的 startupinfo
def create_hidden_startupinfo():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo

def show_vm_status():
    # PowerShell 命令获取虚拟机状态
    ps_command = "Get-VM | Select-Object Name, State | Format-Table -AutoSize"
    
    # 调用 PowerShell 命令
    result = subprocess.run(["powershell", "-Command", ps_command], 
                          capture_output=True, 
                          text=True,
                          startupinfo=create_hidden_startupinfo())
    
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
    vm_list.delete(*vm_list.get_children())
    for name, state in zip(names, states):
        display_text = f"{name} {state}"
        vm_list.insert('', 'end', text=display_text)

# 定义启动虚拟机的工作函数
def start_vm_process(vm_name):
    try:
        subprocess.run(["PowerShell", "Start-VM", "-Name", vm_name], 
                      check=True,
                      startupinfo=create_hidden_startupinfo())
        logging.info(f"虚拟机 {vm_name} 已启动。")
    except subprocess.CalledProcessError as e:
        logging.error(f"启动虚拟机 {vm_name} 失败: {e}")

# 定义关闭虚拟机的工作函数
def stop_vm_process(vm_name):
    try:
        # 使用 PowerShell 强制关闭虚拟机
        subprocess.run(["powershell", "-Command", f"Stop-VM -Name '{vm_name}' -Force"], 
                      check=True,
                      startupinfo=create_hidden_startupinfo())
        logging.info(f"虚拟机 {vm_name} 已强制关闭。")
    except subprocess.CalledProcessError as e:
        logging.error(f"强制关闭虚拟机 {vm_name} 失败: {e}")
        messagebox.showerror("错误", f"强制关闭虚拟机 {vm_name} 失败。\n{e}")

# 修改 start_vm 函数
def start_vm():
    selected = vm_list.selection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.item(selected[0], 'text')
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分
    
    run_in_thread(start_vm_process, vm_name)
    
    messagebox.showinfo("启动中", f"虚拟机 {vm_name} 正在启动。")
    refresh_vm_status()

# 修改 stop_vm 函数
def stop_vm():
    selected = vm_list.selection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.item(selected[0], 'text')
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分

    # 弹出确认对话框
    confirm = messagebox.askyesno("确认", f"确定要强制关闭虚拟机 {vm_name} 吗？")
    if not confirm:
        return
    stop_vm_process(vm_name)
    messagebox.showinfo("关闭中", f"正在强制关闭虚拟机 {vm_name} 。")
    refresh_vm_status()

# 打开虚拟机远程连接
def open_vm_connect():
    selected = vm_list.selection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.item(selected[0], 'text')
    vm_name = display_text.split(" ", 1)[0]  # 获取名称部分

    try:
        # 使用 vmconnect 打开特定虚拟机的远程连接界面
        subprocess.run(["vmconnect", "localhost", vm_name], 
                      check=True,
                      startupinfo=create_hidden_startupinfo())
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
        result = subprocess.run(command, 
                              capture_output=True, 
                              text=True,
                              shell=True,
                              startupinfo=create_hidden_startupinfo())
        
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
    selected = vm_list.selection()
    if not selected:
        messagebox.showwarning("警告", "请选择一个虚拟机。")
        return
    display_text = vm_list.item(selected[0], 'text')
    vm_name = display_text.split(" ", 1)[0]

    # 保存和取消按钮
    def save_gpu_settings():
        gpu_partition = gpu_partition_var.get()
        if gpu_partition == "获取失败或未设置":
            messagebox.showerror("错误", "您还未设置GPU分区")
            GPU_window.destroy()
            return
        low_mem: str = str(low_mem_var.get() or 1)
        high_mem: str = str(high_mem_var.get() or 32)
        low_mem = low_mem + "GB"
        logging.info(f"设置显存映射空间最小: {low_mem}")
        high_mem = high_mem + "GB"
        logging.info(f"设置显存映射空间最大: {high_mem}")
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
            subprocess.run(["powershell", "-Command", ps_command], 
                         check=True,
                         startupinfo=create_hidden_startupinfo())
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
            result = subprocess.run(["powershell", "-Command", command], 
                                   capture_output=True, 
                                   text=True,
                                   startupinfo=create_hidden_startupinfo())
            
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

            main_frame = ttk.Frame(select_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            main_frame.grid_columnconfigure(0, weight=1)
            main_frame.grid_rowconfigure(1, weight=1)

            ttk.Label(main_frame, text="请选择要使用的 GPU分区：").grid(row=0, column=0, sticky="w")
            gpu_listbox = tk.Listbox(main_frame)
            gpu_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

            button_frame = ttk.Frame(main_frame)
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
            ttk.Button(main_frame, text="打开设备管理器", command=open_device_manager).grid(row=0, column=0, sticky="e")
            ttk.Button(button_frame, text="确定", command=on_select).grid(row=2, column=0, sticky="nw", padx=5, pady=5)
            ttk.Button(button_frame, text="取消", command=lambda:select_window.destroy()).grid(row=2, column=0, sticky="ne", padx=5, pady=5)
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
                subprocess.run(["powershell", "-Command", command], 
                              check=True,
                              startupinfo=create_hidden_startupinfo())
                messagebox.showinfo("成功", "GPU 分区已删除。")
                GPU_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"删除 GPU 分区失败：{e}")
                logging.error(f"删除 GPU 分区失败: {e}")
                return False
        else:
            messagebox.showinfo("取消","你取消了删除GPU分区!!")
            GPU_window.destroy()

    # GPU 选择驱动路径
    def select_gpu_driver_path():
        messagebox.showwarning("提示", "这个功能还没有写好\n目前没有任何作用\n需要在以后加入自动更新驱动后可用")
        return
        directory_path = filedialog.askdirectory()
        if directory_path:
            gpu_driver_var.set(directory_path)
        else:
            messagebox.showwarning("提示", "未选择任何文件夹。")

    def save_config(vm_name):
        messagebox.showwarning("提示", "这个功能还没有写好\n设置GPU虚拟化也用不到这个\n需要在以后加入自动更新驱动后才可用")
        return
        try:
            #判断GPU分区是否为错误文本
            if gpu_partition_var.get() == "获取失败或未设置":
                toast.config(text=f"{vm_name} 保存配置失败：GPU分区未设置")
                return
            # 创建配置字典
            config = {
                "vm_name": vm_name,
                "gpu_partition": gpu_partition_var.get(),
                "gpu_driver": gpu_driver_var.get(),
                "low_mem": low_mem_var.get(),
                "high_mem": high_mem_var.get()
            }
            # 保存配置到 JSON 文件
            with open(f"{appdata_path}\\{vm_name}_config.json", "w") as f:
                json.dump(config, f, indent=4)
            toast.config(text=f"{vm_name} 配置已保存。")
            logging.info(f"{vm_name} 配置已保存。")
        except ValueError as ve:
            messagebox.showerror("错误", "保存配置失败：值错误或输入错误")
            logging.error(f"保存配置失败: 值错误或输入错误{ve}")
        except Exception as e:
            messagebox.showerror("错误", "保存配置失败：未知错误")
            logging.error(f"保存配置失败: {e}")
    
    def check(vm_name):
        try:
            # 读取配置文件
            config_path = f"{appdata_path}\\{vm_name}_config.json"
            if os.path.getsize(config_path) == 0:
                raise ValueError("配置文件为空")
            
            with open(config_path, "r") as f:
                config = json.load(f)
                # 设置 Tkinter 变量
                gpu_partition_var.set(config.get("gpu_partition", ""))
                gpu_driver_var.set(config.get("gpu_driver", ""))
                low_mem_var.set(config.get("low_mem", 1))
                high_mem_var.set(config.get("high_mem", 32))
                logging.info(f"{vm_name}配置成功读取")
                toast.config(text=f"{vm_name}配置成功读取")
        except FileNotFoundError:
            logging.info(f"{vm_name}配置文件未找到")
            toast.config(text=f"{vm_name}配置文件未找到")
        except json.JSONDecodeError:
            logging.error(f"{vm_name}配置文件格式错误")
            toast.config(text=f"{vm_name}配置文件格式错误")
        except ValueError as ve:
            logging.error(f"{vm_name}配置文件错误: 值错误!")
            toast.config(text=f"{vm_name}配置文件错误: {ve}")
        except Exception as e:
            logging.error(f"读取{vm_name}配置出错: {e}")
            toast.config(text=f"读取{vm_name}配置出错：未知错误!")
    
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
    GPU_window.minsize(500, 260)  # 设置最小窗口大小
    # 创建主框架
    main_frame = ttk.Frame(GPU_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 配置网格权重
    main_frame.grid_columnconfigure(1, weight=1)  # 使输入框可以水平扩展
    main_frame.grid_rowconfigure(1, weight=1)     # 让列表框可以垂直扩展


    # 标题行
    title_frame = ttk.Frame(main_frame)
    title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
    title_frame.grid_columnconfigure(0, weight=1)
    title_frame.grid_columnconfigure(1, weight=1)

    toast = ttk.Label(title_frame, text="加载中......",style="i.TLabel")
    toast.grid(row=0,column=0,sticky="w")

    admin_button = ttk.Button(title_frame, text="获取管理员权限", command=get_administrator_privileges,style="e.TButton")
    admin_button.grid(row=0, column=2, sticky="e")
    if is_admin():
        admin_button.grid_remove()

    # 其他控件使用相对布局
    ttk.Label(main_frame, text="GPU 分区路径：").grid(row=1, column=0, sticky="e", pady=5)
    gpu_partition_var = tk.StringVar(value="获取中,请稍候.....")
    ttk.Entry(main_frame, textvariable=gpu_partition_var, state='readonly').grid(row=1, column=1, sticky="ew", padx=5)

    # 自动获取 GPU 虚拟化状态并填入 GPU 分区路径
    gpu_status = check_gpu_virtualization_status(vm_name)
    if gpu_status and "InstancePath" in gpu_status:
        gpu_partition_var.set(gpu_status["InstancePath"])
    else:
        gpu_partition_var.set("获取失败或未设置")

    # 显示映射一般默认即可的标签移到row=4
    ttk.Label(main_frame, text="内存映射I/O空间一般默认即可").grid(row=4, column=0,sticky="es")
    
    # 删除和选择GPU分区按钮移到row=2
    delete_button = ttk.Button(main_frame, text="删除 GPU 分区", command=delete)
    select_button = ttk.Button(main_frame, text="选择 GPU 分区", command=query_gpu_partitions)
    if gpu_status and "InstancePath" in gpu_status:
        delete_button.grid(row=1, column=1, padx=5, sticky="e")
        select_button.grid_remove()
    else:
        select_button.grid(row=1, column=1, padx=5, sticky="e")
        delete_button.grid_remove()
    
    # 添加GPU驱动路径选择
    ttk.Label(main_frame, text="GPU 驱动路径：").grid(row=3, column=0, sticky="e", pady=5)
    gpu_driver_var = tk.StringVar(value="")
    ttk.Entry(main_frame, textvariable=gpu_driver_var, state='readonly').grid(row=3, column=1, sticky="ew", padx=5)
    ttk.Button(main_frame, text="选择路径", command=select_gpu_driver_path).grid(row=3, column=1, sticky="e")

    # 显存映射空间设置移到row=5和6
    def validate_int_input(P):
        if P.isdigit() or P == "":
            return True
        else:
            return False
    
    vcmd = (root.register(validate_int_input), '%P')
    
    ttk.Label(main_frame, text="内存映射I/O空间最小:").grid(row=5, column=0, sticky="e")
    ttk.Label(main_frame, text="GB").grid(row=5, column=1, sticky="s")
    low_mem_var = tk.IntVar(value=1)
    ttk.Entry(main_frame, textvariable=low_mem_var, validate="key", validatecommand=vcmd).grid(row=5, column=1, sticky="w")
    
    ttk.Label(main_frame, text="内存映射I/O空间最大:").grid(row=6, column=0, sticky="e")
    ttk.Label(main_frame, text="GB").grid(row=6, column=1, sticky="s")
    high_mem_var = tk.IntVar(value=32)
    ttk.Entry(main_frame, textvariable=high_mem_var, validate="key", validatecommand=vcmd).grid(row=6, column=1, sticky="w")
    # 保存和取消按钮移到row=7
    ttk.Button(main_frame, text="应用", command=save_gpu_settings,style="k.TButton").grid(row=7, column=0, pady=15)
    ttk.Button(main_frame, text="保存配置", command=lambda:save_config(vm_name),style="i.TButton").grid(row=7, column=1)
    ttk.Button(main_frame, text="取消", command=lambda:GPU_window.destroy(),style="e.TButton").grid(row=7, column=2)
    check(vm_name)
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

style = ttk.Style()
style.configure("i.TLabel", foreground="blue")
style.configure("e.TLabel", foreground="red")
style.configure("k.TLabel", foreground="green")
style.configure("i.TButton", foreground="blue")
style.configure("e.TButton", foreground="red")

# 创建状态框架
status_frame = ttk.Frame(root)
status_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

# 创建标题框架
title_frame = ttk.Frame(status_frame)
title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
title_frame.grid_columnconfigure(0, weight=1)
title_frame.grid_columnconfigure(1, weight=1)

# 添加提示标签到标题框架
ttk.Label(title_frame, text="名称:", justify=tk.LEFT).grid(row=0, column=0, sticky="w")
ttk.Label(title_frame, text="状态", justify=tk.LEFT).grid(row=0, column=0, sticky="e")
ttk.Label(title_frame, text="工具:", justify=tk.LEFT).grid(row=0, column=1, sticky="n")

# 配置网格权重
status_frame.grid_columnconfigure(0, weight=3)  # 列表框占更多空间
status_frame.grid_columnconfigure(1, weight=1)  # 按钮占更少空间
status_frame.grid_rowconfigure(1, weight=1)     # 让列表框可以垂直扩展

# 用 Treeview 替换原 tk.Listbox
vm_list = ttk.Treeview(status_frame, show='tree')
vm_list.grid(row=1, column=0, rowspan=4, sticky="nsew", padx=5, pady=5)
vm_list.bind('<Double-1>', lambda e: run_in_thread(set_gpu_virtualization))


# 获取虚拟机状态并显示在列表框中
vm_status = show_vm_status()
names, states = parse_vm_status(vm_status)
update_vm_list(names, states)

# 添加启动和关闭按钮到 status_frame 中
start_button = ttk.Button(status_frame, text="启动", command=lambda:run_in_thread(start_vm))
start_button.grid(row=5, column=0, padx=2, pady=5, sticky="w")

stop_button = ttk.Button(status_frame, text="关闭", command=lambda:run_in_thread(stop_vm),style="e.TButton")
stop_button.grid(row=5, column=0, padx=2, pady=5, sticky="e")

# 添加设置和关闭 GPU 虚拟化按钮到 status_frame 中
set_gpu_button = ttk.Button(status_frame, text="GPU 虚拟化", command=lambda:run_in_thread(set_gpu_virtualization))
set_gpu_button.grid(row=1, column=1, padx=5, pady=5, sticky="e")

Remote_connection_button = ttk.Button(status_frame, text="连接虚拟机", command=lambda:run_in_thread(open_vm_connect))
Remote_connection_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

settings_button = ttk.Button(status_frame, text="Hyper-V管理器", command=lambda: run_in_thread(open_hyper_v_manager))
settings_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

# 添加按钮
save_button = ttk.Button(status_frame, text="打开日志文件夹", command=open_config_folder)
save_button.grid(row=7, column=0, padx=5, pady=10, sticky="w")

# 添加取消按钮
save_button = ttk.Button(status_frame, text="关闭", command=exit)
save_button.grid(row=7, column=1, padx=5, pady=10, sticky="ew")

# 设置窗口居中
center_window(root)

# 主循环
root.mainloop()