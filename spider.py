# -*- coding: utf-8 -*-
#author:zjfeng
import requests,time,os,re # requests作为我们的html客户端
from pyquery import PyQuery as Pq # pyquery来操作dom
from tools.mysql import Mysql
import jieba #分词并取关键词
import jieba.analyse
# 文章详情页 http://www.vccoo.com/v/bf38cd
class Getshow(object):

    def __init__(self, show_id): # 参数为在vccoo上的id
        self.url = 'http://www.vccoo.com/v/{0}'.format(show_id)
        self._dom = None # 弄个这个来缓存获取到的html内容，一个蜘蛛应该之访问一次

    @property
    def dom(self): # 获取html内容
        if not self._dom:
            document = requests.get(self.url)
            document.encoding = 'utf-8'
            self._dom = Pq(document.text)
        return self._dom
    # 标题
    @property
    def title(self): # 让方法可以通过s.title的方式访问 可以少打对括号
        return self.dom('h1.article-title').text() # 关于选择器可以参考css selector或者jquery selector, 它们在pyquery下几乎都可以使用
    # 内容
    @property
    def content(self):
        d=Pq(self.dom('.article-content').html())
        d('.main-tg-area').remove()
        d('.articleRecommend').remove()
        return self.clearInput(d.html())
        # return self.dom('.article-content').html() # 直接获取html 胆子就是大 以后再来过滤
    # 公众号logo
    @property
    def wxlogo(self):
        return self.dom('.author-name img').attr('src')
    #微信号
    @property
    def wxh(self):
        wxlmurl = self.dom('.author-name a').attr('href')#vccoo公众号栏目页
        document = requests.get(wxlmurl)
        document.encoding = 'utf-8'
        dom = Pq(document.text)
        return dom('.publicAccountID').text()
    # 公众号名称
    @property
    def wxname(self):
        return self.dom('.author-name strong').text()
    # 公众号文章真实网址
    @property
    def wxurl(self):
        return re.findall(r'var s = "(.*?)"',self.dom('body').html())[0].replace("&amp;","&")
        # print(re.findall('<title>(.*?)</title>',"dsflksl<title>sdfsdf中国</title>dsfds")[0])
    # 公众号二维码
    @property
    def wxer(self):
        biz= self.wxurl.split("biz=")[1].split("&mid=")[0]
        return "http://mp.weixin.qq.com/mp/qrcode?scene=10000004&size=100&__biz="+biz
    # 发布时间
    @property
    def addtime(self):
        return self.dom('.author-name').text()[-10:] # 获取tags，这里直接用text方法，再切分就行了。一般只要是文字内容，而且文字内容自己没有空格,逗号等，都可以这样弄，省事。


     # 清洗数据
    def clearInput(self,txt):
        txt=txt.replace('<!--main-tg-area-->','')
        txt=txt.replace('<!-- articleRecommend/ -->','')
        # txt=txt.replace('vccoo.com/refer.php?url=','')
        # 正则替换
        txt=re.sub(r'http:\/\/img\d+\.vccoo\.com\/refer\.php\?url=','',txt)
        return txt

        # 入库
    def save(self,tocatid):
        self.database=Mysql(host="121.199.48.195", user="root", pwd="rajltool123", db="test")
        self.tocatid=tocatid
        sDir = 'd:/test/'
        #图片地址
        img_dir = 'img'
        if os.path.exists(sDir)==False:
            os.mkdir(sDir)
        # sName = sDir+str(int(time.time()))+'.txt'
        print('正在采集--'+self.title+'--文章')
        #公众号入库
        isexist = ""
        self.wxid = 0
        try:
            isexist = database.ExecQuery("select id from v9_weixinhao where weixinID='"+self.wxh+"'")
        except Exception as e:
            print(e)
            pass
        if isexist:
            print("公众号-----> 有重复不提交！")
            self.wxid = isexist[0][0]
        else:#入库并返回id
            self.wxid = self.addwx()

        title = self.title
        if (title.strip()==''or self.wxid==0):
            print("标题或微信ID为空,不采集！")
            return
        isexist1=""
        try:
            isexist1 = self.database.ExecQuery("select * from v9_news where title='"+title+"'")
        except Exception as e:
            print(e)
            pass
        if isexist1:
            print(title+'-----> 有重复不提交！')
        else:#无相关记录时提交数据
            self.addnews()


     # 公众号入库
    def addwx(self):
        title = self.wxname
        catid=10 #保存到的栏目
        typeid=0
        tags=jieba.analyse.extract_tags(self.wxname,3)
        keywords=(",".join(tags))
        description=''
        url=''
        listorder=0
        status=99
        username='admin'
        inputtime=updatetime=int(time.time())
        insertbooksql ="insert into v9_weixinhao (title,catid,typeid,keywords,description,url,listorder,status,username,inputtime,updatetime) VALUES ( '{title}', {catid}, {typeid}, '{keywords}', '{description}', '{url}', {listorder}, {status}, '{username}', '{inputtime}', '{updatetime}')"
        insert1 = insertbooksql.format(title=title, catid=catid, typeid=typeid, keywords=keywords, description=description,url=url,listorder=listorder,status=status,username=username,inputtime=inputtime,updatetime=updatetime)
        print(insert1)
        try:
            self.database.cur.execute(insert1)
            # 附表
            lastid=self.database.cur.lastrowid
            fenleiid=self.tocatid
            weixinID=self.wxh
            gnjs=''
            wxrz=''
            wxlogo=self.wxlogo #还要下载图片
            wxepic=self.wxer
            content=''
            paginationtype = 2
            groupids_view = ""
            maxcharperpage = 0
            template = ""
            insertbooksql ="insert into v9_weixinhao_data (id,fenliid,weixinID,gnjs,wxrz,wxlogo,wxepic,content,paginationtype,groupids_view,maxcharperpage,template) VALUES ({lastid},{fenliid},{weixinID},'{gnjs}','{wxrz}','{wxlogo}','{wxepic}','{content}', {paginationtype},'{groupids_view}',{maxcharperpage},'{template}')"
            insert2 = insertbooksql.format(lastid=lastid, fenliid=fenliid, weixinID=weixinID, gnjs=gnjs, wxrz=wxrz, wxlogo=wxlogo, wxepic=wxepic, content=content, paginationtype=paginationtype,groupids_view=groupids_view,maxcharperpage=maxcharperpage,template=template)
            print(insert2)
            self.database.cur.execute(insert2)
            # database.cur.close()
            self.database.conn.commit()
            return self.database.cur.lastrowid
            print('公众号入库成功！')
        except Exception as e:
            print("公众号数据库保存出错，错误信息：%s" % (e) )
            # database.conn.close()
            self.database.conn.rollback()
            return 0

    # 文章入库
    def addnews(self):
       #批量替换旧内容中的图片的路径
        # img_patt = re.compile('src=".*?/(\w+\.\w+)"')
        # new_m = img_patt.sub(r'src="./%s/\1"'%img_dir,m)
        title = self.title
        content=self.database.conn.escape(self.content) #这里对内容进行转义,提交变量时不用加'，因为后面转义过后会自动加引号
        catid=self.tocatid #保存到的栏目
        wxid=self.wxid
        typeid=0
        tags=jieba.analyse.extract_tags(self.title, 6)
        keywords=(",".join(tags))
        description=Pq(self.content).text()[0:200]
        url=''
        listorder=0
        status=99
        username='admin'
        inputtime=updatetime=int(time.time())
        insertbooksql ="insert into v9_news (title,catid,wxid,typeid,keywords,description,url,listorder,status,username,inputtime,updatetime) VALUES ( '{title}',{catid},{wxid},{typeid}, '{keywords}', '{description}', '{url}',{listorder},{status}, '{username}', '{inputtime}', '{updatetime}')"
        insert1 = insertbooksql.format(title=title, catid=catid,wxid=wxid, typeid=typeid, keywords=keywords, description=description,url=url,listorder=listorder,status=status,username=username,inputtime=inputtime,updatetime=updatetime)
        print(insert1)
        try:#这是用到了事务处理
            self.database.cur.execute(insert1)
            lastid=self.database.cur.lastrowid
            paginationtype = 2
            groupids_view = ""
            maxcharperpage = 0
            template = ""
            insertbooksql ="insert into v9_news_data (id,content,paginationtype,groupids_view,maxcharperpage,template) VALUES ({lastid}, {content}, {paginationtype},'{groupids_view}',{maxcharperpage},'{template}')"
            insert2 = insertbooksql.format(lastid=lastid, content=content, paginationtype=paginationtype,groupids_view=groupids_view,maxcharperpage=maxcharperpage,template=template)
            print(insert2)
            self.database.cur.execute(insert2)
            # database.cur.close()
            self.database.conn.commit()
            print('文章入库成功！')
        except Exception as e:
            print("文章数据库保存出错，错误信息：%s" % (e) )
            # database.conn.close()
            self.database.conn.rollback()

#栏目页 http://www.vccoo.com/category/?id=104&page=2
class Getlist(object):
    #tocatid保存到的栏目id
    #getpages要采集的页数
    #page分页码
    def __init__(self, catid , tocatid , getpages , page=1):
        self.url = "http://www.vccoo.com/category/?id=%d&page=%d" % (catid , page)
        self.catid = catid
        self.getpages=getpages
        self.tocatid=tocatid
        self.page = page
        self._dom = None

    @property
    def dom(self):
        if not self._dom:
            document = requests.get(self.url)
            document.encoding = 'utf-8'
            self._dom = Pq(document.text)
            self._dom.make_links_absolute(base_url="http://www.vccoo.com/") # 相对链接变成绝对链接 爽
        return self._dom


    @property
    def urls(self):
        return [url.attr('href') for url in self.dom('.list-con h3 > a').items()]

    @property
    def has_next_page(self): # 看看还有没有下一页，这个有必要
        return bool(self.dom('.pages ul li .next-page')) # 看看有木有下一页

    def next_page(self): # 把这个蜘蛛杀了， 产生一个新的蜘蛛 抓取下一页。 由于这个本来就是个动词，所以就不加@property了
        if self.has_next_page:
            self.__init__(catid=self.catid ,tocatid=self.tocatid,getpages=self.getpages,page=self.page+1)
        else:
            return None

    def crawl(self): # 采集当前分页
        sf_ids = [url.split('/')[-1] for url in self.urls]
        con=len(sf_ids)
        print('此页共要采集%s篇文章' %con)
        i=1
        for sf_id in sf_ids:
            print('此页第%d篇文章采集中' %i)
            Getshow(sf_id).save(self.tocatid)
            i+=1
            print('休息3s采第%d篇' %i)
            time.sleep(3)

    def crawl_all_pages(self):
        while True:
            print(u'正在抓取栏目页:http://www.vccoo.com/category/?id=%d&page=%d , 分页:%d ,共需抓 %d 页' % (self.catid,self.page, self.page, self.getpages))
            self.crawl()
            if int(self.page) >= int(self.getpages) or not self.has_next_page :
                print('采集任务完成！！！')
                break
            else:
                self.next_page()

# 测试
# s = Getshow('324d22')
# print(s.title)
# print(s.content)
# print(s.wxlogo)
# print(s.wxname)
# print(s.wxid)
# # print(s.addtime)
# print(s.wxurl)
# print(s.wxer)
# s=Getlist(104)
# for url in s.urls:
#     show =Getshow(url.split('/')[-1])
#     print(show.title+':'+url)


s=Getlist(121,3,1,6)
# if not s.has_next_page:
#     print('没有下一页')
# else:
#     print('有下一页')
s.crawl_all_pages()

# 还要解决：
#1、数据库转义提交
#2、解决图片下载
#3、公众号的判断新增
#4、对网站不匹配栏目判断分类，等问题
# 用while True 循环加time. sleep来控制访问频率吧，最好加上headers ，还有睡眠时间最好随机生成，这样被发现是机器人的概率低点。
