# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Job(scrapy.Item):
    岗位ID=scrapy.Field()   #岗位ID
    岗位编号=scrapy.Field()  #岗位编号 
    岗位名称=scrapy.Field() #岗位名称
    计划招募人数=scrapy.Field()#计划招募人数
    已招募人数=scrapy.Field()    #已招募人数
    岗位描述=scrapy.Field()  #岗位描述   
    岗位条件=scrapy.Field()    #岗位条件

class Outline(scrapy.Item):
    项目地点=scrapy.Field()
    服务类别=scrapy.Field()
    受众人数=scrapy.Field()
    服务对象=scrapy.Field()
    招募日期=scrapy.Field()
    项目日期=scrapy.Field()
    发布日期=scrapy.Field()
    服务时间=scrapy.Field()
    志愿者保障=scrapy.Field()


class ProjectInitiator(scrapy.Item):    #项目发起人
    cover=scrapy.Field()
    name=scrapy.Field()
    address=scrapy.Field()

class Contact(scrapy.Item): #联系方式
    项目联系人=scrapy.Field()
    联系方式=scrapy.Field()
   


class Project(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    ID=scrapy.Field()   #项目ID
    cover=scrapy.Field()   #封面
    name=scrapy.Field() #项目名称
    outline=scrapy.Field()  #项目概要
    jobs=scrapy.Field() #岗位描述
    detail=scrapy.Field()   #项目详情
    initiator=scrapy.Field()
    contact=scrapy.Field()  #联系方式
    项目地址=scrapy.Field()
    项目二维码=scrapy.Field()

