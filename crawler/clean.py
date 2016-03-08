#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
from urllib.request import urlopen
from datetime import date, timedelta
from collections import namedtuple
import os
from io import StringIO
import signal

import log


KB_SIZE = 1024
DIR_HTML = '../data/html/'
DIR_TEXT = '../data/text/'
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

htmls = set(map(int, open(HTMLS_INDEX).readlines()))
texts = set(map(int, open(TEXTS_INDEX).readlines()))


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
        self._date_published = str()


    def when_published(self, string_date):
        # сегодня в 12:00
        # вчера в 12:00
        # 1 января в 12:00
        # 1 января 2014 в 12:00
        string_date = string_date.split()
        hours = string_date[-1].split(':')[0]  # 12
        minute = string_date[-1].split(':')[1]  # 00
        if string_date[0] == "сегодня":
            publ_date = self._today.isoformat()
        elif string_date[0] == "вчера":
            publ_date = (self._today - timedelta(1)).isoformat()
        else:
            day = string_date[0]
            mon = MONTHS[string_date[1]]  # января -> 01
            if string_date[2] != 'в':
                year = string_date
            else:
                year = self._today.year
            publ_date = '{}-{}-{}'.format(year, mon, day)
        publ_date = '{}-{}-{}'.format(publ_date, hours, minute)
        return publ_date


    # we wrote in the comment the day when we downloaded page
    # so we can work out what "сегодня" or "вчера" is
    def handle_comment(self, data):
        # <!-- when_downloaded 2016-01-01 -->
        data = data.split()
        if data[0] == "when_published":
            data = list(map(int, data[1].split('-')))
            self._today = date(data[0], data[1], data[2])


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
            self._date_published = self.when_published(data.strip())

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
    path = '{}.html'.format(DIR_HTML + str(post))
    with open(path, encoding='utf-8') as html:
        page = html.read()
    return Parser().parse(page)


def clean_list(ids_list, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt
    for post in ids_list:
        if post not in htmls or (not force and post in texts):
            continue
        data = get_data_from_html(post)
        log.debug('Parse post {}.'.format(post))
        path = '{}.txt'.format(DIR_TEXT + str(post))
        with open(path, 'w') as fout:
            # two break-lines for more readable
            fout.write('{}\n\n{}\n\n{}\n\n{}'.format(data.date, ' '.join(data.keywords),
                                                     data.title, data.article_text))
        log.debug('Store {} to {}... {} KB'.format(post, path, round(os.path.getsize(path) // KB_SIZE)))
        texts.add(post)
    ending()


def ending():
    with open(TEXTS_INDEX, 'w') as fout:
        fout.write('\n'.join(map(str, texts)))


def signal_handler(signal, frame):
    ending()
    exit()
