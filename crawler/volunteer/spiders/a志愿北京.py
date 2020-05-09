# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from ..items import Project, Job, Outline, ProjectInitiator, Contact
from scrapy.loader import ItemLoader
import urllib
import re
import requests


class A志愿北京Spider(scrapy.Spider):
    name = '志愿北京'
    depth = 1
    count = 1
    allowed_domains = ['www.bv2008.cn/app/opp/list.php']

    default_initiator_cover = None  # 默认发起人封面
    default_project_cover = None  # 默认项目图片

    def start_requests(self):
        url = 'https://www.bv2008.cn/app/opp/list.php'
        while self.count <= self.depth:
            crawl_url = url+'?p='+str(self.count)
            yield scrapy.Request(crawl_url, callback=self.parseFirstPage)

    def parseFirstPage(self, response):  # 爬取第一个页面
        # if self.count == 1:
        #     self.depth = int(response.css('div.pagebar a::text')[-1].extract())
        for href in response.css('div.listtxt p.ptitle a::attr(href)').extract():
            try:
                # 获取每个项目的具体链接 https://www.bv2008.cn/app/opp/view.php?id=JRQgdDbKG
                url = 'https://www.bv2008.cn/'+href
                yield scrapy.Request(url, callback=self.parseProjectPage, dont_filter=True)
            except:
                # continue
                pass

    def parseProjectPage(self, response):
        single_project = Project()
        # 提取封面
        img = response.css('div.l.desc_img.listimg_opp img::attr(src)').get()
        if img is None:
            single_project['cover'] = self.default_project_cover
        else:
            single_project['cover'] = self.getImage(img)
        # 提取标题
        title_raw = response.css('#main_body h1.l div.l').get()
        project_ID = re.findall(r'【(.*?)】\xa0', title_raw)[0]  # 转为int
        project_title = re.findall(r'\xa0(.+)\xa0\xa0', title_raw)[0]
        single_project['ID'] = project_ID
        single_project['name'] = project_title
        # 提取项目概要
        tbody = response.css('div.l.desc_txt')
        single_project['outline'] = self.parseIntro(tbody)
        # 提取岗位信息
        jobs = response.css('div.job')
        single_project['jobs'] = self.parseJob(jobs)
        # 提取项目详情
        detail = response.css('#con1 *::text').getall()
        details = ''.join(detail)
        details = re.sub(re.compile(r'^\s+|\s+$'), '', details)
        single_project['detail'] = details
        # 提取联系人
        conr = response.css('div.conr')
        single_project['contact'] = self.parseContact(conr)
        # 提取发起人
        single_project['initiator'] = self.parseInitiator(conr)

        # 提取项目地址
        single_project['项目地址'] = re.findall(
            r'\s*([^\s]+)\s*', ''.join(conr.css('div.boxcon.m10::text').getall()))[0]

        # 提取二维码
        QRurl = 'https://www.bv2008.cn' + \
            conr.css('div.boxcon')[1].css('img::attr(src)')[0].get()

       # yield scrapy.Request(url,callback=self.getImage,dont_filter=True)
        single_project['项目二维码'] = self.getImage(QRurl)
        self.count += 1
        yield single_project

    def parseIntro(self, tbody):
        outline = Outline()
        line_count = 1
        trs = tbody.css('tr')
        if len(trs) == 9:
            outline['项目地点'] = trs[0].css('td *::text').get()
            outline['服务类别'] = ";".join(trs[1].css('a::text').extract())
            outline['服务对象'] = trs[2].css('td *::text').get()
            spans1 = trs[3].css('span::text').getall()
            outline['招募日期'] = [spans1[0], spans1[1]]
            spans2 = trs[4].css('span::text').getall()
            outline['项目日期'] = [spans2[0], spans2[1]]
            outline['发布日期'] = trs[5].css('td *::text').get()
            outline['服务时间'] = trs[6].css('td *::text').get()
            outline['志愿者保障'] = trs[7].css('td *::text').get()
        elif len(trs) == 10:
            outline['项目地点'] = trs[0].css('td *::text').get()
            outline['服务类别'] = trs[1].css('a::text').extract()
            outline['服务对象'] = trs[2].css('td *::text').get()
            outline['受众人数'] = int(trs[3].css('td::text').get())
            spans1 = trs[4].css('span::text').getall()
            outline['招募日期'] = [spans1[0], spans1[1]]
            spans2 = trs[5].css('span::text').getall()
            outline['项目日期'] = [spans2[0], spans2[1]]
            outline['发布日期'] = trs[6].css('td *::text').get()
            outline['服务时间'] = trs[7].css('td *::text').get()
            outline['志愿者保障'] = trs[8].css('td *::text').get()

        return outline
        # for tr in tbody.css('tr'):
        #     key=tr.css('th::text')[0].extract()

        #     if key=='受众人数：' or key=='受众人次：':
        #         line_count-=1
        #         val=tr.css('td::text')[0].extract()
        #     elif line_count==2:
        #         val=tr.css('a::text').extract()
        #     elif line_count==4 or line_count==5:
        #         spans=tr.css('span::text').extract()
        #         val=(spans[0],spans[1])
        #     elif line_count==9:
        #         continue
        #     else:
        #         val=tr.css('td *::text')[0].extract()

        # single_project[key]=val
        # line_count+=1

    def parseJob(self, jobs):
        jobs_info = []  # 总的岗位信息
        # 提取表头信息： 岗位、计划招募、已招募
        for job in jobs:
            job_info = Job()
            # 提取表头信息： 岗位名字、计划招募、已招募
            info1 = job.css('span.l::text').get()
            p = re.compile(r'^\s+|\s*\xa0\xa0|\s+$')  # 所要去除的信息
            left = re.sub(p, '', info1)
            job_num = re.search(r'^岗位\d', left).group(0)  # 岗位x

            job_content = re.findall(r'岗位\d*：(.*)计划招募', left)[0]  # 岗位内容

            job_info['岗位编号'] = job_num
            job_info['岗位名称'] = job_content
            to_recruit = int(re.findall(r'计划招募：(.*)已招募', left)[0])  # 计划招募
            job_info['计划招募人数'] = to_recruit
            recruited = int(re.findall(r'已招募：(.*)', left)[0])
            job_info['已招募人数'] = recruited
            # 提取详细信息
            info2 = job.css('div.con p')
            job_info['岗位ID'] = info2[0].css('::text')[1].get()
            job_info['岗位描述'] = re.sub(re.compile(r'</?\w+[^>]*>'), '', ''.join(
                info2[1].css('::text')[1:].getall()))  # 利用正则表达式将合并后的信息中的标签去除
            job_info['岗位条件'] = re.sub(re.compile(
                r'</?\w+[^>]*>'), '', ''.join(info2[2].css('::text')[1:].getall()))

            jobs_info.append(job_info)

        return jobs_info

    def parseInitiator(self, conr):
        # 提取项目发起人
        initiator = ProjectInitiator()
        initiator_info = conr.css('div.boxcon')[0].css('tr')
        imag = initiator_info.css('img::attr(src)').get()
        if imag is None:
            initiator['cover'] = self.default_initiator_cover
        else:
            initiator['cover'] = self.getImage(imag)
        initiator['name'] = initiator_info.css('a::text').get()
        initiator['address'] = re.findall(
            r'地址：([^\s]*)\s*', ''.join(initiator_info.css('::text').getall()))[0]
        return initiator

    def parseContact(self, conr):
        contact = Contact()

        # 提取项目联系人
        contactPerson_info = conr.css('div.boxcon')[2].css('tr')
        contact['项目联系人'] = contactPerson_info.css('span::text').get()
        contact['联系方式'] = re.findall(
            r'\s*([^\s]+)\s*', ''.join(contactPerson_info.css('td.org_desc::text').getall()))[0]
        return contact

    def getImage(self, url):
        try:
            if url[0:4] != 'http':
                url = 'https:'+url
            picture = requests.get(url)
            return picture.content
        except:
            print('爬取图片失败。传入的url:'+url)
