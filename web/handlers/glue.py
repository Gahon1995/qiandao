#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:


import time
import json
import umsgpack
from tornado import gen
from jinja2 import Environment, meta
from libs import utils

from .base import *


class GlueEditor(BaseHandler):
    def get(self, id=None):
        # return self.render('glue/editor.html', tplid=id)
        # id = self.request.arguments.get("id")
        return self.render('glue/vue/index.html', tplid=id)

    def post(self, id):
        """
            获取id对应的数据
        :param id:
        :return:
        """
        user = self.current_user

        tpl = self.check_permission(
            self.db.tpl.get(id, fields=('id', 'userid', 'sitename', 'siteurl', 'banner', 'note', 'cron', 'interval',
                                        'har', 'variables', 'lock')))

        tpl['har'] = self.db.user.decrypt(tpl['userid'], tpl['har'])
        tpl['variables'] = json.loads(tpl['variables'])

        # self.db.tpl.mod(id, atime=time.time())
        self.finish(dict(
            filename=tpl['sitename'] or '未命名模板',
            har=tpl['har'],
            env=dict((x, tpl['variables'][x]) for x in tpl['variables']),
            setting=dict(
                sitename=tpl['sitename'],
                siteurl=tpl['siteurl'],
                note=tpl['note'],
                banner=tpl['banner'],
                cron=tpl['cron'] or '',
                interval=tpl['interval'] or '',
            ),
            readonly=not tpl['userid'] or not self.permission(tpl, 'w') or tpl['lock'],
        ))


class GlueTest(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.render('glue/editor1.html', tplid=id)

    @gen.coroutine
    def post(self):
        self.evil(+1)

        result = dict(success=False, msg="")

        data = json.loads(self.request.body)
        try:
            yield self.fetcher.do_fetch_python(data['code'], data)
            result['success'] = True
        except Exception as e:
            # logger.exception(e)
            logger.info("测试失败")
            result['msg'] = repr(e)

        self.finish(result)


import requests


# the class to define your task
class Demo(object):

    def __init__(self, variables):
        self.variables = variables

    @classmethod
    def start(cls, variables):
        # the function to init Demo
        demo = Demo(variables)
        demo.run()
        return 'something'

    def run(self):
        # function to run task
        return 'something'


# entry point
def run(variables: dict):
    # use this function to start your task
    res = Demo.start(variables)
    return dict(
        variables=variables,  # set new variables if need to update
        success=True,  # whether the task is success
        msg="msg to show"  # msg to desc your task result
    )


class GlueSave(BaseHandler):

    def get(self, id=None):

        self.finish('''import requests

# the class to define your task
class Demo(object):

    def __init__(self, variables):
        self.variables = variables

    @classmethod
    def start(cls, variables):
        # the function to init Demo
        demo = Demo(variables)
        demo.run()
        return 'something'

    def run(self):
        # function to run task
        return 'something'


# entry point
def run(variables: dict):
    # use this function to start your task
    res = Demo.start(variables)
    return dict(
        variables=variables,  # set new variables if need to update
        success=True,  # whether the task is success
        msg="msg to show"  # msg to desc your task result
    )
'''
                    )

    # @staticmethod
    # def get_variables(tpl):
    #     variables = set()
    #     extracted = set(utils.jinja_globals.keys())
    #     env = Environment()
    #     for entry in tpl:
    #         req = entry['request']
    #         rule = entry['rule']
    #         var = set()
    #
    #         def _get(obj, key):
    #             if not obj.get(key):
    #                 return
    #             try:
    #                 ast = env.parse(obj[key])
    #             except:
    #                 return
    #             var.update(meta.find_undeclared_variables(ast))
    #
    #         _get(req, 'method')
    #         _get(req, 'url')
    #         _get(req, 'data')
    #         for header in req['headers']:
    #             _get(header, 'name')
    #             _get(header, 'value')
    #         for cookie in req['cookies']:
    #             _get(cookie, 'name')
    #             _get(cookie, 'value')
    #
    #         variables.update(var - extracted)
    #         extracted.update(set(x['name'] for x in rule.get('extract_variables', [])))
    #     return variables

    @tornado.web.authenticated
    def post(self, id):
        self.evil(+1)

        userid = self.current_user['id']
        data = json.loads(self.request.body)

        har = self.db.user.encrypt(userid, data['har'])
        tpl = self.db.user.encrypt(userid, data['har'])
        # TODO 修改获取变量设置（每个任务需要的自定义配置）
        # variables = json.dumps(list(self.get_variables(data['har'])))
        variables = json.dumps(data['variables'])

        if id:
            _tmp = self.check_permission(self.db.tpl.get(id, fields=('id', 'userid', 'lock')), 'w')
            if not _tmp['userid']:
                self.set_status(403)
                self.finish('公开模板不允许编辑')
                return
            if _tmp['lock']:
                self.set_status(403)
                self.finish('模板已锁定')
                return

            self.db.tpl.mod(id, har=har, tpl=tpl, variables=variables)
        else:
            id = self.db.tpl.add(userid, har, tpl, variables)
            if not id:
                raise Exception('create tpl error')

        setting = data.get('setting', {})
        self.db.tpl.mod(id,
                        sitename=setting.get('sitename'),
                        siteurl=setting.get('siteurl'),
                        note=setting.get('note'),
                        type=setting.get('type'),
                        cron=setting.get('cron') or None,
                        interval=setting.get('interval') or None,
                        mtime=time.time())
        self.finish({
            'id': id
        })


# def run(variables):
#     print(variables)
#     return "成功执行了该方法"


# {
#     "har": "def run(variables):\n print(variables) \n return \"成功执行了该方法\"\n",
#     "variables": "{\"name\":\"Gahon\"}",
#     "setting": {
#         "sitename": "测试网址",
#         "siteurl": "www.test.com",
#         "note": "",
#         "type": "1",
#         "cron": "0 0 0 01",
#         "interval": "-1"
#     }
# }

handlers = [
    # (r'/tpl/(\d+)/edit', GlueEditor),
    # (r'/tpl/(\d+)/save', GlueSave),

    (r'/glue/edit/?(\d+)?', GlueEditor),
    (r'/glue/save/?(\d+)?', GlueSave),
    (r'/glue/test', GlueTest),

]
