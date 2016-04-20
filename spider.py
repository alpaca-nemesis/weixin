#! /usr/bin/env python
#coding=utf-8
import urllib
import re
# import MySQLdb
# from _mysql import MySQLError, NULL
# from twisted.web.client import getPage

class spider:
    def __init__(self, heroList=["沙王"], itemList=["荒地之冠"]):
        self.pageIndex = 1
        self.heroList = heroList
        self.itemList = itemList
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.headers = { 'User-Agent' : self.user_agent }
        self.enable = 1

    def getPage(self,pageIndex,hero,item):
        url = "http://www.dota2shop.cn/?n="+str(item)+"&h="+str(hero)+"&page=" + str(pageIndex)
        page = urllib.urlopen(url)
        html = page.read()
        return html

    def getPageItems(self,html):
        myItems = re.findall('<div.*?class="price".*?<span>(.*?)</span>.*?class="name">(.*?)</div>',html,re.S)
        if len(myItems):
            return myItems
        else:
            self.enable = 0
            return None

    # def save2MySQL(self,prices,hero):
        # try:
        #     conn=MySQLdb.connect(host='localhost',user='root',passwd='',db='dota2',port=3306)
        #     conn.set_character_set('utf8')
        #     cur=conn.cursor()
        #     sql = "create table if not exists "+hero +"(id int not null auto_increment, name varchar(40), price float, primary key (id))"
        #     cur.execute(sql)
        #     for price in prices:
        #         value = [price[1].decode('utf-8'),price[0]]
        #         sql = "insert into "+ hero +" (name,price) values(%s,%s)"
        #         cur.execute(sql,value)
        #     conn.commit()
        #     cur.close()
        #     conn.close()
        #     print ("hero %s page %s is down"% (hero ,self.pageIndex))
        # except MySQLError as error:
        #     print ("MySQL %s", error)

    def start(self):
        print ("正在读取网站数据，请稍候...")
        prices = []
        for hero in self.heroList:
            for item in self.itemList:
                while self.enable == 1:
                    html = self.getPage(self.pageIndex,hero,item)
                    prices_new = self.getPageItems(html)
                    if prices_new is not None:
                        prices = prices + prices_new
                    if self.enable == 0:
                        break
                    self.pageIndex = self.pageIndex + 1
                self.enable = 1
                self.pageIndex = 1
                print("item" + item + "DOWN!")
            print("hero "+ hero + " DOWN!")
        low = 100
        for price in prices:
            low = min(float(price[0]),low)
        return low

if __name__ == "__main__":
    count = 0
    sp = spider()
    price = sp.start()
    print price
