#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
from urllib.request import urlopen
from datetime import date, timedelta
from collections import namedtuple
import os
from io import StringIO

import log


DIR_HTML = '../data/html/'
DIR_TEXT = '../data/text/'
KB_SIZE = 1024
TEXTS_INDEX = '../data/text/.index'
HTMLS_INDEX = '../data/html/.index'
Result = namedtuple('Result', ['date', 'keywords', 'title', 'article_text'])
MONTHS = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12'
        }


def when_published(string_date, today):
        # сегодня в 12:00
        # вчера в 12:00
        # 1 января в 12:00
        # 1 января 2014 в 12:00
        string_date = string_date.split()
        hours = string_date[-1].split(':')[0]  # 12:09
        minute = string_date[-1].split(':')[1]
        if string_date[0] == "сегодня":
            num_date = today.strftime('%y%m%d')
        elif string_date[0] == "вчера":
            num_date = (today - timedelta(1)).strftime('%y%m%d')
        else:
            day = string_date[0]
            mon = MONTHS[string_date[1]]  # января -> 01
            if string_date[2] != 'в':
                year = string_date[-2:]  # 2014 -> 14
            else:
                year = today.strftime('%y')
            num_date = year + mon + day
        num_date = int(num_date + hours + minute)
        return num_date


class Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._in_published_tag = False
        self._in_h1_tag = False
        self._in_span_tag = False
        self._in_text = False
        self._in_polling = False
        self._in_poll_title = False
        self._in_label = False
        self._today = date.today()

        self._article_text = StringIO()
        self._keywords = list()
        self._title = str()
        self._date_published = int()


    # we write out the day when we downloaded page
    # so we can work out what "сегодня" or "вчера" is
    def handle_comment(self, data):
        data = data.split()
        if data[0] == "when_published":
            data = list(map(int, data[1].split('.')))
            self._today = date(2000 + data[0], data[1], data[2])


    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == 'meta':
            if attrs.get('name') == 'keywords':
                self._keywords = attrs['content'].split()

        if tag == 'div':
            div_class =  attrs.get('class')
            if div_class == 'published':
                self._in_published_tag = True
            if div_class == 'content html_format':
                self._in_text = True
            if div_class == 'clear' and self._in_text:
                self._in_text = False
            if div_class == 'polling':
                self._in_text = False  # cause we always have polling in article end
                self._in_polling = True
            if div_class == 'poll_title':
                self._in_poll_title = True

        # polling points
        if tag == 'label' and self._in_polling:
            self._in_label = True

        # article title
        if tag == 'h1':
            if attrs.get('class') == 'title':
                self._in_h1_tag = True
        if tag == 'span' and self._in_h1_tag:
            self._in_span_tag = True


    def handle_endtag(self, tag):
        if tag == 'div':
            if self._in_published_tag:
                self._in_published_tag = False
            if self._in_poll_title:
                self._in_poll_title = False
            elif self._in_polling:
                self._in_polling = False

        if tag == 'label' and self._in_label:  # polling points
            self._in_label = False

        if tag == 'span' and self._in_span_tag:  # article title
            self._in_span_tag = False
            self._in_h1_tag = False

        if tag == 'br' and self._in_text:  # break-lines for more readable
            self._article_text.write('\n')


    def handle_data(self, data):
        if self._in_published_tag:
            self._date_published = when_published(data.strip(), self._today)

        if self._in_span_tag:
            self._title = data.strip()

        if self._in_text:
            self._article_text.write(data.strip())

        if self._in_poll_title:
            self._article_text.write('\n' + data.strip())

        if self._in_label:  # polling points
            self._article_text.write('\n' + data.strip())


    def parse(self, page):
        self.feed(page)
        return Result(self._date_published, self._keywords,
                      self._title, self._article_text.getvalue())


def get_data_from_html(post):
    path = '{}{}.html'.format(DIR_HTML, post)
    with open(path, encoding='utf-8') as html:
        page = html.read()
    return Parser().parse(page)


def clean_range(first, last):
    # 1234.html -> 1234 and 1234.txt -> 1234
    htmls = set(map(int, open(HTMLS_INDEX).readlines()))
    texts = set(map(int, open(TEXTS_INDEX).readlines()))
    for post in range(first, last + 1):
        if post not in htmls or post in texts:
            continue
        info = get_data_from_html(post)
        log.debug('Parse post {}.'.format(post))
        path = '{}{}.txt'.format(DIR_TEXT, post)
        with open(path, 'w') as fout:
            fout.write('\n\n'.join(map(str, info)))  # two break-lines for more readable
        with open(TEXTS_INDEX, 'a') as fout:
            fout.write('{}\n'.format(post))
        log.debug('Store {} to {}... {} KB'.format(post, path, round(os.path.getsize(path) // KB_SIZE)))
