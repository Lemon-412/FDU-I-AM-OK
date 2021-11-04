import base64
import json
import sys
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def base64_api(uname, pwd, img, typeid):
    base64_data = base64.b64encode(img)
    b64 = base64_data.decode()
    data = {"username": uname, "password": pwd, "typeid": typeid, "image": b64}
    result = json.loads(requests.post("http://api.ttshitu.com/predict", json=data).text)
    return result

def reportError(id):
    data = {"id": id}
    result = json.loads(requests.post("http://api.kuaishibie.cn/reporterror.json", json=data).text)
    if result['success']:
        return "报错成功"
    else:
        return result["message"]

from sys import exit as sys_exit
def getCaptchaData(zlapp):
    url = 'https://zlapp.fudan.edu.cn/backend/default/code'
    headers = {'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'accept-encoding': 'gzip',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'dnt': '1',
    'referer': 'https://zlapp.fudan.edu.cn/site/ncov/fudanDaily',
    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'image',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin',
    "User-Agent": zlapp.UA}
    res = zlapp.session.get(url, headers=headers)
    return res.content

class DailyFDCaptcha:
    zlapp = None
    uname = ''
    pwd = ''
    typeid = 2 # 纯英文
    info = lambda x: x
    id = 0
    def __init__(self,
                 uname, pwd,
                 zlapp,
                 info_callback):
        self.zlapp = zlapp
        self.uname = uname
        self.pwd = pwd
        self.info = info_callback
    def __call__(self):
        img = getCaptchaData(self.zlapp)
        result = base64_api(self.uname,self.pwd,img,self.typeid)
        print(result)
        if result['success']:
            self.id = result["data"]["id"]
            return result["data"]["result"]
        else:
            self.info(result["message"])
    def reportError(self):
        if self.id != 0:
            self.info(reportError(self.id))


class DailyFDCaptcha_Baidu:
    zlapp = None
    API_KEY = None
    SECRET_KEY = None
    info = lambda x: x

    def __init__(self, API_KEY, SECRET_KEY, zlapp, info_callback):
        self.zlapp = zlapp
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
    
    def __call__(self):
        for i in range(3):
            img = getCaptchaData(self.zlapp)
            self.result = self._basicGeneral(img)
            if self.ok():
                break
        if self.result['words_result_num'] != 1:
            return 0
        return self.result['words_result'][0]['words']
    
    def ok(self):
        return self.result['words_result_num'] == 1 and len(self.result['words_result'][0]['words']) == 4
    
    def _get_token(self):
        resp = requests.request('POST', 'https://aip.baidubce.com/oauth/2.0/token',
                        params={'grant_type': 'client_credentials', 'client_id': self.API_KEY, 'client_secret': self.SECRET_KEY})
        resp.raise_for_status()
        resp = resp.json()
        return resp['access_token']
    def _basicGeneral(self, img):
        data = {}
        data['image'] = base64.b64encode(img).decode()
        data['language_type'] = 'ENG'

        resp = requests.post('https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic', data=data, params={'access_token': self._get_token()})
        resp.raise_for_status()
        resp = resp.json()
        if 'error_code' in resp:
            raise RuntimeError(resp['error_msg'])
        if resp['words_result_num'] == 1:
            resp['words_result'][0]['words'] = ''.join(re.findall('[a-zA-Z]',resp['words_result'][0]['words']))
        return resp
    def reportError(self):
        if self.result['words_result_num'] != 1 or len(self.result['words_result'][0]['words']) != 4:
            self.info(reportError(self.ressult))

if __name__ == "__main__":
    def base64_api(uname, pwd, img, typeid):
        return {
            "success": False,
            "code": "-1",
            "message": "用户名或密码错误",
            "data": ""
        }
    
    print(base64_api(0,0,0,0))
    test = DailyFDCaptcha(0,0,0,print)
    test(0)
    def base64_api(uname, pwd, img, typeid):
        return {
            "success": True,
            "code": "0",
            "message": "success",
            "data": {
                "result": "hhum",
                "id": "00504808e68a41ad83ab5c1e6367ae6b"
            }
        }
    print(test(0))
    def reportError(id):
        return id
    test.reportError()
