__author__ = 'HLN'
# -*- coding:utf-8 -*-

import re
import requests
import time
import os
import html

class VS:
    def __init__(self):

        #你的名字
        self.name = ''
        #代码备份路径 如无需备份不填即可
        self.path = ''

        self.enable = False
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
        self.headers = {
            'User-Agent': self.user_agent,
        }
        self.session = requests.session()
        self.username = ''
        self.password = ''
        self.homeworks = []
        self.questioninfo = {}
        self.n = 0
        self.filepath = ''
        self.backuppath = 'E:\PPT\VS\Code'
        self.copyright = '/***********************************************\nAuthor\tHLN\nStudentid\t2150506055\nUploadtime\t2018-03-06 10.34.14\nStatus\tSuccess\n\nPowered by HLN Copyright (c) 2018 HLN All rights reserved.\n***********************************************/\n'
        self.site = 'http://202.117.35.198'
        self.loginpage = 'http://202.117.35.198/Login/Login'
        self.courseindexpage = 'http://202.117.35.198/Login/Teaching_index'
        self.coursepage = ''
        self.homeworkpage = 'http://202.117.35.198/UserWeekHomework/Index'
        self.posturl = 'http://202.117.35.198/UserWeekHomeworkSumbit/result?QTId='

    def login(self):
        self.username = input("请输入用户名：") or '2150506055'
        self.password = input("请输入密码：") or self.username
        data = {
            'UserName': self.username,
            'Password': self.password,
        }
        wb_data = self.session.post(self.loginpage, data=data)
        if wb_data.url != self.loginpage:
            print("登陆成功！！！")

            if not self.username == '2150506055':
                self.copyright = re.sub('HLN', self.name, self.copyright)
                self.copyright = re.sub('2150506055', self.username, self.copyright)
                self.backuppath = self.path

            pattern = re.compile('figure.*?href="(.*?)".*?href.*?>(.*?)<', re.S)
            items = re.findall(pattern, wb_data.text)

            #应添加无课程报错
            if len(items) == 1:
                self.coursepage = self.site + items[0][0]
            else:
                i = 1
                for item in items:
                    print(str(i) + " : " + str(item))
                switch = input("请选择课程序号：")
                self.coursepage = self.site + items[int(switch)-1][0]
        else:
            print("登陆失败！请重新登陆！")
            self.login()

    def get_homework_list(self):
        self.session.get(self.coursepage, headers=self.headers)
        wb_data = self.session.get(self.homeworkpage, headers=self.headers)
        pattern = re.compile('<p>.*?href="(.*?)">(.*?)<.*?：(.*?)<', re.S)
        items = re.findall(pattern, wb_data.text)
        ticks = time.mktime(time.localtime())
        for item in items:
            if int(time.mktime(time.strptime(item[2], "%Y-%m-%d %H:%M:%S "))) > int(ticks):
                homework = {
                    'id': re.search(r'\d+', item[0]).group(),
                    'link': self.site + item[0],
                    'title': item[1],
                    'deadline': item[2].strip()
                }
                self.homeworks.append(homework)

    def get_homework_info(self):
        wb_data = self.session.get(self.homeworks[self.n]['link'], headers=self.headers)
        pattern = re.compile('active">(.*?)<.*?<p><span(.*?)</p.*?answerText.*?>(.*?)<', re.S)
        items = re.findall(pattern, wb_data.text)
        pattern = re.compile('>(.*?)<', re.S)
        texts = re.findall(pattern, items[0][1])
        info = {
            'title': items[0][0],
            'text': '\n'.join(list(texts)[::3]),
            'answer': html.unescape(items[0][2]),
        }
        self.questioninfo = info

        if re.search(r'Status\tSuccess', info['answer']):
            if len(self.homeworks) == 1:
                print("\n所有作业已完成！！！")
                self.enable = False
                return
            del self.homeworks[self.n]
            if self.n == len(self.homeworks):
                self.n = 0
            self.get_homework_info()
            return
        elif not re.search(r'Status\tFail', info['answer']):
            response = self.submit(self.posturl + str(self.homeworks[self.n]['id']), info['answer']).text
            if re.search('恭喜你，所有用例均通过！', response):
                id_to_resubmit = str(self.homeworks[self.n]['id'])
                code_to_resubmit = ''.join([re.sub('2018-03-06 10.34.14', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.copyright), info['answer']])
                self.submit(self.posturl + id_to_resubmit, code_to_resubmit)
                if self.backuppath:
                    self.backup_code(info['title'], code_to_resubmit)
                if len(self.homeworks) == 1:
                    print("\n所有作业已完成！！！")
                    self.enable = False
                    return
                del self.homeworks[self.n]
                if self.n == len(self.homeworks):
                    self.n = 0
                self.get_homework_info()
            else:
                if self.backuppath:
                    self.backup_code(info['title'], ''.join([re.sub('Success', 'Fail', re.sub('2018-03-06 10.34.14', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.copyright)), info['answer']]))
                print(info['title'])
                print(info['text'])
        else:
            if self.backuppath:
                self.backup_code(info['title'], info['answer'])
            print(info['title'])
            print(info['text'])

    def homework(self):
        self.n = 0
        while self.enable:
            self.get_homework_info()
            in_put = ''
            while self.enable:
                in_put = input("\nA重新提交 Q退出 N下一题 P上一题 或输入文件路径:") or 'A'
                if in_put in ['A', 'a', 'N', 'n', 'P', 'p', 'Q', 'q', 'B', 'b']:
                    if in_put in ['Q', 'q']:
                        self.enable = False
                    elif in_put in ['A', 'a']:
                        if self.filepath:
                            self.upload_code()
                        else:
                            print("\n错误！请先输入文件路径...")
                    elif in_put in ['N', 'n']:
                        if self.n == len(self.homeworks)-1:
                            self.n = 0
                        else:
                            self.n += 1
                        self.get_homework_info()
                    elif in_put in ['P', 'p']:
                        if self.n == 0:
                            self.n = len(self.homeworks) - 1
                        else:
                            self.n -= 1
                        self.get_homework_info()
                    elif in_put in ['B', 'b']:
                        self.backup_all()
                else:
                    if os.path.exists(in_put):
                        self.filepath = in_put
                        self.upload_code()

    def upload_code(self):
        f = open(self.filepath, "r")
        answer = f.read()
        f.close()
        response = self.submit(self.posturl + str(self.homeworks[self.n]['id']), answer).text

        if re.search('恭喜你，所有用例均通过！', response):
            print("\n恭喜你，所有用例均通过！\n\n")
            id_to_resubmit = str(self.homeworks[self.n]['id'])
            code_to_resubmit = ''.join([re.sub('2018-03-06 10.34.14', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.copyright), answer])
            if self.backuppath:
               self.backup_code(self.questioninfo['title'], code_to_resubmit)
            if len(self.homeworks) == 1:
                print("\n所有作业已完成！！！")
                self.enable = False
                self.submit(self.posturl + id_to_resubmit, code_to_resubmit)
                return
            del self.homeworks[self.n]
            if self.n == len(self.homeworks):
                self.n = 0
            self.get_homework_info()
            self.submit(self.posturl + id_to_resubmit, code_to_resubmit)
        else:
            pattern = re.compile('<h4>(.*?)<', re.S)
            items = re.findall(pattern, response)
            print("\n" + '\n'.join(list(items)))
            if self.backuppath:
                self.backup_code(self.questioninfo['title'], ''.join([re.sub('Success', 'Fail', re.sub('2018-03-06 10.34.14', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.copyright)), answer]))

    def submit(self, url, answertext):
        data = {
            'answerText': answertext,
            'endTime': '',
            'startTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        return self.session.post(url, data=data)

    def backup_all(self):
        if self.backuppath:
            print("正在备份代码...")
            self.session.get(self.coursepage, headers=self.headers)
            wb_data = self.session.get(self.homeworkpage, headers=self.headers)
            pattern = re.compile('<p>.*?href="(.*?)".*?<p>', re.S)
            items = re.findall(pattern, wb_data.text)
            for item in items:
                homeworkpage = self.session.get(self.site + item, headers=self.headers)
                pattern = re.compile('active">(.*?)<.*?answerText.*?>(.*?)<', re.S)
                items = re.findall(pattern, homeworkpage.text)
                if items[0][1]:
                    self.backup_code(items[0][0], html.unescape(items[0][1]))

    def backup_code(self, title, code):
        pattern = re.compile('第 (\d*?) 周 / 编程题 - (.*?) ', re.S)
        items = re.findall(pattern, title)
        path = os.path.join(self.backuppath, 'Week' + str(items[0][0].strip()))
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                self.backuppath = input("创建备份文件夹失败！请重新输入备份路径或回车取消备份：")
                self.backup_code(title, code)
                return
        filename = path + '\\' + items[0][1].strip() + '.cpp'
        if re.search('Status\tFail', code):
            try:
                f = open(filename, 'r')
                code_old = f.read()
                f.close()
                if re.search('Status\tSuccess', code_old):
                    return
            except:
                pass
        f = open(filename, 'w')
        f.write(code)
        f.close()

    def start(self):
        print("正在登陆...")
        self.enable = True
        self.login()
        self.get_homework_list()
        self.homework()

VS = VS()
VS.start()
