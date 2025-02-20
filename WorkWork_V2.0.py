import cv2
import datetime
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders


# 本程序用于网格通自动打卡
class Work:
    def __init__(self):
        # 加载要识别的图片
        self.work_icon = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\Icon.png'
        self.ask_for_leave_icon = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\ask_for_leave.png'
        self.totalcontrol_icon = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\TotalControl.png'
        self.born = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\Born.png'
        self.work_entry = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\WorkEntry.png'
        self.check_in_icon = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\check_in.png'
        self.check_out_icon = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\check_out.png'
        self.login_button = r'C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\login.png'
        self.bound_button = r"C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\bound.jpg"
        self.update_button = r"C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\update.png"
        self.agree_button = r"C:\Users\Administrator\PycharmProjects\pythonProject\WorkWorkAttachments\agree.png"
        self.login_keyboard = {
            '1': [230, 1400],
            '2': [530, 1400],
            '3': [800, 1400],
            '4': [230, 1650],
            '5': [530, 1650],
            '6': [800, 1650],
            '7': [230, 1900],
            '8': [530, 1900],
            '9': [800, 1900],
            '0': [530, 2100]
        }
        self.password = input('请输入锁屏密码：')
        self.reason_list = ["事假", "病假", "年休假", "产假", "护理假", "育儿假", "婚假", "工伤假", "补休假", "探亲假",
                            "独生子女护理假", "其他"]

    def adb_command(self, command):
        os.system(f"adb {command}")

    # 输入中文字符
    def input_Chinese_text(self, text):
        self.adb_command(f"shell am broadcast -a ADB_INPUT_TEXT --es msg '{text}'")

    # 点击指定坐标
    def tap_screen(self, x, y):
        self.adb_command(f"shell input tap {x} {y}")

    # 将锁屏密码转换为对应坐标
    def get_password_location(self):
        for key in self.password:
            self.tap_screen(self.login_keyboard[key][0], self.login_keyboard[key][1])

    # 唤醒手机并模拟按键输入密码
    def wake_up(self):
        # 唤醒屏幕
        self.adb_command("shell input keyevent 3")
        # 唤醒解锁界面
        self.adb_command("shell input keyevent 82")
        time.sleep(1)
        print("正在输入密码")
        # 模拟输入密码
        self.get_password_location()
        time.sleep(1)
        # 如果当前页面没有APP图标，多点击几次home键，防止广告弹出
        self.get_screenshot()
        if not self.find_png(self.work_icon):
            check_icon = False
            self.adb_command("shell input keyevent 3")
            self.adb_command("shell input keyevent 3")
            self.adb_command("shell input keyevent 3")
            while not check_icon:
                self.swipe_screen(800, 1000, 200, 1000)
                check_icon = self.find_png(self.work_icon)

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

    # 点击登录界面
    def login_page(self):
        self.get_screenshot()
        print("正在搜索登录按键")
        time.sleep(2)
        self.find_png(self.login_button, precision=0.7)

    # 点击更新
    def update_page(self):
        self.get_screenshot()
        print("正在搜索绑定按键")
        time.sleep(2)
        coords = self.find_image_on_screen(self.update_button, r"C:/Users/Administrator/PycharmProjects/pythonProject/screen.png", precision=0.7)
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

    # 点击出生证明
    def born_png(self):
        self.get_screenshot()
        print("正在搜索出生证明")
        time.sleep(2)
        self.find_png(self.born, precision=0.85)

    # 进入请假页面
    def ask_for_leave_page(self):
        self.get_screenshot()
        time.sleep(2)
        print("正在搜索请假入口")
        self.find_png(self.ask_for_leave_icon)
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
        # print("正在搜索签到APP")
        # self.find_png(self.work_icon)
        time.sleep(5)
        self.get_screenshot()
        time.sleep(2)
        # self.swipe_screen(800, 800, 800, 200)
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
        self.adb_command("pull /sdcard/screen.png C:/Users/Administrator/PycharmProjects/pythonProject")
        time.sleep(1)

    # 查找目标图片
    def find_image_on_screen(self, template_path, screenshot_path="C:/Users/Administrator/PycharmProjects/pythonProject/screen.png", precision=0.8):
        print("正在从当前截图寻找目标…… | 目标名称：{}".format(template_path.split('\\')[-1]))
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
            self.wake_up()
            self.get_screenshot()
            screenshot = cv2.imread(screenshot_path)

        if template is None:
            print(f"Failed to read template {template_path}.")
            return None

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print('max_val:', max_val)
        if max_val > precision:  # 设定一个匹配阈值
            print("找到匹配目标！")
            template_height, template_width = template.shape[:2]
            center_x = max_loc[0] + template_width/2
            center_y = max_loc[1] + template_height/2
            return center_x, center_y
        print("未找到匹配目标！")
        return None

    # 点击指定图片
    def find_png(self, png, screenshot_path="C:/Users/Administrator/PycharmProjects/pythonProject/screen.png", precision=0.8):
        # self.get_screenshot()
        coords = self.find_image_on_screen(png, screenshot_path, precision)
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
        with open(r'C:\Users\Administrator\Desktop\relax.txt', 'r') as file:
            dates = file.readlines()
            dates = [f"{current_year}.{day}" for day in dates]
        # 去掉每行的换行符并转换为datetime.date对象
        dates = [datetime.datetime.strptime(date.strip(), "%Y.%m.%d").date() for date in dates]
        # print(dates)
        return dates

    # 主程序
    def main(self):
        while True:
            now = datetime.datetime.now()
            current_date = now.date()
            current_time = now.time()
            i = 0
            j = 0

            # 如果今天是需要上班的日期
            # print(current_date)
            # print(self.relax_day())
            if current_date not in self.relax_day():
                # 定义打卡时间范围
                start_morning = datetime.time(8, 0)
                end_morning = datetime.time(8, 58)
                start_evening = datetime.time(17, 30)
                end_evening = datetime.time(18, 10)

                # 判断当前时间是否在上班签到时间范围内
                # print(i)
                # print(j)
                if start_morning <= current_time <= end_morning and i == 0:
                    self.wake_up()
                    time.sleep(7)
                    try:
                        self.update_page()
                    except Exception:
                        print('已是最新版本')
                    try:
                        self.agreement_page()
                    except Exception:
                        print('未检测到协议按钮')
                    try:
                        self.bound_page()
                    except Exception:
                        print('已绑定')
                    try:
                        self.login_page()
                    except Exception:
                        print('已登录')
                    self.check_in_page()
                    time.sleep(5)
                    self.get_screenshot()
                    # print('模拟打卡成功！')
                    self.check_in()
                    time.sleep(2)
                    self.get_screenshot()
                    time.sleep(2)
                    self.send_email_html()
                    self.check_out_page()
                    self.sleep()
                    i += 1
                    print("当前为上班打卡，i的值为{}，日志生成时间：{} | {}".format(i, current_date, current_time))

                # 判断当前时间是否在下班签到时间之后

                elif start_evening <= current_time <= end_evening and j <= 0:
                    self.wake_up()
                    time.sleep(7)
                    try:
                        self.update_page()
                    except Exception:
                        print('已是最新版本')
                    try:
                        self.agreement_page()
                    except Exception:
                        print('未检测到协议按钮')
                    try:
                        self.bound_page()
                    except Exception:
                        print('已绑定')
                    try:
                        self.login_page()
                    except Exception:
                        print('已登录')
                    self.check_in_page()
                    time.sleep(5)
                    self.get_screenshot()
                    # print('模拟打卡成功！')
                    self.check_out()
                    time.sleep(2)
                    self.get_screenshot()
                    time.sleep(2)
                    self.send_email_html()
                    self.check_out_page()
                    self.sleep()
                    j += 1
                    print("当前为下班打卡，j的值为{}，日志生成时间：{} | {}".format(j, current_date, current_time))
                else:
                    if i > 0 or j > 0:
                        print("当前已打卡，日志产生时间：{} | {}".format(current_date, current_time))
                    else:
                        print("当前非打卡时段，日志产生时间：{} | {}".format(current_date, current_time))
            else:
                print("当前非上班日，日志产生时间：{} | {}".format(current_date, current_time))

            # 每40分钟检查一次
            time.sleep(2400)

    def send_email_html(self):
        image_path = r"C:\Users\Administrator\PycharmProjects\pythonProject\screen.png"
        try:
            # 创建一个多部分的邮件消息
            msg = MIMEMultipart('related')
            msg['From'] = '806816512@qq.com'
            msg['To'] = '806816512@qq.com'
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
            server.sendmail('806816512@qq.com', '806816512@qq.com', msg.as_string())
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

    def test(self):
        self.wake_up()
        self.adb_command("shell input keyevent 3")
        self.adb_command("shell input keyevent 3")
        self.adb_command("shell input keyevent 3")
        self.get_screenshot()

    def copy_test(self):
        while True:
            now = datetime.datetime.now()
            current_date = now.date()
            current_time = now.time()
            i = 0
            j = 0

            # 如果今天是需要上班的日期
            # print(current_date)
            # print(self.relax_day())
            if current_date not in self.relax_day():
                # 定义时间范围
                start_morning = datetime.time(8, 0)
                end_morning = datetime.time(8, 50)
                start_evening = datetime.time(17, 30)
                end_evening = datetime.time(18, 30)

                # 判断当前时间是否在上班签到时间范围内
                print(i)
                print(j)
                if start_morning <= current_time <= end_morning and i == 0:
                    self.wake_up()
                    self.get_screenshot()
                    while not self.find_png(self.work_icon):
                        self.swipe_screen(800, 1000, 200, 1000)
                    self.check_in_page()
                    self.get_screenshot()
                    # print('模拟上午签到')
                    time.sleep(2)
                    self.get_screenshot()
                    time.sleep(2)
                    # print('模拟发送上午签到邮件')
                    self.check_out_page()
                    self.sleep()
                    i += 1
                    print("当前为上班打卡，i的值为{}，日志生成时间：{} | {}".format(i, current_date, current_time))

                # 判断当前时间是否在下班签到时间之后

                elif start_evening <= current_time <= end_evening and j <= 0:
                    self.wake_up()
                    self.get_screenshot()
                    while not self.find_png(self.work_icon):
                        self.swipe_screen(800, 1000, 200, 1000)
                    self.check_in_page()
                    self.get_screenshot()
                    # print('模拟下午打卡')
                    time.sleep(2)
                    self.get_screenshot()
                    time.sleep(2)
                    # print('模拟发送下午打卡邮件')
                    self.check_out_page()
                    self.sleep()
                    j += 1
                    print("当前为上班打卡，j的值为{}，日志生成时间：{} | {}".format(j, current_date, current_time))
                else:
                    if i > 0 or j > 0:
                        print("当前已打卡，日志产生时间：{} | {}".format(current_date, current_time))
                    else:
                        print("当前非打卡时段，日志产生时间：{} | {}".format(current_date, current_time))
            else:
                print("当前非上班日，日志产生时间：{} | {}".format(current_date, current_time))
            # 每40分钟检查一次
            time.sleep(2400)

    # 请假程序
    def ask_for_leave(self):
        # 常规前置操作
        self.wake_up()
        time.sleep(7)
        try:
            self.update_page()
        except Exception:
            print('已是最新版本')
        try:
            self.agreement_page()
        except Exception:
            print('未检测到协议按钮')
        try:
            self.bound_page()
        except Exception:
            print('已绑定')
        try:
            self.login_page()
        except Exception:
            print('已登录')

        # 开始正题
        self.ask_for_leave_page()
        info_reason = [str(i + 1) + "." + item for i, item in enumerate(self.reason_list)]
        reason_select = input("请选择假期类型：" + "\n".join(info_reason))
        # 点击请假类型
        self.tap_screen(500, 400)
        time.sleep(0.5)
        # 下滑
        # 先回归最上方
        self.swipeonly_screen(250, 1700, 250, 7200)
        # 按照输入的选项选择假期
        self.swipeonly_screen(250, 2200, 250, 2200 - 80 * int(reason_select))
        # 点击确认
        self.tap_screen(1000, 1600)

        # 获取请假开始日期
        leave_start = input("请输入请假起始日期（例如11.11）：")
        leave_start_mon = int(leave_start.split(".")[0])
        leave_start_day = int(leave_start.split(".")[1])
        # 点击开始日期选项
        self.tap_screen(500, 550)
        time.sleep(0.5)
        # 月回归最上方
        self.swipeonly_screen(250, 1700, 250, 7200)
        # 选择月份
        self.swipeonly_screen(250, 2200, 250, 2200 - 80 * (leave_start_mon-1))
        # 日回归最上方
        self.swipeonly_screen(450, 1700, 450, 7200)
        # 选择日期
        self.swipeonly_screen(450, 2200, 450, 2200 - 80 * (leave_start_day - 1))
        # 时回归最上方，并设置为9点
        self.swipeonly_screen(750, 1700, 750, 7200)
        self.swipeonly_screen(750, 2200, 750, 2200 - 720)
        # 分回归最上方
        self.swipeonly_screen(1000, 1700, 1000, 7200)
        # 点击确认
        self.tap_screen(1000, 1600)

        # 获取请假结束日期
        leave_end = input("请输入请假结束日期（例如11.11）：")
        leave_end_mon = int(leave_end.split(".")[0])
        leave_end_day = int(leave_end.split(".")[1])
        # 点击开始日期选项
        self.tap_screen(500, 700)
        time.sleep(0.5)
        # 月回归最上方
        self.swipeonly_screen(250, 1700, 250, 7200)
        # 选择月份
        self.swipeonly_screen(250, 2200, 250, 2200 - 80 * (leave_end_mon - 1))
        # 日回归最上方
        self.swipeonly_screen(450, 1700, 450, 7200)
        # 选择日期
        self.swipeonly_screen(450, 2200, 450, 2200 - 80 * (leave_end_day - 1))
        # 时回归最上方，并设置为17点
        self.swipeonly_screen(750, 1700, 750, 7200)
        self.swipeonly_screen(750, 2200, 750, 2200 - 80*17)
        # 分回归最上方，设置为30分
        self.swipeonly_screen(1000, 1700, 1000, 7200)
        self.swipeonly_screen(1000, 2200, 1000, 2200 - 80*31)
        # 点击确认
        self.tap_screen(1000, 1600)

        # 调整默认输入法为ADBIME
        self.adb_command("shell ime set com.android.adbkeyboard/.AdbIME")

        # 输入目的地
        self.tap_screen(500, 950)
        time.sleep(0.5)
        self.input_Chinese_text("苏州")

        # 输入请假原因
        self.tap_screen(500, 1050)
        reason = input("请输入请假原因：")
        self.input_Chinese_text(reason)
        time.sleep(0.5)

        # 选择图片
        self.tap_screen(500, 1300)
        time.sleep(1)
        self.tap_screen(100, 500)
        time.sleep(1)
        self.tap_screen(100, 500)
        time.sleep(1)
        self.born_png()
        time.sleep(2)

        # 发送截图，确认后再点击提交
        self.get_screenshot()
        time.sleep(2)
        self.send_email_html()
        check_rst = input("已发送当前截图至邮箱，确认后请输入1，返回上一页则输入2：")

        # 提交
        if check_rst == "1":
            self.tap_screen(530, 2100)
        elif check_rst == "2":
            self.tap_screen(100, 100)

    # 查看请假结果
    def check_leave_result(self):
        # 常规前置操作
        self.wake_up()
        time.sleep(7)
        try:
            self.update_page()
        except Exception:
            print('已是最新版本')
        try:
            self.agreement_page()
        except Exception:
            print('未检测到协议按钮')
        try:
            self.bound_page()
        except Exception:
            print('已绑定')
        try:
            self.login_page()
        except Exception:
            print('已登录')

        # 查看请假结果
        time.sleep(5)
        self.tap_screen(800, 1500)
        self.get_screenshot()
        time.sleep(2)
        self.send_email_html()


if __name__ == '__main__':
    test = Work()
    test.main()
    # test.agreement_page()
    # test.test()
    # test.copy_test()