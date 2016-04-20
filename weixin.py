#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from spider import spider

import os
import requests
import re
import time
import xml.dom.minidom
import json
import sys
import math
import subprocess
import ssl

class weixin():
    def __init__(self):
        MAX_GROUP_NUM = 35  # 每组人数
        INTERFACE_CALLING_INTERVAL = 40  # 接口调用时间间隔, 间隔太短容易出现"操作太频繁", 会被限制操作半小时左右
        MAX_PROGRESS_LEN = 50

        #目测是二维码的
        self.QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')

        #tip是啥不知道
        self.tip = 0
        self.uuid = ''

        self.base_uri = ''
        self.redirect_uri = ''
        self.push_uri = ''

        self.skey = ''
        self.wxsid = ''
        self.wxuin = ''
        self.pass_ticket = ''
        self.deviceId = 'e000000000000000'

        self.BaseRequest = {}

        self.ContactList = []
        self.My = []
        self.SyncKey = []


    def responseState(self, func, BaseResponse):
        ErrMsg = BaseResponse['ErrMsg']
        Ret = BaseResponse['Ret']
        if DEBUG or Ret != 0:
            print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))

        if Ret != 0:
            return False

        return True

    def getUUID(self):
        global uuid

        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()),
        }

        #r这里是读取网页的操作，上边有了url和param 之后将r的文本内容读到data中
        r= myRequests.get(url=url, params=params)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
        # 正则表达是匹配 提取code 和uuid
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)

        #这里设置了code和uuid
        code = pm.group(1)
        self.uuid = pm.group(2)

        if code == '200':
            return True

        return False

    def showQRImage(self):
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(time.time()),
        }

        r = myRequests.get(url=url, params=params)

        self.tip = 1

        f = open(self.QRImagePath, 'wb')
        f.write(r.content)
        f.close()
        time.sleep(1)

        if sys.platform.find('darwin') >= 0:
            subprocess.call(['open', self.QRImagePath])
        elif sys.platform.find('linux') >= 0:
            subprocess.call(['xdg-open', self.QRImagePath])
        else:
            os.startfile(QRImagePath)

        print('请使用微信扫描二维码以登录')

    def waitForLogin(self):
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
            self.tip, self.uuid, int(time.time()))

        r = myRequests.get(url=url)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.code=500;
        regx = r'window.code=(\d+);'
        pm = re.search(regx, data)

        code = pm.group(1)

        if code == '201':  # 已扫描
            print('成功扫描,请在手机上点击确认以登录')
            self.tip = 0
        elif code == '200':  # 已登录
            print('正在登录...')
            regx = r'window.redirect_uri="(\S+?)";'
            pm = re.search(regx, data)
            self.redirect_uri = pm.group(1) + '&fun=new'
            self.base_uri = self.redirect_uri[:self.redirect_uri.rfind('/')]

            # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
            services = [
                ('wx2.qq.com', 'webpush2.weixin.qq.com'),
                ('qq.com', 'webpush.weixin.qq.com'),
                ('web1.wechat.com', 'webpush1.wechat.com'),
                ('web2.wechat.com', 'webpush2.wechat.com'),
                ('wechat.com', 'webpush.wechat.com'),
                ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
            ]
            self.push_uri = self.base_uri
            for (searchUrl, pushUrl) in services:
                if self.base_uri.find(searchUrl) >= 0:
                    self.push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
                    break

            # closeQRImage
            if sys.platform.find('darwin') >= 0:  # for OSX with Preview
                os.system("osascript -e 'quit app \"Preview\"'")
        elif code == '408':  # 超时
            pass
        # elif code == '400' or code == '500':

        return code

    def login(self):

        r = myRequests.get(url=self.redirect_uri)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.wxsid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.wxuin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
        # wxuin, pass_ticket))

        if not all((self.skey, self.wxsid, self.wxuin, self.pass_ticket)):
            return False

        self.BaseRequest = {
            'Uin': int(self.wxuin),
            'Sid': self.wxsid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
        }

        return True

    def webwxinit(self):
        url = (self.base_uri +
            '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                self.pass_ticket, self.skey, int(time.time())) )
        params  = {'BaseRequest': self.BaseRequest }
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = myRequests.post(url=url, data=json.dumps(params),headers=headers)
        r.encoding = 'utf-8'
        data = r.json()

        if DEBUG:
            f = open(os.path.join(os.getcwd(), 'webwxinit.json'), 'wb')
            f.write(r.content)
            f.close()


        # print(data)

        dic = data
        self.ContactList = dic['ContactList']
        self.My = dic['User']
        self.SyncKey = dic['SyncKey']

        state = responseState('webwxinit', dic['BaseResponse'])
        return state

    def webwxgetcontact(self):

        url = (self.base_uri +
            '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
                self.pass_ticket, self.skey, int(time.time())) )
        headers = {'content-type': 'application/json; charset=UTF-8'}


        r = myRequests.post(url=url,headers=headers)
        r.encoding = 'utf-8'
        data = r.json()


        # print(data)

        dic = data
        MemberList = dic['MemberList']

        # 倒序遍历,不然删除的时候出问题..
        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                        "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
        for i in range(len(MemberList) - 1, -1, -1):
            Member = MemberList[i]
            if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                MemberList.remove(Member)
            elif Member['UserName'] in SpecialUsers:  # 特殊账号
                MemberList.remove(Member)
            elif Member['UserName'].find('@@') != -1:  # 群聊
                MemberList.remove(Member)

        return MemberList

    def sendMsg(self, MyUserName, ToUserName, msg, seconds=1):

        global headers
        url = self.base_uri + '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)

        for i in range(self.MemberCount):
            if self.MemberList[i]['NickName'] == MyUserName:
                MyUser = self.MemberList[i]['UserName']
        for i in range(self.MemberCount):
            if self.MemberList[i]['NickName'] == ToUserName:
                ToUser = self.MemberList[i]['UserName']

        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': {'Type': 1, 'Content': msg, 'FromUserName': MyUser, 'ToUserName': ToUser},
        }
        time.sleep(seconds)
        r = myRequests.post(url=url, data=json.dumps(params),headers=headers)

    def start(self):
        if not self.getUUID():
            print('failed to get UUID')
            return False

        print('QR CODE Image Loading...')
        self.showQRImage()

        while self.waitForLogin() != '200':
            pass

        os.remove(self.QRImagePath)

        if not self.login():
            print('failed to login')
            return False

        self.MemberList = self.webwxgetcontact()
        self.MemberCount = len(self.MemberList)

        print('There are %s Friends in this WeChat' % self.MemberCount)




def main():
    global myRequests ,headers
    # ssl._create_default_https_context = ssl._create_unverified_context
    headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'}
    myRequests = requests.Session()
    myRequests.headers.update(headers)

    link = weixin()
    link.start()
    spi = spider()
    while 1:
        price = spi.start()
        print(price)
        # for price in prices:
        #     print (price[1])
        link.sendMsg('mountain blue','Daen' ,str(price))
        time.sleep(10)


if __name__ == '__main__':
    main()
