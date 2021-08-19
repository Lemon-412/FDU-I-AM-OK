import time
from json import loads as json_loads
from os import environ
from lxml import etree
from requests import session

import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr


class Email:
    def __init__(self, sender, smtp, receiver):
        self.__sender = sender
        self.__smtp = smtp
        self.__receiver = receiver
        self.title = ""
        self.content = ""

    def clear(self):
        self.title = ""
        self.content = ""

    def set_title(self, title):
        self.title = title

    def add_content(self, content):
        self.content += content

    def add_line(self, content):
        self.content += content + '\n'

    def show_mail(self):
        print("=" * 40)
        print(self.title)
        print("-" * 40)
        print(self.content)
        print("=" * 40)

    def post(self, coding_type="plain", clear=True):
        assert coding_type in ["HTML", "plain"]
        msg = MIMEText(self.content, coding_type, 'utf-8')
        msg['From'] = formataddr(['发送人昵称', self.__sender])
        msg['To'] = formataddr(['收件人昵称', self.__receiver])
        msg['Subject'] = self.title
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(self.__sender, self.__smtp)
        server.sendmail(self.__sender, [self.__receiver, ], msg.as_string())
        server.quit()
        if clear:
            self.clear()


class FduLogin:
    """
    建立与复旦服务器的会话，执行登录/登出操作
    _page_init()
    login()
    logout()
    close()
    """
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gcko/20100101 Firefox/76.0"

    def __init__(self, user_info, url_login):
        """
        初始化session，及登录信息
        :user_info: 包含学号密码及收信邮箱
        :login_url: 登录页
        """
        self.session = session()
        self.session.headers['User-Agent'] = self.UA
        self.url_login = url_login

        self.username, self.__password, self.__email, self.__smtp = user_info
        self.postman = Email(self.__email, self.__smtp, self.__email)

    def _page_init(self):
        """
        检查是否能打开登录页面
        :return: 登录页page source
        """
        page_login = self.session.get(self.url_login)
        if page_login.status_code == 200:
            return page_login.text
        else:
            info_str = "Fail to open Login Page, Check your Internet connection!"
            self.postman.add_line(info_str)
            self.close()

    def login(self):
        card_info = "正在为" + self.username + "打卡"
        self.postman.add_line(card_info)
        page_login = self._page_init()

        html = etree.HTML(page_login, etree.HTMLParser())

        data = {
            "username": self.username,
            "password": self.__password,
            "service": "https://zlapp.fudan.edu.cn/site/ncov/fudanDaily"
        }

        # 获取登录页上的令牌
        data.update(
            zip(
                html.xpath("/html/body/form/input/@name"),
                html.xpath("/html/body/form/input/@value")
            )
        )

        headers = {
            "Host": "uis.fudan.edu.cn",
            "Origin": "https://uis.fudan.edu.cn",
            "Referer": self.url_login,
            "User-Agent": self.UA
        }

        post = self.session.post(
            self.url_login,
            data=data,
            headers=headers,
            allow_redirects=False)

        if post.status_code == 302:
            info_str = "登录成功"
            self.postman.add_line(info_str)
        else:
            info_str = "login failed, check your account info "
            self.postman.add_line(info_str)
            self.postman.set_title('[ERROR]')
            self.close()

    def logout(self):
        """
        执行登出
        """
        exit_url = 'https://uis.fudan.edu.cn/authserver/logout?service=/authserver/login'
        expire = self.session.get(exit_url).headers.get('Set-Cookie')

        if '01-Jan-1970' in expire:
            info_str = "登出完毕"
            self.postman.add_line(info_str)
        else:
            info_str = "登出异常"
            self.postman.add_line(info_str)

    def close(self):
        """
        执行登出并关闭会话
        """
        self.logout()
        self.session.close()

    def sendmail(self):
        self.postman.show_mail()
        # for elem in ["填报成功", "已提交"]:
        #     if elem in self.postman.title:
        #         return
        self.postman.post()


class AutoReport(FduLogin):
    last_info = ''

    def get_lastinfo(self):
        """
        获取用户上次填报的信息
        """
        get_info = self.session.get('https://zlapp.fudan.edu.cn/ncov/wap/fudan/get-info')
        self.last_info = get_info.json()["d"]["info"]
        self.last_info_date = self.last_info["date"]
        self.last_info_position = json_loads(self.last_info['geo_api_info'])['addressComponent']

    def report(self):
        """
        自动填写平安复日
        """
        headers = {
            "Host": "zlapp.fudan.edu.cn",
            "Referer": "https://zlapp.fudan.edu.cn/site/ncov/fudanDaily?from=history",
            "DNT": "1",
            "TE": "Trailers",
            "User-Agent": self.UA
        }

        self.postman.add_line("正在提交...")

        province = self.last_info_position.get("province", "")
        #   print(province)上海市
        city = self.last_info_position.get("city", "")
        #  print(city)
        city = city if city else province

        district = self.last_info_position.get("district", "")
        #   print(district)杨浦区
        self.last_info.update(
            {
                "tw": "13",
                "province": province,
                "city": city,
                "district": district,
                "area": " ".join((province, city, district))
            }
        )

        save = self.session.post(
            'https://zlapp.fudan.edu.cn/ncov/wap/fudan/save',
            data=self.last_info,
            headers=headers,
            allow_redirects=False
        )
        save_msg = json_loads(save.text)["m"]
        self.postman.add_line(save_msg)

    def check(self):
        """
        检查今天是否已提交平安复旦
        """
        self.get_lastinfo()
        today = time.strftime("%Y%m%d", time.localtime())
        if self.last_info["date"] == today:
            info_str = "今日已提交"
            self.postman.set_title('[已提交]')
            self.postman.add_line(info_str)
        else:
            info_str = "今日尚未提交"
            self.postman.add_line(info_str)
            self.report()
            self.get_lastinfo()
            self.postman.set_title('[填报成功]')


def get_account():
    if 'PASSWORD' in environ.keys() and environ['PASSWORD']:
        print(environ['USERNAME'])
        print(environ['EMAIL'])
        print(environ['SMTP'])
        username, password, email, smtp = environ['USERNAME'], environ['PASSWORD'], environ['EMAIL'], environ['SMTP']
    else:
        with open("local_pass.txt", "r") as FILE:
            username, password, email, smtp = map(str.strip, FILE.readlines())
    return [username, password, email, smtp]


def main():
    user_info = get_account()
    url_login = 'https://uis.fudan.edu.cn/authserver/login?service=https://zlapp.fudan.edu.cn/site/ncov/fudanDaily'
    daily_fudan = AutoReport(user_info, url_login)
    daily_fudan.login()
    daily_fudan.check()
    daily_fudan.close()
    daily_fudan.sendmail()


if __name__ == '__main__':
    main()
