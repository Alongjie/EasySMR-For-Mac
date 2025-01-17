import os
import json
import subprocess
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox, Listbox

from setuptools.command.easy_install import easy_install
from smb.SMBConnection import SMBConnection  # 安装库: pip install pysmb

CONFIG_FILE = os.path.join(sys._MEIPASS, "server_config.json")


class ServerAccessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("服务器访问工具")
        self.server_list = []
        self.load_config()

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        self.listbox = Listbox(self.root, height=15, width=50)
        self.listbox.pack(pady=10)

        # 按钮布局
        btn_frame = tk.Frame(self.root)
        btn_frame.pack()

        tk.Button(btn_frame, text="添加服务器", command=self.add_server).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="编辑服务器", command=self.edit_server).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除选中", command=self.delete_server).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="连接服务器", command=self.connect_server).pack(side=tk.LEFT, padx=5)

        self.update_listbox()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.server_list = json.load(f)
        else:
            self.server_list = []

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.server_list, f)

    def add_server(self):
        self.edit_server(is_new=True)

    def edit_server(self, is_new=False):
        if not is_new:
            selected = self.listbox.curselection()
            if not selected:
                messagebox.showwarning("警告", "请选择一个服务器进行编辑！")
                return
            idx = selected[0]
            server = self.server_list[idx]
        else:
            server = {"name": "", "address": "", "username": "", "password": ""}

        # 弹出输入对话框
        server["name"] = simpledialog.askstring("输入服务器信息", "服务器名称:", initialvalue=server["name"])
        server["address"] = simpledialog.askstring("输入服务器信息", "服务器地址:", initialvalue=server["address"])
        server["username"] = simpledialog.askstring("输入服务器信息", "用户名:", initialvalue=server["username"])
        server["password"] = simpledialog.askstring("输入服务器信息", "密码:", initialvalue=server["password"],
                                                    show="*")

        # 校验和保存
        if all([server["name"], server["address"], server["username"], server["password"]]):
            if is_new:
                self.server_list.append(server)
            else:
                self.server_list[idx] = server
            self.save_config()
            self.update_listbox()
        else:
            messagebox.showwarning("警告", "所有字段均为必填！")

    def delete_server(self):
        selected = self.listbox.curselection()
        if selected:
            idx = selected[0]
            del self.server_list[idx]
            self.save_config()
            self.update_listbox()
        else:
            messagebox.showwarning("警告", "请选择一个服务器进行删除！")

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for server in self.server_list:
            self.listbox.insert(tk.END, f"{server['name']} ({server['address']})")

    def connect_server(self):
        selected = self.listbox.curselection()
        if selected:
            idx = selected[0]
            server = self.server_list[idx]
            try:
                if server['address'].startswith("smb://"):
                    self.connect_smb(server)
                else:
                    messagebox.showinfo("提示", "仅支持 SMB 连接")
            except Exception as e:
                messagebox.showerror("错误", f"连接失败: {e}")
        else:
            messagebox.showwarning("警告", "请选择一个服务器进行连接！")

    def connect_smb(self, server):
        try:
            smb_conn = SMBConnection(
                server["username"], server["password"],
                "PythonClient", "SMBServer",
                use_ntlm_v2=True
            )
            address = server["address"].replace("smb://", "").split("/")
            ip = address[0]
            shared_folder = address[1] if len(address) > 1 else ""

            smb_conn.connect(ip, 139)  # 默认 SMB 端口 139
            shares = smb_conn.listShares()

            # 选择共享文件夹
            shared_names = [share.name for share in shares]
            shared_names_display = "\n".join(shared_names)
            # messagebox.showinfo("连接成功", f"可用共享文件夹:\n{shared_names_display}")

            # 示例：列出目标共享文件夹内容
            try:
                # 列出共享文件夹内容
                # files = smb_conn.listPath(shared_folder, "/")
                # file_names = [file.filename for file in files]
                # file_list_display = "\n".join(file_names)

                # 显示文件列表
                # messagebox.showinfo("文件列表", f"{shared_folder} 文件:\n{file_list_display}")

                # 构建本地挂载路径
                local_mount_point = f"/Volumes/{shared_folder}"  # 假设挂载点在 /Volumes 下

                # 检查路径是否存在，如果不存在则提示用户挂载共享文件夹
                if not os.path.exists(local_mount_point):
                    messagebox.showerror("错误",
                                         f"未找到本地挂载点 {local_mount_point}。\n请先手动挂载该共享文件夹到 /Volumes。")
                else:
                    # 使用访达打开指定路径
                    subprocess.run(["open", local_mount_point])
            except Exception as e:
                messagebox.showerror("错误", f"操作失败: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"SMB 连接失败: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerAccessApp(root)
    root.mainloop()

