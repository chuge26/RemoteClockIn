import tkinter as tk
from tkinter import filedialog, messagebox
import configparser
from pathlib import Path

CONFIG_PATH = Path.cwd() / "config.ini"
SECTION = "SETTINGS"

# 默认图片路径
DEFAULT_ICONS = {
    "work_icon": "Assets/Icon1.png",
    "ask_for_leave_icon": "Assets/ask_for_leave.png",
    "password_page": "Assets/password_expired.png",
    "totalcontrol_icon": "Assets/TotalControl.png",
    "work_entry": "Assets/WorkEntry.png",
    "check_in_icon": "Assets/check_in.png",
    "check_out_icon": "Assets/check_out.png",
    "login_button": "Assets/login.png",
    "bound_button": "Assets/bound.jpg",
    "update_button": "Assets/update.png",
    "agree_button": "Assets/agree.png",
    "screenshot": "Assets/screen.png"
}

class ConfigGUI:
    def __init__(self, master):
        self.master = master
        master.title("签到参数设置")

        self.cfg = configparser.ConfigParser()
        self.cfg.read(CONFIG_PATH, encoding='utf-8')
        if SECTION not in self.cfg:
            self.cfg[SECTION] = {}

        # 图片路径设置
        self.icon_vars = {}
        row = 0
        for key, label in DEFAULT_ICONS.items():
            tk.Label(master, text=key).grid(row=row, column=0, sticky="e")
            var = tk.StringVar(value=self.cfg[SECTION].get(key, label))
            entry = tk.Entry(master, textvariable=var, width=40)
            entry.grid(row=row, column=1)
            btn = tk.Button(master, text="选择", command=lambda k=key, v=var: self.choose_file(k, v))
            btn.grid(row=row, column=2)
            self.icon_vars[key] = var
            row += 1

        # 邮箱
        tk.Label(master, text="邮箱").grid(row=row, column=0, sticky="e")
        self.email_var = tk.StringVar(value=self.cfg[SECTION].get("邮箱", ""))
        tk.Entry(master, textvariable=self.email_var, width=40).grid(row=row, column=1, columnspan=2)
        row += 1

        # 激活码
        tk.Label(master, text="激活码").grid(row=row, column=0, sticky="e")
        self.license_var = tk.StringVar(value=self.cfg[SECTION].get("激活码", ""))
        tk.Entry(master, textvariable=self.license_var, width=40).grid(row=row, column=1, columnspan=2)
        row += 1

        # 上午打卡区间
        tk.Label(master, text="上午打卡区间").grid(row=row, column=0, sticky="e")
        self.morning_var = tk.StringVar(value=self.cfg[SECTION].get("上午打卡区间", "08:00-08:58"))
        tk.Entry(master, textvariable=self.morning_var, width=20).grid(row=row, column=1, columnspan=2)
        row += 1

        # 下午打卡区间
        tk.Label(master, text="下午打卡区间").grid(row=row, column=0, sticky="e")
        self.evening_var = tk.StringVar(value=self.cfg[SECTION].get("下午打卡区间", "17:30-18:10"))
        tk.Entry(master, textvariable=self.evening_var, width=20).grid(row=row, column=1, columnspan=2)
        row += 1

        # 保存按钮
        tk.Button(master, text="确定", command=self.save).grid(row=row, column=0, columnspan=3, pady=10)

    def choose_file(self, key, var):
        path = filedialog.askopenfilename(title="选择图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if path:
            var.set(path)

    def save(self):
        for key, var in self.icon_vars.items():
            self.cfg[SECTION][key] = var.get()
        self.cfg[SECTION]["邮箱"] = self.email_var.get()
        self.cfg[SECTION]["激活码"] = self.license_var.get()
        self.cfg[SECTION]["上午打卡区间"] = self.morning_var.get()
        self.cfg[SECTION]["下午打卡区间"] = self.evening_var.get()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self.cfg.write(f)
        messagebox.showinfo("保存成功", "配置已保存！")
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()