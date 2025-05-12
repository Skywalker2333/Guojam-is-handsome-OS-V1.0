
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
from PIL import Image, ImageTk
import io
import os
class ControlOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Guojam is handsome OS V1.0")
        self.geometry("1024x768")
        self.host = 'Your_Host'
        self.port = 34567 # 远程端口
        self.secret_key = '12345'
        self.create_widgets()
    def create_widgets(self):
        # 控制面板
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, fill='x')
        buttons = [
            (" 截取屏幕", self.capture_screen),
            ("⚙️ 执行命令", self.execute_command),
            (" 发送消息", self.send_message),
            (" 上传文件", self.upload_file),
            (" 下载文件", self.download_file)
        ]
        for idx, (text, cmd) in enumerate(buttons):
            ttk.Button(control_frame, text=text, command=cmd).grid(row=0, column=idx, padx=5)
        # 截图显示区
        self.screen_frame = ttk.LabelFrame(self, text="实时屏幕预览")
        self.screen_frame.pack(pady=10, expand=True, fill='both')
        self.canvas = tk.Canvas(self.screen_frame)
        self.canvas.pack(expand=True, fill='both')
        # 命令输入区
        self.cmd_entry = ttk.Entry(self, width=70)
        self.cmd_entry.pack(pady=5, fill='x', padx=10)
        self.cmd_entry.insert(0, "输入系统命令...")
        # 文件传输区
        file_frame = ttk.Frame(self)
        file_frame.pack(fill='x', pady=5)
        ttk.Label(file_frame, text="本地路径:").pack(side='left')
        self.local_path = ttk.Entry(file_frame, width=30)
        self.local_path.pack(side='left', padx=5)
        ttk.Label(file_frame, text="远程路径:").pack(side='left')
        self.remote_path = ttk.Entry(file_frame, width=30)
        self.remote_path.pack(side='left', padx=5)
    def send_request(self, command):
        """发送命令并接收响应"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15)
                s.connect((self.host, self.port))
                full_cmd = f"{self.secret_key}:{command}"
                s.sendall(full_cmd.encode())
                response = b''
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                return response
        except Exception as e:
            return f"连接错误: {e}".encode()
    def capture_screen(self):
        response = self.send_request('screenshot')
        if response.startswith(b'Error'):
            messagebox.showerror("错误", response.decode())
            return
        try:
            img = Image.open(io.BytesIO(response))
            img.thumbnail((1000, 800))
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor='nw', image=self.tk_img)
        except Exception as e:
            messagebox.showerror("错误", f"图片解析失败: {e}")
    def execute_command(self):
        cmd = self.cmd_entry.get()
        if not cmd or cmd == "输入系统命令...":
            return
        response = self.send_request(f'execute:{cmd}')
        messagebox.showinfo("执行结果", response.decode())
    def send_message(self):
        title = self.remote_path.get() or "系统通知"
        content = self.local_path.get()
        if not content:
            messagebox.showwarning("警告", "消息内容不能为空")
            return
        response = self.send_request(f'messagebox:{title}:{content}')
        messagebox.showinfo("状态", response.decode())
    def upload_file(self):
        local_path = filedialog.askopenfilename()
        if not local_path:
            return
        remote_path = self.remote_path.get() or os.path.basename(local_path)
        self.local_path.delete(0, tk.END)
        self.local_path.insert(0, local_path)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(f"{self.secret_key}:upload:{remote_path}".encode())
                if s.recv(1024) != b'START_UPLOAD':
                    raise Exception("服务端未就绪")
                file_size = os.path.getsize(local_path)
                s.send(str(file_size).encode())
                if s.recv(1024) == b'READY':
                    with open(local_path, 'rb') as f:
                        while True:
                            data = f.read(4096)
                            if not data:
                                break
                            s.sendall(data)
                    result = s.recv(1024).decode()
                    messagebox.showinfo("上传结果", result)
        except Exception as e:
            messagebox.showerror("错误", f"上传失败: {str(e)}")
    def download_file(self):
        remote_path = self.remote_path.get()
        if not remote_path:
            messagebox.showwarning("警告", "请输入远程文件路径")
            return
        local_path = filedialog.asksaveasfilename(
            initialfile=os.path.basename(remote_path))
        if not local_path:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(f"{self.secret_key}:download:{remote_path}".encode())
                file_size = int(s.recv(1024).decode())
                s.send(b'READY')
                received = 0
                with open(local_path, 'wb') as f:
                    while received < file_size:
                        data = s.recv(4096)
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                if received == file_size:
                    messagebox.showinfo("成功", "文件下载完成")
                else:
                    messagebox.showerror("错误", f"下载不完整 ({received}/{file_size} bytes)")
        except Exception as e:
            messagebox.showerror("错误", f"下载失败: {str(e)}")
if __name__ == '__main__':
    app = ControlOS()
    app.mainloop()

