#encoding:utf-8

import re,os
import base64
from Crypto.Cipher import AES
import requests
from lxml import etree
from m3u8download_hecoter import m3u8download
import logging
from rich.table import Table
from rich.console import Console

# 单个视频解析下载类
class huke88:
    def __init__(self,url,Cookie,sucai = False):
        self.url = url
        self.Cookie = Cookie
        self.headers = {
            'Cookie':self.Cookie,
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67'
        }
        self.title = ''
        self.sucai = sucai

    def judge_type(self,url):
        if 'course' in url:
            return 'course'
        elif 'career' in url:
            return 'career'
        elif 'training' in url:
            return 'training'
        elif 'live' in url:
            return 'live'
        elif 'route' in url:
            return 'route'
        elif 'keyWorld' in url:
            return 'keyWorld'
        else:
            return ''

    def getm3u8(self,app_id, tx_file_id, token):
        key = '0000000000000000'
        overlayKey = key.encode().hex()
        overlayIv = key.encode().hex()
        geturl = f'https://playvideo.qcloud.com/getplayinfo/v4/{app_id}/{tx_file_id}?psign={token}&overlayKey={overlayKey}&overlayIv={overlayIv}'
        response_get = requests.get(geturl).json()
        # 得到3个参数 drmToken title m3u8列表
        drmToken = response_get['media']['streamingInfo']['drmToken']
        title = response_get['media']['basicInfo']['name']
        playlisturl = response_get['media']['streamingInfo']['drmOutput'][0]['url']

        headersurl = '/'.join(playlisturl.split('/')[:-1]) + '/'
        parms = playlisturl.split('/')[-1]
        playlisturl = headersurl + 'voddrm.token.' + drmToken + '.' + parms
        m3u8url = headersurl + requests.get(playlisturl).text.split('\n')[-2]

        # 得到 key
        m3u8text = requests.get(m3u8url).text
        keyurl = re.findall('(?<=METHOD=AES-128,URI=").+?(?=")', m3u8text)[0]
        # print(keyurl)
        encryptkey = requests.get(keyurl).content
        cryptor = AES.new(key=key.encode(), mode=AES.MODE_CBC, iv=key.encode())

        decryptkey = cryptor.decrypt(encryptkey)
        # base64编码的解密key
        decryptkey = base64.b64encode(decryptkey).decode()

        return (title, m3u8url, decryptkey)

    def get_csrf(self):
        url = self.url
        headers = self.headers
        response = requests.get(url=url,headers=headers).text
        csrf = re.findall('<meta name="csrf-token" content="(.+?)">', response)[0]
        return csrf

    def course_parse(self):
        url = 'https://asyn.huke88.com/video/video-play'
        headers = self.headers
        data = {
            'id': re.findall('/(\d+).html', self.url)[0],
            '_csrf-frontend': self.get_csrf()
        }
        response = requests.post(url=url,headers=headers,data=data).json()
        # print(response)
        msg = response['msg']
        if msg != '无权限播放':
            app_id = response['app_id']
            tx_file_id = response['tx_file_id']
            token = response['token']
            self.title = response['catalogHeaderTitle']
            return (app_id,tx_file_id,token)
        else:
            print('无权限播放')
            pass

    def career_parse(self):
        id = re.findall('/(\d+)-(\d+).html', self.url)[0]
        id1 = id[0]
        id2 = id[1]

        data = {
            'id': id2,
            '_csrf-frontend': self.get_csrf(),
            'confirm': '0',
            'exposure': "0",
            'sourceIdentity': '0',
            'studySourceId': '0',
            'async': 'false',
            'career_id': id1

        }
        posturl = 'https://asyn.huke88.com/video/video-play'
        response = requests.post(url=posturl, headers=self.headers, data=data).json()

        msg = response['msg']
        if msg != '无权限播放':
            app_id = response['app_id']
            tx_file_id = response['tx_file_id']
            token = response['token']
            self.title = response['catalogHeaderTitle']
            return (app_id, tx_file_id, token)
        else:
            print('无权限播放')
            pass

    def training_parse(self):
        training_id = re.findall('/(\d+).html', self.url)[0]
        posturl = "https://asyn.huke88.com/video/video-play"
        data = {
            'id': id,
            'training_id': training_id,
            '_csrf-frontend': self.get_csrf()
        }
        response = requests.post(url=posturl, headers=self.headers, data=data).json()

        msg = response['msg']
        if msg != '无权限播放':
            app_id = response['app_id']
            tx_file_id = response['tx_file_id']
            token = response['token']
            self.title = response['catalogHeaderTitle']
            return (app_id, tx_file_id, token)
        else:
            print('无权限播放')
            pass

    def live_parse(self):
        response = requests.get(self.url, headers=self.headers).text
        # 获取基本信息
        course = re.findall("(?<=course: ').+?(?=')", response)[0]

        url = 'https://huke88.com/live/play-back'
        data = {
            'course': course,
            '_csrf-frontend': self.get_csrf(),
            'catalogSmall': self.url.split('/')[-1].split('.')[0]
        }
        response = requests.post(url, headers=self.headers, data=data).json()

        msg = response['msg']
        if msg != '无权限播放':
            app_id = response['app_id']
            tx_file_id = response['tx_file_id']
            token = response['token']
            self.title = response['catalogHeaderTitle']
            return (app_id, tx_file_id, token)
        else:
            print('无权限播放')
            pass

    def material_download(self, sucai_workdir='虎课素材'):

        if os.path.exists(sucai_workdir) == False:
            os.makedirs(sucai_workdir)
        posturl = 'https://asyn.huke88.com/download/video-annex'
        try:
            id = re.findall('/(\d+).html', self.url)[0]
        except:
            id = re.findall('/(\d+)-(\d+).html', self.url)[0][1]
        data = {
            'id': id,
            'type': '2',
            '_csrf-frontend': self.get_csrf()
        }
        response = requests.post(url=posturl, headers=self.headers, data=data)

        download_url = response.json()['download_url']

        sucai_title = download_url.split('&')[0].split('=')[-1].replace(' (课程素材及源文件仅供练习学习使用,不可直接商用)', '')
        sucai_response = requests.get(url=download_url, headers=self.headers, stream=True).content
        if b'404 Not Found' not in sucai_response:
            with open(sucai_workdir + '/' + sucai_title, 'wb') as f:
                f.write(sucai_response)
                print(sucai_title, '素材下载完成')
                f.close()


    def run(self):
        _type = self.judge_type(self.url)
        if _type == 'course':
            (app_id, tx_file_id, token) = self.course_parse()
        elif _type == 'career':
            (app_id, tx_file_id, token) = self.career_parse()
        elif _type == 'training':
            (app_id, tx_file_id, token) = self.training_parse()
        elif _type == 'live':
            (app_id, tx_file_id, token) = self.live_parse()
        else:
            print('Wrong type!')
            return

        (title, m3u8url, decryptkey) = self.getm3u8(app_id=app_id, tx_file_id=tx_file_id, token=token)
        m3u8url = m3u8url.replace('‾','~')

        m3u8download(m3u8url=m3u8url,title=title,key=decryptkey)
        # m3u8download(M3u8url=m3u8url,WorkDir='Downloads',Title=title,Key=decryptkey)
        # 素材下载
        if self.sucai:
            try:
                self.material_download()
            except:
                pass

class GetList(huke88):
    def course_list(self):
        response = requests.get(url=self.url).text
        html = etree.HTML(response)
        srcs = html.xpath("//div[@class='dd-list']//@href")
        if srcs == []:
            hrefs = html.xpath("//div[@class='right-mid ']//@href")
            for href in hrefs:
                if href[0:5] == 'https':
                    srcs.append(href)
        if srcs == []:
            srcs.append(self.url)
        srcs = self.resume(srcs)
        return srcs

    def career_list(self):
        if "-" not in self.url:
            id1 = re.findall('/career/(\d+).html', self.url)[0]
        else:
            id1 = re.findall('career/video/(\d+)', self.url)[0]
        url = f"https://huke88.com/career/{id1}.html"
        response = requests.get(url=url).text
        id2 = re.findall('<a href="https://huke88.com/career/video/(\d+-\d+).html" class="fl chapter-img capter-click"',
                         response)
        links = []
        for id in id2:
            src = f"https://huke88.com/career/video/{id}.html"
            # 爬取单个页面
            response = requests.get(url=src)
            html = etree.HTML(response.text)
            hrefs = html.xpath("//div[@class='course-chapter']//a/@href")
            for href in hrefs:
                href = "https://huke88.com" + href
                links.append(href)
                # getcareer(href,Cookie,name)
                # print(href)
        links = self.resume(links)
        return links

    def training_list(self):
        url = re.findall('https://huke88.com/training/\d+.html', self.url)[0]

        response = requests.get(url=url).text

        datas = re.findall("task_dates.push\('(.+)'\);", response)

        links = []
        for data in datas:
            data_url = url + "?" + "date=" + data
            print(data_url)
            links.append(data_url)
        links = self.resume(links)
        return links

    def live_list(self):
        response = requests.get(url=self.url)
        html = etree.HTML(response.text)
        hrefs = html.xpath("//div[@class='comLeft curriculumIntroduce']//@data-id")
        links = []
        for href in hrefs:
            href = "https://huke88.com/live/{}.html".format(href)
            links.append(href)

        links = self.resume(links)
        return links

    def route_list(self):
        response = requests.get(url=self.url)
        html = etree.HTML(response.text)
        # First_dir = html.xpath("//h2/text()")[0]
        section_lists = html.xpath("//div[@class='item-tit']")[0]
        links = []
        for les_item in section_lists:
            hrefs = les_item.xpath("//div[@class='cont-box']/div[@class='box-main']//a[@target='_blank']/@href")
            for href in hrefs:
                if href[0:7] != "https:/":
                    href = "https://huke88.com" + href
                links.append(href)
        links = self.resume(links)
        return links

    def keyWorld_list(self):
        links = []
        # 拼接出全部网址
        response = requests.get(self.url).text
        maxpage = re.findall('data-page="\d+">(\d+)</a>', response)[-1]
        maxpage = int(maxpage)
        print(f'共{maxpage}页视频，请耐心等待……')
        for i in range(1, maxpage + 1):
            link = self.url + f'&page={i}'
            # 每页链接
            response2 = requests.get(link).text
            html = etree.HTML(response2)
            hrefs = html.xpath("//div[@class='img-name clearfix']//@href")
            for href in hrefs:
                links.append(href)
        links = self.resume(links)
        return links

    def run(self):
        _type = self.judge_type(self.url)
        if _type == 'course':
            List = self.course_list()

        elif _type == 'career':
            List = self.career_list()
        elif _type == 'training':
            List = self.training_list()
        elif _type == 'live':
            List = self.live_list()
        elif _type == 'route':
            List = self.route_list()
        elif _type == 'keyWorld':
            List = self.keyWorld_list()
        else:
            print('Wrong type!')
            return
        return List

    def resume(self,List1):
        table = Table()
        console = Console(color_system='256', style=None)
        List2 = []
        if List1 == []:
            print('列表获取错误')
            return
        i = 0
        table.add_column(f'[red]序号')
        table.add_column(f'[red]名称')
        table.add_column(f'[red]链接')
        for List in List1:
            # print(i, List)
            table.add_row(str(i), '',List)
            i = i + 1
        console.print(table)
        numbers = input('输入下载序列（① 5 ② 4-10 ③ 4 10）:')
        if ' ' in numbers:
            for number in numbers.split(' '):
                number = int(number)
                List2.append(List1[number])
        elif '-' in numbers:
            number = re.findall('\d+', numbers)
            return List1[int(number[0]):int(number[1]) + 1]
        else:
            number = re.findall('\d+', numbers)
            List2.append(List1[int(number[0])])
            return List2
        return List2


if __name__ == '__main__':
    print('虎课视频、素材下载器')
    print('使用方法：\n\t①输入Cookie（找cookie方法自行百度）\n\t②输入视频网址\n\t③选择下载序列\n\t④等待下载完成')
    Cookie = input('输入Cookie(例如：advanced-frontend=25s8gaakan2s2i7hi0dsrrqbe5):') # advanced-frontend=ushdiq51l47ro6obkqq7tml472
    # Cookie = 'advanced-frontend=25s8gaakan2s2i7hi0dsrrqbe5'
    while True:
        url = input('输入视频网址：')
        sucai = True if input('是否下载素材(y/n):') == 'y'else False
        batch = True if input('是否批量下载(y/n):') == 'y' else False
        # huke88(url=url, Cookie=Cookie,sucai=sucai).run()
        try:
            if batch:
                Urls = GetList(url=url, Cookie=Cookie).run()
                for url in Urls:
                    print(url)
                    huke88(url=url, Cookie=Cookie, sucai=sucai).run()
            else:
                huke88(url=url, Cookie=Cookie, sucai=sucai).run()
        except Exception as e:
            logging.exception(e)


