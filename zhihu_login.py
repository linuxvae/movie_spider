# -*- coding: utf-8 -*-
import threading
import sys
import re
import re # 正则表达式库
import collections # 词频统计库
import numpy as np # numpy数据处理库
import jieba # 结巴分词
import wordcloud # 词云展示库
from PIL import Image # 图像处理库
#import matplotlib.pyplot as plt # 图像展示库

__author__ = 'zkqiang'
__zhihu__ = 'https://www.zhihu.com/people/z-kqiang'
__github__ = 'https://github.com/zkqiang/Zhihu-Login'

import base64
import hashlib
import hmac
import json
import re
import time
from http import cookiejar
from urllib.parse import urlencode

import execjs
import requests
from PIL import Image

class ZhihuAccount(object):
    def __init__(self, username: str = None, password: str = None):
        self.username = username
        self.password = password

        self.login_data = {
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'grant_type': 'password',
            'source': 'com.zhihu.web',
            'username': '',
            'password': '',
            'lang': 'en',
            'ref_source': 'homepage',
            'utm_source': ''
        }
        self.session = requests.session()
        self.session.headers = {
            'accept-encoding': 'gzip, deflate, br',
            'Host': 'www.zhihu.com',
            'Referer': 'https://www.zhihu.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        }
        self.session.cookies = cookiejar.LWPCookieJar(filename='./cookies.txt')

    def login(self, captcha_lang: str = 'en', load_cookies: bool = True):
        """
        模拟登录知乎
        :param captcha_lang: 验证码类型 'en' or 'cn'
        :param load_cookies: 是否读取上次保存的 Cookies
        :return: bool
        若在 PyCharm 下使用中文验证出现无法点击的问题，
        需要在 Settings / Tools / Python Scientific / Show Plots in Toolwindow，取消勾选
        """
        if load_cookies and self.load_cookies():
            print('读取 Cookies 文件')
            if self.check_login():
                print('登录成功')
                return True
            print('Cookies 已过期')

        self._check_user_pass()
        self.login_data.update({
            'username': self.username,
            'password': self.password,
            'lang': captcha_lang
        })

        timestamp = int(time.time() * 1000)
        self.login_data.update({
            'captcha': self._get_captcha(self.login_data['lang']),
            'timestamp': timestamp,
            'signature': self._get_signature(timestamp)
        })

        headers = self.session.headers.copy()
        headers.update({
            'content-type': 'application/x-www-form-urlencoded',
            'x-zse-83': '3_1.1',
            'x-xsrftoken': self._get_xsrf()
        })
        self.session.headers = headers
        data = self._encrypt(self.login_data)
        login_api = 'https://www.zhihu.com/api/v3/oauth/sign_in'
        resp = self.session.post(login_api, data=data, headers=headers)
        if 'error' in resp.text:
            print(json.loads(resp.text)['error'])
        if self.check_login():
            print('登录成功')
            return True
        print('登录失败')
        return False

    def load_cookies(self):
        """
        读取 Cookies 文件加载到 Session
        :return: bool
        """
        try:
            self.session.cookies.load(ignore_discard=True)
            return True
        except FileNotFoundError:
            return False

    def check_login(self):
        """
        检查登录状态，访问登录页面出现跳转则是已登录，
        如登录成功保存当前 Cookies
        :return: bool
        """
        login_url = 'https://www.zhihu.com/signup'
        resp = self.session.get(login_url, allow_redirects=False)
        if resp.status_code == 302:
            self.session.cookies.save()
            return True
        return False

    def _get_xsrf(self):
        """
        从登录页面获取 xsrf
        :return: str
        """
        self.session.get('https://www.zhihu.com/', allow_redirects=False)
        for c in self.session.cookies:
            if c.name == '_xsrf':
                return c.value
        raise AssertionError('获取 xsrf 失败')

    def _get_captcha(self, lang: str):
        """
        请求验证码的 API 接口，无论是否需要验证码都需要请求一次
        如果需要验证码会返回图片的 base64 编码
        根据 lang 参数匹配验证码，需要人工输入
        :param lang: 返回验证码的语言(en/cn)
        :return: 验证码的 POST 参数
        """
        if lang == 'cn':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        resp = self.session.get(api)
        show_captcha = re.search(r'true', resp.text)

        if show_captcha:
            put_resp = self.session.put(api)
            json_data = json.loads(put_resp.text)
            img_base64 = json_data['img_base64'].replace(r'\n', '')
            with open('./captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')
            if lang == 'cn':
                import matplotlib.pyplot as plt
                plt.imshow(img)
                print('点击所有倒立的汉字，在命令行中按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({'img_size': [200, 44],
                                   'input_points': [[i[0] / 2, i[1] / 2] for i in points]})
            else:
                img_thread = threading.Thread(target=img.show, daemon=True)
                img_thread.start()
                capt = input('请输入图片里的验证码：')
            # 这里必须先把参数 POST 验证码接口
            self.session.post(api, data={'input_text': capt})
            return capt
        return ''

    def _get_signature(self, timestamp: int or str):
        """
        通过 Hmac 算法计算返回签名
        实际是几个固定字符串加时间戳
        :param timestamp: 时间戳
        :return: 签名
        """
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        ha.update(bytes((grant_type + client_id + source + str(timestamp)), 'utf-8'))
        return ha.hexdigest()

    def _check_user_pass(self):
        """
        检查用户名和密码是否已输入，若无则手动输入
        """
        if not self.username:
            self.username = input('请输入手机号：')
        if self.username.isdigit() and '+86' not in self.username:
            self.username = '+86' + self.username

        if not self.password:
            self.password = input('请输入密码：')

    def getQsAnswer(self, questionId):
        # 每次我们取10条回答
        limit = 10
        # 获取答案时的偏移量
        offset = 0

        # 开始时假设当前有这么多的回答，得到请求后我再解析
        total = 2 * limit;

        # 我们当前已记录的回答数量
        record_num = 0

        # 定义问题的标题，为了避免获取失败，我们在此先赋值
        title = questionId

        # 存储所有的答案信息
        answer_info = []

        print('Fetch info start...')
        while record_num < total:
            # 开始获取数据
            # 我们获取数据的URL格式是什么样呢？
            # https://www.zhihu.com/api/v4/questions/39162814/answers?
            # sort_by=default&include=data[*].is_normal,content&limit=5&offset=0
            url = 'https://www.zhihu.com/api/v4/questions/' \
                    + questionId + '/answers' \
                    '?sort_by=default&include=data[*].is_normal,voteup_count,content' \
                    '&limit=' + str(limit) + '&offset=' + str(offset)
            print(url)
            response = self.session.get(url)
            # 返回的信息为json类型
            response = json.loads(response.content.decode('utf-8'))

            # 其中的paging实体包含了前一页&下一页的URL，可据此进行循环遍历获取回答的内容
            # 我们先来看下总共有多少回答
            total = response['paging']['totals']

            # 本次请求返回的实体信息数组
            datas = response['data']

            # 遍历信息并记录
            if datas is not None:

                if total <= 0:
                    break

                for data in datas:
                    dr = re.compile(r'<[^>]+>', re.S)
                    content = dr.sub('', data['content'])
                    answer = data['author']['name'] + ' ' + str(data['voteup_count']) + ' 人点赞' + '\n'
                    answer = answer + 'Answer:' + content + '\n'
                    answer_info.append('\n')
                    answer_info.append(answer)
                    answer_info.append('\n')
                    answer_info.append('------------------------------')
                    answer_info.append('\n')
                    # 获取问题的title
                    title = data['question']['title']


                # 请求的向后偏移量
                offset += len(datas)
                record_num += len(datas)

                # 如果获取的数组size小于limit,循环结束
                if len(datas) < limit:
                    break;

        print('Fetch info end...')
        answer_info.insert(0, title + '\n')
        self.write2File('zhihu'+ '.txt', answer_info)

    def write2File(self, filePath, answerInfo):
        print('Write info to file:Start...')
        # 将文件内容写到文件中
        with open(filePath, 'a', encoding='utf-8') as f:
            f.writelines('\n\n')
            for text in answerInfo:
                f.writelines(text)
            f.writelines('\n\n')
            print('Write info to file:end...')

    def read_file_and_pickup(self, filePath):
        print('read info to file:Start...')
        object_list = []
        word_counts=[]
        with open(filePath, 'r', encoding='utf-8') as f:
            txt = f.read()
            pattern = '《(.*?)》'
            dwstr = re.findall(pattern, txt, re.S|re.M)
            for word in dwstr:
                object_list.append(word)

            # 词频统计
            word_counts = collections.Counter(object_list) # 对分词做词频统计
            word_counts_top10 = word_counts.most_common(10000) # 获取前10最高频的词
            #print (word_counts_top10) # 输出检查
            print(len(word_counts))
            print(len(word_counts_top10))
            print(type(word_counts))
            print(type(word_counts_top10))
            

            with open('out_movie.txt', 'w', encoding='utf-8') as of:
                of.writelines('\n\n')
                for text in word_counts_top10:
                    if len(text[0])>50:
                        continue
                    of.writelines(text[0])
                    of.writelines('     ')
                    of.writelines(str(text[1]))
                    of.writelines('\n')

            back_coloring = np.array(Image.open('background.jpg'))

            font_path="song.ttf"
            wc = wordcloud.WordCloud(font_path=font_path,  # 设置字体
                    background_color="white",  # 背景颜色
                    max_words=200,  # 词云显示的最大词数
                    mask=back_coloring,  # 设置背景图片
                    #stopwords=stopwords,
                    max_font_size=100,  # 字体最大值
                    random_state=42,
                    width=1000, height=860, margin=2,# 设置图片默认的大小,但是如果使用背景图片的话,那么保存的图片大小将会按照其大小保存,margin为词语边缘距离
                    #               prefer_horizontal=1,
                    )

            wc.generate_from_frequencies(word_counts)
            wc.to_file("w.png")
            print('readinfo to file:end...')

    @staticmethod
    def _encrypt(form_data: dict):
        with open('./encrypt.js') as f:
            js = execjs.compile(f.read())
            return js.call('Q', urlencode(form_data))


if __name__ == '__main__':
    if len(sys.argv)<3:
        print("cmd: python login.py -g questionId")
        print("cmd: python login.py -o zhihu.txt")
        sys.exit()
    account = ZhihuAccount('', '')
    account.login(captcha_lang='en', load_cookies=True)
    if sys.argv[1]=='-g':
        account.getQsAnswer(sys.argv[2])
    if sys.argv[1]=='-o':
        account.read_file_and_pickup(sys.argv[2])
