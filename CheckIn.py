import os
import sys
import requests
import zipfile
import subprocess
import configparser
import time
from pathlib import Path
import msvcrt
import cv2
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re
import random
import pymysql
from config_gui import ConfigGUI
import tkinter as tk
import shutil

# 本程序用于网格通自动打卡
class Work:
    def __init__(self):
        # 加载要识别的图片
        # 获取资源路径，兼容打包为exe后的情况
        def resource_path(relative_path):
            # try:
            # # PyInstaller创建临时文件夹，并把路径存储于_MEIPASS
            #     base_path = sys._MEIPASS
            # except Exception:
            base_path = Path.cwd()
            return Path(base_path) / relative_path
        
        # 检查是否为PyInstaller打包环境
        if hasattr(sys, "_MEIPASS"):
            # 将Assets文件夹从_MEIPASS复制到当前工作目录
            assets_src = Path(sys._MEIPASS) / "Assets"
            assets_dst = Path.cwd() / "Assets"
            if not assets_dst.exists():
                try:
                    shutil.copytree(assets_src, assets_dst)
                except Exception as e:
                    print(f"复制Assets文件夹失败: {e}")
            # resource_path直接返回当前路径下的文件
            def resource_path(relative_path):
                return Path.cwd() / relative_path

        cfg = configparser.ConfigParser()
        cfg.read("config.ini", encoding="utf-8")
        section = "SETTINGS"
        get_path = lambda key, default: cfg[section].get(key, default)

        self.work_icon = get_path("work_icon", str(resource_path("Assets/Icon1.png")))
        self.password_page = get_path("password_page", str(resource_path("Assets/password_expired.png")))
        self.totalcontrol_icon = get_path("totalcontrol_icon", str(resource_path("Assets/TotalControl.png")))
        self.work_entry = get_path("work_entry", str(resource_path("Assets/WorkEntry.png")))
        self.check_in_icon = get_path("check_in_icon", str(resource_path("Assets/check_in.png")))
        self.check_out_icon = get_path("check_out_icon", str(resource_path("Assets/check_out.png")))
        self.login_button = get_path("login_button", str(resource_path("Assets/login.png")))
        self.bound_button = get_path("bound_button", str(resource_path("Assets/bound.jpg")))
        self.update_button = get_path("update_button", str(resource_path("Assets/update.png")))
        self.agree_button = get_path("agree_button", str(resource_path("Assets/agree.png")))
        self.screenshot = get_path("screenshot", str(resource_path("Assets/screen.png")))
        
        self.preset = Presetting()
        self.preset.init_system()

    def countdown(self, seconds):
        while seconds > 0:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            print(f"\r倒计时... {hours}小时{minutes}分钟{secs}秒", end='', flush=True)
            time.sleep(1)
            seconds -= 1
        print("\r等待结束!" )

    def adb_command(self, command):
        os.system(f"adb {command}")

    # 点击指定坐标
    def tap_screen(self, x, y):
        self.adb_command(f"shell input tap {x} {y}")

    # 滑动指定距离，只滑动
    def swipeonly_screen(self, start_x, start_y, end_x, end_y, duration=500):
        print("滑动屏幕中……")
        self.adb_command(f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}")
        time.sleep(1)

    # 滑动指定距离
    def swipe_screen(self, start_x, start_y, end_x, end_y, duration=500):
        print("滑动屏幕中……")
        self.adb_command(f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}")
        time.sleep(1)
        self.get_screenshot()

    def find_work_icon(self):
        self.get_screenshot()
        if not self.find_png(self.work_icon, precision=0.7):
            check_icon = False
            self.adb_command("shell input keyevent 3")
            self.adb_command("shell input keyevent 3")
            self.adb_command("shell input keyevent 3")
            while not check_icon:
                self.swipe_screen(800, 1000, 200, 1000)
                check_icon = self.find_png(self.work_icon, precision=0.7)

    # 点击登录界面
    def login_page(self):
        self.get_screenshot()
        print("正在搜索登录按键")
        time.sleep(2)
        self.find_png(self.login_button, precision=0.7)

    # 点击更新
    def update_page(self):
        self.get_screenshot()
        print("正在搜索更新按键")
        time.sleep(2)
        coords = self.find_image_on_screen(self.update_button, precision=0.7)
        if coords:
            x1, y1 = coords
            # 点击icon.png中心
            self.tap_screen(x1+200, y1+300)
            time.sleep(1)
            print('更新中……')
            time.sleep(120)
            self.tap_screen(530, 2200)
            time.sleep(10)
            self.tap_screen(530, 2100)
            time.sleep(5)

    # 协议相关页面
    def agreement_page(self):
        self.get_screenshot()
        print("正在搜索同意按键")
        time.sleep(2)
        self.find_png(self.agree_button, precision=0.85)

    # 点击绑定界面
    def bound_page(self):
        self.get_screenshot()
        print("正在搜索绑定按键")
        time.sleep(2)
        self.find_png(self.bound_button, precision=0.6)

    # 点击密码过期提示
    def password_expired_page(self):
        time.sleep(2)
        self.get_screenshot()
        print("正在搜索密码过期提示")
        time.sleep(2)
        coords = self.find_image_on_screen(self.password_page, precision=0.7)
        if coords:
            x1, y1 = coords
            # 点击icon.png中心
            self.tap_screen(x1+380, y1+130)
            time.sleep(1)

    # 进入TotalControl页面
    def total_control_page(self):
        self.get_screenshot()
        time.sleep(2)
        print("正在搜索TotalControl入口")
        self.find_png(self.totalcontrol_icon)
        time.sleep(1)

    # 进入签到页面
    def check_in_page(self):
        time.sleep(5)
        self.get_screenshot()
        time.sleep(2)
        print("正在搜索签到入口")
        self.find_png(self.work_entry)
        time.sleep(1)

    # 上班签到
    def check_in(self):
        print("正在搜索签到按键")
        self.find_png(self.check_in_icon, precision=0.6)

    # 下班签到
    def check_out(self):
        print("正在搜索签到按键")
        self.find_png(self.check_out_icon)

    # 退出签到页面，返回上一级后回主页面并息屏
    def check_out_page(self):
        print("返回上级界面并准备休眠")
        self.tap_screen(100, 100)
        self.adb_command("shell input keyevent 3")
        time.sleep(1)

    # 获取屏幕截图
    def get_screenshot(self):
        print("获取截图中……")
        self.adb_command("shell screencap -p /sdcard/screen.png")
        time.sleep(1)
        print('上传截图至电脑中……')
        self.adb_command(r"pull /sdcard/screen.png {}".format(self.screenshot))
        time.sleep(1)

    # 查找目标图片
    def find_image_on_screen(self, template_path, precision=0.8):
        screenshot_path = self.screenshot
        print("正在从当前截图寻找目标…… | 目标名称：{}".format(template_path))
        if not os.path.exists(screenshot_path):
            print(f"Screenshot file {screenshot_path} does not exist.")
            return None

        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(template_path)

        # 检查图像是否成功读取
        while screenshot is None:
            print(f"Failed to read screenshot {screenshot_path}.")
            print('retry...')
            self.adb_command('reboot')
            print('重启手机中……')
            time.sleep(120)
            self.preset.run()
            self.get_screenshot()
            screenshot = cv2.imread(screenshot_path)

        if template is None:
            print(f"Failed to read template {template_path}.")
            return None

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print('目标识别匹配度:', max_val)
        if max_val > precision:  # 设定一个匹配阈值
            print("找到匹配目标！")
            template_height, template_width = template.shape[:2]
            center_x = max_loc[0] + template_width/2
            center_y = max_loc[1] + template_height/2
            return center_x, center_y
        print("未找到匹配目标！")
        return None

    # 点击指定图片
    def find_png(self, png, screenshot_path="", precision=0.8):
        screenshot_path = self.screenshot
        print("正在从当前截图寻找目标…… | 目标名称：{}".format(png))
        print("screenshot_path:", screenshot_path)
        coords = self.find_image_on_screen(png, precision)
        if coords:
            x1, y1 = coords
            # 点击icon.png中心
            self.tap_screen(x1, y1)
            time.sleep(1)
            return True

    # 息屏
    def sleep(self):
        self.adb_command("shell input keyevent KEYCODE_POWER")

    # 获取不用上班的日期
    def relax_day(self):
        current_year = datetime.datetime.now().year
        text_path = Path.cwd() / "relax.txt"
        if not text_path.exists():
            with open(text_path, 'w') as f:
                f.write("请在下方分割线后输入后续休息日日期，格式示例：\n6.9\n6.11\n----------分割线----------")
        with open(text_path, 'r') as file:
            dates = file.readlines()[4:]
            dates = [f"{current_year}.{day}" for day in dates]
        # 去掉每行的换行符并转换为datetime.date对象
        dates = [datetime.datetime.strptime(date.strip(), "%Y.%m.%d").date() for date in dates]
        # print(dates)
        return dates

    # 计算当前时间与上午、下午打卡区间开始时间的时间差，决定等待时间
    def get_next_checkin_time(self, now, morning_range, evening_range):
        today = now.date()
        start_morning = datetime.datetime.combine(today, datetime.datetime.strptime(morning_range[0], "%H:%M").time())
        end_morning = datetime.datetime.combine(today, datetime.datetime.strptime(morning_range[1], "%H:%M").time())
        start_evening = datetime.datetime.combine(today, datetime.datetime.strptime(evening_range[0], "%H:%M").time())
        end_evening = datetime.datetime.combine(today, datetime.datetime.strptime(evening_range[1], "%H:%M").time())

        if start_morning <= now <= end_morning or start_evening <= now <= end_evening:
            return now  # 立即打卡
        elif now < start_morning:
            return start_morning
        elif now < start_evening:
            return start_evening
        else:
            # 已过所有打卡时间，等待到明天上午
            return start_morning + datetime.timedelta(days=1)

    # 主程序
    def main(self):
        
        moring_check_in = self.preset.cfg[self.preset.SECTION].get("上午打卡区间") 
        evening_check_in = self.preset.cfg[self.preset.SECTION].get("下午打卡区间")
        self.preset.run()
        self.sleep()
        print(f"当前打卡时间段为：{moring_check_in} | {evening_check_in}")
        # 询问用户是否使用当前打卡时间
        print(f"当前打卡时间段为：上午 {moring_check_in} | 下午 {evening_check_in}")
        use_default = input("是否使用以上打卡时间？(Y/N): ").strip().lower()
        if use_default != 'y':
            print(f"请在 {self.preset.CONFIG_PATH} 文件中修改 '上午打卡区间' 和 '下午打卡区间'，修改后保存。")
            os.startfile(self.preset.CONFIG_PATH)
            input("修改完成后按回车键继续...")
            self.preset.cfg.read(self.preset.CONFIG_PATH, encoding='utf-8')
            moring_check_in = self.preset.cfg[self.preset.SECTION].get("上午打卡区间")
            evening_check_in = self.preset.cfg[self.preset.SECTION].get("下午打卡区间")
            print(f"已读取最新打卡时间段：上午 {moring_check_in} | 下午 {evening_check_in}")
        

        morning_range = moring_check_in.split('-')
        evening_range = evening_check_in.split('-')

        last_checkin_date = {"morning": None, "evening": None}
        while True:
            time_now = datetime.datetime.now()
            current_date = time_now.date()
            current_time = time_now.time()
            print("当前时间：", time_now.strftime("%Y-%m-%d %H:%M:%S"))

            next_checkin_time = self.get_next_checkin_time(time_now, morning_range, evening_range)
            wait_seconds = (next_checkin_time - time_now).total_seconds()
            random_seconds = random.randint(0, 300)  # 随机等待0-300秒
            if wait_seconds > 0:
                total_wait = int(wait_seconds + random_seconds)
                hours = total_wait // 3600
                minutes = (total_wait % 3600) // 60
                if hours > 0:
                    print(f"距离下一次打卡开始还有 {hours} 小时 {minutes} 分钟，等待中...")
                    # time.sleep(wait_seconds + random_seconds)
                    self.countdown(total_wait)
                else:
                    print(f"距离下一次打卡开始还有 {minutes} 分钟，等待中...")
                    # time.sleep(wait_seconds + random_seconds)
                    self.countdown(total_wait)
            elif last_checkin_date["morning"] == current_date and last_checkin_date["evening"] != current_date:
                print("当前时间已过上午打卡时间，等待下午打卡时间...")
                next_checkin_time = datetime.datetime.combine(time_now.date(), datetime.datetime.strptime(evening_range[0], "%H:%M").time())
                wait_seconds = (next_checkin_time - time_now).total_seconds() + random_seconds
                total_wait = int(wait_seconds)
                hours = total_wait // 3600
                minutes = (total_wait % 3600) // 60
                if hours > 0:
                    print(f"距离下一次打卡开始还有 {hours} 小时 {minutes} 分钟，等待中...")
                    self.countdown(total_wait)
                else:
                    print(f"距离下一次打卡开始还有 {minutes} 分钟，等待中...")
                    self.countdown(total_wait)
            elif last_checkin_date["evening"] == current_date:
                print("今日已完成打卡，等待明天的打卡时间...")
                next_checkin_time = datetime.datetime.combine(time_now.date() + datetime.timedelta(days=1), datetime.datetime.strptime(morning_range[0], "%H:%M").time())
                wait_seconds = (next_checkin_time - time_now).total_seconds() + random_seconds
                total_wait = int(wait_seconds)
                hours = total_wait // 3600
                minutes = (total_wait % 3600) // 60
                if hours > 0:
                    print(f"距离下一次打卡开始还有 {hours} 小时 {minutes} 分钟，等待中...")
                    self.countdown(total_wait)
                else:
                    print(f"距离下一次打卡开始还有 {minutes} 分钟，等待中...")
                    self.countdown(total_wait)
            else:
                print("当前正处于打卡时间区间内，准备打卡...")

            if current_date not in self.relax_day():
            # 定义打卡时间范围
                morning_range = moring_check_in.split('-')
                evening_range = evening_check_in.split('-')
                start_morning = datetime.datetime.strptime(morning_range[0], "%H:%M").time()
                end_morning = datetime.datetime.strptime(morning_range[1], "%H:%M").time()
                start_evening = datetime.datetime.strptime(evening_range[0], "%H:%M").time()
                end_evening = datetime.datetime.strptime(evening_range[1], "%H:%M").time()

                # 只在同一天的同一打卡区间打一次卡
                if start_morning <= current_time <= end_morning:
                    if last_checkin_date["morning"] == current_date:
                        print("今日上午已打卡，无需重复打卡。")
                    else:
                        self.preset.run()
                        self.find_work_icon()
                        print("正在等待页面加载……")
                        time.sleep(7)
                        self.page_checker(self.check_in)
                        last_checkin_date["morning"] = current_date
                        print("当前为上班打卡，日志生成时间：{} | {}".format(current_date, current_time))

                elif start_evening <= current_time <= end_evening:
                    if last_checkin_date["evening"] == current_date:
                        print("今日下午已打卡，无需重复打卡。")
                    else:
                        self.preset.run()
                        self.find_work_icon()
                        print("正在等待页面加载……")
                        time.sleep(7)
                        self.page_checker(self.check_out)
                        last_checkin_date["evening"] = current_date
                        print("当前为下班打卡，日志生成时间：{} | {}".format(current_date, current_time))
                else:
                    print("当前非打卡时段，日志产生时间：{} | {}".format(current_date, current_time))
            else:
                print("当前非上班日，日志产生时间：{} | {}".format(current_date, current_time))

    def page_checker(self, func):
        if not self.login_page():
            if not self.update_page():
                print('已是最新版本')
            if not self.agreement_page():
                print('未检测到协议按钮')
            if not self.bound_page():
                print('已绑定')
            print('已登录')
        if not self.password_expired_page():
            print('密码未过期')
        self.check_in_page()
        time.sleep(5)
        self.get_screenshot()
        func()
        time.sleep(2)
        self.get_screenshot()
        time.sleep(2)
        self.send_email_html()
        self.check_out_page()
        self.sleep()

    def send_email_html(self):
        image_path = self.screenshot
        try:
            # 创建一个多部分的邮件消息
            msg = MIMEMultipart('related')
            msg['From'] = '806816512@qq.com'
            msg['To'] = self.preset.email_address
            msg['Subject'] = "{}签到信息".format(datetime.datetime.now().strftime("%Y年%m月%d日"))
            password = 'piptszncxxrgbaib'

            # 创建邮件正文
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # 创建HTML内容
            html_content = f"""
                <html>
                <body>
                    <p>今日签到结果如下：</p>
                    <img src="cid:image1">
                </body>
                </html>
                """
            msg_alternative.attach(MIMEText(html_content, 'html'))

            # 打开图片文件并读取
            with open(image_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-ID', '<image1>')
                msg.attach(img)

            # 连接到SMTP服务器并发送邮件
            smtp_server = "smtp.qq.com"
            smtp_port = 587
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # 启用TLS加密
            server.login('806816512@qq.com', password)
            server.sendmail('806816512@qq.com', self.preset.email_address, msg.as_string())
            print("邮件发送成功")
        except smtplib.SMTPAuthenticationError:
            print("SMTP身份验证失败：请检查你的邮箱地址和密码。")
        except smtplib.SMTPConnectError:
            print("SMTP连接失败：请检查SMTP服务器地址和端口号。")
        except smtplib.SMTPRecipientsRefused:
            print("收件人地址被拒绝：请检查收件人邮箱地址。")
        except smtplib.SMTPSenderRefused:
            print("发件人地址被拒绝：请检查发件人邮箱地址。")
        except smtplib.SMTPDataError:
            print("SMTP数据传输错误：请检查邮件内容。")
        except FileNotFoundError:
            print(f"文件未找到：请检查图片路径 {image_path} 是否正确。")
        except Exception as e:
            print(f"邮件发送失败: {e}")


class Presetting:
    CONFIG_PATH = Path.cwd() / "config.ini"
    SECTION = "SETTINGS"
    EXPECTED_CLICKS = 6  # 密码位数 (记录6次点击)

    def __init__(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read(self.CONFIG_PATH, encoding='utf-8')
        self.email_address = ""
        self.init_system()
        

    def check_adb_installed(self):
        try:
            subprocess.run(["adb", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False
        
    def test_adb_connection(self):
        try:
            res = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            lines = [l for l in res.stdout.splitlines() if l.endswith("device")]
            print("ADB连接测试结果：", lines)
            return len(lines) > 0
        except Exception:
            print("ADB连接测试失败，请检查ADB是否正确安装或设备是否连接。")
            return False

    def download_and_install_adb(self):
        def adb_in_path():
            # 检查系统 PATH 中是否已有 adb
            for path in os.environ.get("PATH", "").split(os.pathsep):
                adb_path = Path(path) / "adb.exe"
                if adb_path.exists():
                    print(f"ADB 已存在于: {adb_path}")
                    return True
            return False

        if adb_in_path():
            return True

        # 改用临时目录下载
        download_dir = Path(os.getenv("TEMP", "."))
        zip_name = download_dir / "platform-tools.zip"
        adb_dir = download_dir / "platform-tools"
        adb_exe = adb_dir / "adb.exe"

        # 如果已存在，直接使用
        if adb_exe.exists():
            print(f"使用本地 ADB: {adb_exe}")
            os.environ["PATH"] = f"{adb_dir.absolute()};{os.environ.get('PATH', '')}"
            return True

        # 下载 ADB
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        print(f"正在下载 ADB 到: {zip_name}...")

        try:
            # 更健壮的下载逻辑
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()

            with open(zip_name, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:  # 过滤 keep-alive 空 chunk
                        f.write(chunk)

            # 验证下载结果
            if not zip_name.exists():
                raise FileNotFoundError("下载的文件未保存！")

            # 解压
            print(f"正在解压到: {adb_dir}...")
            with zipfile.ZipFile(zip_name, 'r') as z:
                z.extractall(download_dir)

            # 验证解压结果
            if not adb_exe.exists():
                raise FileNotFoundError("解压后未找到 adb.exe！")

            # 更新 PATH
            os.environ["PATH"] = f"{adb_dir.absolute()};{os.environ.get('PATH', '')}"
            print(f"ADB 已安装到: {adb_exe}")
            return True

        except Exception as e:
            print(f"ADB 安装失败: {e}")
            return False


    def init_config(self):
        if not self.CONFIG_PATH.exists():
            self.cfg[self.SECTION] = {
                "开发者模式": "False",
                "密码设置": "Null",
                "密码": "",
                "激活码": "",
                "邮箱地址": "",
                "上午打卡区间": "08:00-08:58",
                "下午打卡区间": "17:30-18:10",
            }
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                self.cfg.write(f)

    def check_developer_mode(self):
        if self.cfg[self.SECTION].get("开发者模式", "False") != "True":
            print("""
一、请按步骤开启开发者选项：
1. 设置 > 关于手机 > 连续点击版本号7次
2. 返回 系统和更新 > 开发人员选项 > 开启 USB 调试
3. 连接电脑，授权“始终允许”
二、请按步骤调整目标icon：
1.保持手机处于主界面
2.确认icon在手机主界面上
3.确认后将手机调整为息屏状态
如已完成请输入 Y: """)
            while input().strip().lower() != 'y':
                print("请输入Y以确认已完成以上步骤：")
            self.cfg[self.SECTION]["开发者模式"] = "True"
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                self.cfg.write(f)


    def handle_password_and_unlock(self):
        state = self.cfg[self.SECTION].get("密码设置", "Null")
        if state == "Null":
            print("手机是否有锁屏密码？(Y/N)")
            choice = input().strip().lower()
            if choice == 'n':
                self.cfg[self.SECTION]["密码设置"] = "False"
                with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                    self.cfg.write(f)
                subprocess.run(["adb", "shell", "input", "swipe", "500", "2000", "500", "800"], check=True)
                return
            else:
                self.setup_password_sequence()
        elif state == "False":
            print("当前为无密码锁屏，正在解锁...")
            subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=True)
            time.sleep(0.5)
            subprocess.run(["adb", "shell", "input", "swipe", "500", "2000", "500", "800"], check=True)
            time.sleep(0.5)
            return
        else:
            self.input_password()

    def setup_password_sequence(self):
        print("开始密码坐标记录，按提示操作...")
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=True)
        time.sleep(0.5)
        subprocess.run(["adb", "shell", "input", "swipe", "500", "2000", "500", "800"], check=True)
        time.sleep(0.5)

        dev = self.get_touch_device()
        if not dev:
            print("无法检测到触摸设备，请手动输入坐标。")
            return

        print(f"请在手机上依次输入{self.EXPECTED_CLICKS}位密码，系统自动记录坐标...")
        coords = []
        proc = subprocess.Popen(["adb", "shell", "getevent", "-lt", dev], stdout=subprocess.PIPE, text=True)
        try:
            x = y = None
            while len(coords) < self.EXPECTED_CLICKS:
                line = proc.stdout.readline()
                if not line:
                    break
                if 'ABS_MT_POSITION_X' in line:
                    x = int(line.strip().split()[-1], 16)
                elif 'ABS_MT_POSITION_Y' in line and x is not None:
                    y = int(line.strip().split()[-1], 16)
                    coords.append(f"{x},{y}")
                    print(f"记录：{coords[-1]}")
        finally:
            proc.terminate()
            subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_POWER"], stdout=subprocess.DEVNULL)

        if len(coords) != self.EXPECTED_CLICKS:
            print("坐标记录失败，重新开始...")
            return self.setup_password_sequence()

        self.cfg[self.SECTION]["密码"] = ",".join(coords)
        self.cfg[self.SECTION]["密码设置"] = "True"
        with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
            self.cfg.write(f)
        print("密码记录完成！")

        print("模拟首次解锁，请确认是否成功...")
        self.simulate_unlock()
        ans = input("是否唤醒成功？(Y/N): ").strip().lower()
        if ans != 'y':
            print("重新设置密码...")
            self.setup_password_sequence()

    def get_touch_device(self):
        try:
            out = subprocess.run(["adb", "shell", "getevent -pl"], shell=True, stdout=subprocess.PIPE, text=True)
            device = None
            for line in out.stdout.splitlines():
                if line.startswith("add device"):
                    device = line.split()[-1]
                elif device and "ABS_MT_POSITION_X" in line:
                    return device
        except:
            return None
        return None

    def simulate_unlock(self):
        coords = self.cfg[self.SECTION].get("密码", "").split(',')
        seq = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
        subprocess.run(["adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=True)
        time.sleep(0.5)
        subprocess.run(["adb", "shell", "input", "swipe", "500", "2100", "500", "600"], check=True)
        time.sleep(0.5)
        for x, y in seq:
            subprocess.run(["adb", "shell", "input", "tap", x, y], check=True)
            time.sleep(0.3)
        time.sleep(1)
    
    # 检查邮箱设置
    def check_email_setting(self):
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        email = self.cfg[self.SECTION].get("邮箱", "").strip()
        while not re.match(email_pattern, email):
            email = input("请设置接收签到结果的邮箱地址：").strip()
            if re.match(email_pattern, email):
                self.cfg[self.SECTION]["邮箱"] = email
                with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                    self.cfg.write(f)
            else:
                print("邮箱格式不正确，请重新输入。")
        self.email_address = email

    def input_password(self):
        print("自动解锁启动...")
        self.simulate_unlock()

    def run_main_program(self):
        print("主程序运行中...")

        DB_CONFIG = {
            'host': 'YourHostIP',
            'port': Port,
            'user': 'user_name',
            'password': 'YourPassword',
            'database': 'database_name',
            'charset': 'utf8mb4'
        }
        TABLE_NAME = 'user_activation'

        def get_device_id():
            try:
                result = subprocess.check_output(["adb", "shell", "getprop", "ro.serialno"], text=True).strip()
                if not result or "unknown" in result.lower():
                    result = subprocess.check_output(["adb", "devices"], text=True).splitlines()[1].split()[0]
                return result
            except Exception:
                return "unknown_device"

        def check_activation_code(self):
            code = self.cfg[self.SECTION].get("激活码", "").strip()
            while not code:
                code = input("请输入激活码：").strip()
                self.cfg[self.SECTION]["激活码"] = code
                with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                    self.cfg.write(f)
            device_id = get_device_id()
            try:
                conn = pymysql.connect(**DB_CONFIG)
                with conn.cursor() as cursor:
                    sql = f"SELECT devices_id FROM {TABLE_NAME} WHERE activation_code=%s"
                    cursor.execute(sql, (code,))
                    row = cursor.fetchone()
                    if not row:
                        print("激活码不存在，请检查后重新输入。")
                        self.cfg[self.SECTION]["激活码"] = ""
                        with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                            self.cfg.write(f)
                        return self.check_activation_code()
                    db_device_id = row[0]
                    if db_device_id is None or db_device_id == "" or db_device_id.lower() == "null":
                        update_sql = f"UPDATE {TABLE_NAME} SET devices_id=%s WHERE activation_code=%s"
                        update_sql2 = f"UPDATE {TABLE_NAME} SET is_activated=%s WHERE activation_code=%s"
                        update_sql3 = f"UPDATE {TABLE_NAME} SET updated_at=%s WHERE activation_code=%s"
                        cursor.execute(update_sql3, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), code))
                        cursor.execute(update_sql2, (1, code))
                        cursor.execute(update_sql, (device_id, code))
                        conn.commit()
                        print("激活码绑定成功。")
                    elif db_device_id == device_id:
                        print("激活码已绑定本设备。")
                    else:
                        print("激活码已被其他设备使用，请联系管理员。")
                        sys.exit(1)
            except Exception as e:
                print(f"激活码校验失败: {e}")
                sys.exit(1)
            finally:
                try:
                    conn.close()
                except:
                    pass

        Presetting.check_activation_code = check_activation_code

        def run_main_program(self):
            self.check_activation_code()
            print("主程序运行中...")

        Presetting.run_main_program = run_main_program

    def init_system(self):
        print("初始化系统设置...")
        self.init_config()
        self.run_main_program()

        # 清理现有的ADB进程
        def clean_adb():
            try:
                subprocess.run(["adb", "kill-server"], check=True)
                print("正在清理ADB进程...")
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL)
                time.sleep(1)
            except Exception:
                print("清理ADB进程失败，可能是ADB未安装或未正确配置。")
                pass
        clean_adb()

        if not self.check_adb_installed():
            self.download_and_install_adb()

        
        self.check_developer_mode()
        self.check_email_setting()
        print("当前ADB信息如下：")
        try:
            adb_version = subprocess.check_output(["adb", "version"], text=True)
            adb_devices = subprocess.check_output(["adb", "devices"], text=True)
            print(adb_version)
            print(adb_devices)
        except Exception as e:
            print(f"获取ADB信息失败: {e}")
        while not self.test_adb_connection():
            print("ADB连接异常，按任意键重试...")
            msvcrt.getch()

    def run(self):
        self.handle_password_and_unlock()


# subprocess.run(["python", "config_gui.py"])
if __name__ == '__main__':
    # 先行运行 config_gui
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

    work = Work()
    work.main()
