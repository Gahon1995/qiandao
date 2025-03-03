#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-08-07 22:00:27
import importlib
import os
import socket
import struct

import croniter
from tornado import gen


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


import umsgpack
import functools


def func_cache(f):
    _cache = {}

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = umsgpack.packb((args, kwargs), use_bin_type=True)
        if key not in _cache:
            _cache[key] = f(*args, **kwargs)
        return _cache[key]

    return wrapper


def method_cache(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_cache'):
            self._cache = dict()
        key = umsgpack.packb((args, kwargs), use_bin_type=True)
        if key not in self._cache:
            self._cache[key] = fn(self, *args, **kwargs)
        return self._cache[key]

    return wrapper


import datetime


def format_date(date, gmt_offset=-8 * 60, relative=True, shorter=False, full_format=False):
    """Formats the given date (which should be GMT).

    By default, we return a relative time (e.g., "2 minutes ago"). You
    can return an absolute date string with ``relative=False``.

    You can force a full format date ("July 10, 1980") with
    ``full_format=True``.

    This method is primarily intended for dates in the past.
    For dates in the future, we fall back to full format.
    """
    if not date:
        return '-'
    if isinstance(date, float) or isinstance(date, int):
        date = datetime.datetime.utcfromtimestamp(date)
    now = datetime.datetime.utcnow()
    local_date = date - datetime.timedelta(minutes=gmt_offset)
    local_now = now - datetime.timedelta(minutes=gmt_offset)
    local_yesterday = local_now - datetime.timedelta(hours=24)
    local_tomorrow = local_now + datetime.timedelta(hours=24)
    if date > now:
        later = "后"
        date, now = now, date
    else:
        later = "前"
    difference = now - date
    seconds = difference.seconds
    days = difference.days

    format = None
    if not full_format:
        if relative and days == 0:
            if seconds < 50:
                return "%(seconds)d 秒" % {"seconds": seconds} + later

            if seconds < 50 * 60:
                minutes = round(seconds / 60.0)
                return "%(minutes)d 分钟" % {"minutes": minutes} + later

            hours = round(seconds / (60.0 * 60))
            return "%(hours)d 小时" % {"hours": hours} + later

        if days == 0:
            format = "%(time)s"
        elif days == 1 and local_date.day == local_yesterday.day and \
                relative and later == '前':
            format = "昨天" if shorter else "昨天 %(time)s"
        elif days == 1 and local_date.day == local_tomorrow.day and \
                relative and later == '后':
            format = "明天" if shorter else "明天 %(time)s"
        # elif days < 5:
        # format = "%(weekday)s" if shorter else "%(weekday)s %(time)s"
        elif days < 334:  # 11mo, since confusing for same month last year
            format = "%(month_name)s-%(day)s" if shorter else \
                "%(month_name)s-%(day)s %(time)s"

    if format is None:
        format = "%(year)s-%(month_name)s-%(day)s" if shorter else \
            "%(year)s-%(month_name)s-%(day)s %(time)s"

    str_time = "%d:%02d:%02d" % (local_date.hour, local_date.minute, local_date.second)

    return format % {
        "month_name": local_date.month,
        "weekday": local_date.weekday(),
        "day": str(local_date.day),
        "year": str(local_date.year),
        "time": str_time
    }


def get_next_cron_time(crontab):
    crontab = crontab.replace("?", "*")
    now = datetime.datetime.now()
    cron = croniter.croniter(crontab, now)
    # return [cron.get_next(datetime.datetime).strftime("%Y-%m-%d %H:%M")][0]
    return cron.get_next(datetime.datetime).timestamp()


def utf8(string):
    if isinstance(string, str):
        return string.encode('utf8')
    return string


import urllib.request, urllib.parse, urllib.error
import config
from tornado import httpclient


def send_mail(to, subject, text=None, html=None, async=False, _from="签到提醒 <noreply@%s>" % config.mail_domain):
    if not config.mailgun_key:
        subtype = 'html' if html else 'plain'
        return _send_mail(to, subject, html or text or '', subtype)

    httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
    if async:
        client = httpclient.AsyncHTTPClient()
    else:
        client = httpclient.HTTPClient()

    body = {
        'from': utf8(_from),
        'to': utf8(to),
        'subject': utf8(subject),
    }

    if text:
        body['text'] = utf8(text)
    elif html:
        body['html'] = utf8(html)
    else:
        raise Exception('nedd text or html')

    req = httpclient.HTTPRequest(
        method="POST",
        url="https://api.mailgun.net/v2/%s/messages" % config.mail_domain,
        auth_username="api",
        auth_password=config.mailgun_key,
        body=urllib.parse.urlencode(body)
    )
    return client.fetch(req)


import smtplib
from email.mime.text import MIMEText
import logging

logger = logging.getLogger('qiandao.util')


def _send_mail(to, subject, text=None, subtype='html'):
    if not config.mail_smtp:
        logger.info('no smtp')
        return
    msg = MIMEText(text, _subtype=subtype, _charset='utf-8')
    msg['Subject'] = subject
    msg['From'] = config.mail_user
    msg['To'] = to
    try:
        logger.info('send mail to {}'.format(to))
        if config.mail_ssl:
            s = smtplib.SMTP_SSL()
        else:
            s = smtplib.SMTP()
        s.connect(config.mail_smtp, config.mail_port)
        s.login(config.mail_user, config.mail_password)
        s.sendmail(config.mail_user, to, msg.as_string())
        s.close()
    except Exception as e:
        logger.error('send mail error {}'.format(str(e)))


import chardet
from requests.utils import get_encoding_from_headers, get_encodings_from_content


def find_encoding(content, headers=None):
    return 'utf-8'
    # # content is unicode
    # if isinstance(content, str):
    #     return 'str'
    #
    # encoding = None
    #
    # # Try charset from content-type
    # if headers:
    #     encoding = get_encoding_from_headers(headers)
    #     if encoding == 'ISO-8859-1':
    #         encoding = None
    #
    # # Try charset from content
    # if not encoding:
    #     encoding = get_encodings_from_content(content)
    #     encoding = encoding and encoding[0] or None
    #
    # # Fallback to auto-detected encoding.
    # if not encoding and chardet is not None:
    #     encoding = chardet.detect(content)['encoding']
    #
    # if encoding and encoding.lower() == 'gb2312':
    #     encoding = 'gb18030'
    #
    # return encoding or 'latin_1'


def decode(content, headers=None):
    encoding = find_encoding(content, headers)

    try:
        return content.decode(encoding, 'replace')
    except Exception:
        return None


def quote_chinese(url, encodeing="utf-8"):
    if isinstance(url, str):
        return quote_chinese(url.encode("utf-8"))
    res = [b if ord(b) < 128 else '%%%02X' % (ord(b)) for b in url]
    return "".join(res)


import hashlib

md5string = lambda x: hashlib.md5(utf8(x)).hexdigest()

import random


def get_random(min_num, max_mun, unit):
    random_num = random.uniform(min_num, max_mun)
    result = "%.{0}f".format(int(unit)) % random_num
    return result


import datetime


def get_date_time(date=True, time=True, time_difference=0):
    time_difference = time_difference + 12
    now_date = datetime.datetime.today() + datetime.timedelta(hours=time_difference)
    if date:
        if time:
            return str(now_date).split('.')[0]
        else:
            return str(now_date.date())
    elif time:
        return str(now_date.time()).split('.')[0]
    else:
        return


import time

jinja_globals = {
    'md5': md5string,
    'quote_chinese': quote_chinese,
    'utf8': utf8,
    'timestamp': time.time,
    'random': get_random,
    'date_time': get_date_time,
}

import hashlib


def md5(_str):
    m = hashlib.md5()
    m.update(_str.encode("utf8"))
    print(m.hexdigest())
    return m.hexdigest()


def save_py_file(name, data, basepath):
    print("save python file:", name)
    if not os.path.exists(basepath):
        os.mkdir(basepath)

    if os.path.isfile(basepath):
        os.remove(basepath)
        os.mkdir(basepath)

    file_path = os.path.join(basepath, f"{name}.py")
    if os.path.exists(file_path):
        print("文件已存在")
        return

    print("创建新文件")
    with open(f"{basepath}/{name}.py", mode='w', encoding='utf-8') as fp:
        fp.write(data)
