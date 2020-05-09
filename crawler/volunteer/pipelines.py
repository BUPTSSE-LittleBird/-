# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
from scrapy.conf import settings
# 以下两种写法保存json格式，需要在settings里面设置'coolscrapy.pipelines.JsonPipeline': 200
import codecs
import os
import json
from volunteer.items import *
from collections import Counter
import traceback
from twisted.enterprise import adbapi


# class JsonPipeline(object):
#     def __init__(self):
#         self.file = codecs.open('Json_data.json', 'w', encoding='utf-8')

#     def process_item(self, item, spider):
#         info = {}
#         info['outline'] = dict(item['outline'])
#         info['jobs'] = Counter(item['jobs'])
#         info['detail'] = item['detail']
#         info['contact'] = dict(item['contact'])
#         info['cover'] = item['cover']
#         info['ID'] = item['ID']
#         info['name'] = item['name']
#         line = json.dumps(info, ensure_ascii=False) + "\n"
#         print("保存成功")
#         self.file.write(line)
#         return item

#     def spider_closed(self, spider):
#         self.file.close()


class MySQLPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    # classmethod 修饰符对应的函数不需要实例化，不需要 self 参数，但第一个参数需要是表示自身类的 cls 参数，可以来调用类的属性，类的方法，实例化对象等。
    @classmethod
    def from_settings(cls, settings):  # 函数名固定，会被scrapy调用，直接可用settings的值
        """
        数据库建立连接
        :param settings: 配置参数
        :return: 实例化参数
        """
        adbparams = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            use_unicode=True,
            cursorclass=pymysql.cursors.DictCursor  # 指定cursor类型
        )
        # 连接数据池ConnectionPool，使用pymysql或者Mysqldb连接
        dbpool = adbapi.ConnectionPool('pymysql', **adbparams)
        # 返回实例化参数
        return cls(dbpool)

    def process_item(self, item, spider):
        """
        使用twisted将MySQL插入变成异步执行。通过连接池执行具体的sql操作，返回一个对象
        """
        query = self.dbpool.runInteraction(self.dumpAll, item)  # 指定操作方法和操作数据
        # 添加异常处理
        query.addCallback(self.handle_error)  # 处理异常

        # query = self.dbpool.runInteraction(self.dumpJob, item)  # 指定操作方法和操作数据
        # # 添加异常处理
        # query.addCallback(self.handle_error)  # 处理异常

    def handle_error(self, failure):
        if failure:
            # 打印错误信息
            print(failure)

    def dumpAll(self, cue, item):
        # project_info=[item['ID'], item['cover'], item['name'], item['detail']]
        # jobs_info = item['jobs']
        # job_sql="replace into job(岗位ID,岗位编号,岗位名称,计划招募人数,已招募人数,岗位描述,岗位条件,所属项目ID) values(%d,%s,%s,%d,%d,%s,%s,%d"

        # cue.execute("replace into project(ID,cover,name,detail,jobs) values(%d,%s,%s,%s)",
        #             project_info)
        self.dumpProject(cue, item)
        self.dumpJob(cue, item)
        self.dumpOutline(cue, item)
        self.dumpContact(cue, item)
        self.dumpProjectInitiator(cue, item)

    def dumpProject(self, cue, item):
        try:
            cue.execute("replace into project(ID,cover,name,detail,initiator,contact,项目二维码,项目地址) values(%s,%s,%s,%s,%s,%s,%s,%s);",
                        (item['ID'], item['cover'], item['name'], item['detail'], item['initiator']['name'], item['contact']['联系方式'], item['项目二维码'], item['项目地址']))
            #print('导入project成功')
        except:
            print('导入project失败')
            print(item['ID'])
            print(traceback.format_exc())

    def dumpJob(self, cue, item):
        try:
            jobs_info = item['jobs']
            for job in jobs_info:
                cue.execute("replace into job(岗位ID,岗位编号,岗位名称,计划招募人数,已招募人数,岗位描述,岗位条件,所属项目ID) values(%s,%s,%s,%s,%s,%s,%s,%s);",
                            (job['岗位ID'], job['岗位编号'], job['岗位名称'], job['计划招募人数'], job['已招募人数'], job['岗位描述'], job['岗位条件'], item['ID']))
            #print('导入job成功')
        except:
            print('导入job失败')
            print(item['ID'])
            print(traceback.format_exc())

    def dumpOutline(self, cue, item):
        try:
            outline = item['outline']
            if '受众人数' in outline:
                cue.execute("replace into outline(ID,项目地点,服务类别,受众人数,服务对象,招募开始日期,招募结束日期,项目开始日期,项目结束日期,发布日期,服务时间,志愿者保障) " +
                            "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", (item['ID'], outline['项目地点'], outline['服务类别'], outline['受众人数'], outline['服务对象'],
                                                                             outline['招募日期'][0], outline['招募日期'][1], outline['项目日期'][0], outline['项目日期'][1], outline['发布日期'], outline['服务时间'], outline['志愿者保障']))
            else:
                cue.execute("replace into outline(ID,项目地点,服务类别,服务对象,招募开始日期,招募结束日期,项目开始日期,项目结束日期,发布日期,服务时间,志愿者保障) " +
                            "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", (item['ID'], outline['项目地点'], outline['服务类别'], outline['服务对象'],
                                                                          outline['招募日期'][0], outline['招募日期'][1], outline['项目日期'][0], outline['项目日期'][1], outline['发布日期'], outline['服务时间'], outline['志愿者保障']))
            #print('导入outline成功')
        except:
            print('导入outline失败')
            print(traceback.format_exc())

    def dumpContact(self, cue, item):
        try:
            contact = item['contact']
            cue.execute("replace into contact(项目联系人,联系方式) values(%s,%s);",
                        (contact['项目联系人'], contact['联系方式']))
            #print('导入contact成功')
        except:
            print('导入contact失败')
            print(traceback.format_exc())

    def dumpProjectInitiator(self, cue, item):
        try:
            initiator = item['initiator']
            cue.execute('replace into project_initiator(name,cover,address) values(%s,%s,%s);',
                        (initiator['name'], initiator['cover'], initiator['address']))
            #print('导入项目发起人成功')
        except:
            print('导入项目发起人失败')
            print(traceback.format_exc())
