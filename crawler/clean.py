#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

'''
texts создавать в main и передавать функциям, где оно нужно
(видимо, уже после того, как я разнесу argparse)
'''

from html.parser import HTMLParser
from urllib.request import urlopen
from datetime import datetime, date, timedelta
from collections import namedtuple
import os
from io import StringIO
import signal

import log
from config import *


ArticleData = namedtuple('ArticleData', ['date', 'keywords', 'title', 'article_text'])
RU_MONTH_TO_NUM = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
        }

texts = set(map(int, open(TEXTS_INDEX).readlines()))


def parse_str_date(today, day_to_parse):
    # Possible date formats:
    # сегодня в 12:00
    # вчера в 12:00
    # 1 января в 12:00
    # 1 января 2014 в 12:00
    *date_prefix, time = day_to_parse.split()
    hour, minute = map(int, time.split(':'))
    if date_prefix[0] == "сегодня":
        year, month, day = today.year, today.month, today.day
    elif date_prefix[0] == "вчера":
        d = today - timedelta(1)
        year, month, day = d.year, d.month. d.day
    else:
        day = int(date_prefix[0])
        month = RU_MONTH_TO_NUM[date_prefix[1]]  # января -> 1
        if date_prefix[2] != 'в':
            year = int(date_prefix[2])
        else:
            year = today.year
    result = datetime(year, month, day, hour, minute)
    return result


class ArticleParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._in_published_tag = False
        self._in_span_tag = False
        self._in_text = False
        self._in_polling = False
        self._in_poll_title = False
        self._in_label = False

        self._today = datetime.now()
        self._article_text = StringIO()
        self._keywords = list()
        self._title = str()
        self._date_published = str()


    # we wrote in the comment the day when we downloaded page
    # so we can work out what "сегодня" or "вчера" is
    def handle_comment(self, data):
        # <!-- when_downloaded 2016-01-01 -->
        data = data.split()
        if data[0] == "when_downloaded":
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
        if tag == 'span' and attrs.get('class') == "post_title":
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

        if tag == 'br' and self._in_text:  # break-lines for more readable
            self._article_text.write('\n')


    def handle_data(self, data):
        if self._in_published_tag:
            self._date_published = parse_str_date(self._today, data.strip())

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
        return ArticleData(self._date_published, self._keywords,
                      self._title, self._article_text.getvalue())


def parse_html(post):
    path = '{}.html'.format(HTML_DIR + str(post))
    with open(path, encoding='utf-8') as html:
        page = html.read()
    return ArticleParser().parse(page)


def clean_list(ids_list, force=False):
    signal.signal(signal.SIGINT, signal_handler)  # catching KeyboardInterrupt

    htmls = set(map(int, open(HTMLS_INDEX).readlines()))
    for post in ids_list:
        if post not in htmls:
            log.debug("Can't parse post {}. File doesn't exist.".format(post))
            continue
        if not force and post in texts:
            log.debug("Skip post {}. It's already processed.".format(post))
            continue
        data = parse_html(post)
        log.debug('Parse post {}.'.format(post))
        path = '{}.txt'.format(TEXT_DIR + str(post))
        with open(path, 'w') as fout:
            # two break-lines for more readable
            fout.write('\n\n'.join((data.date.isoformat(sep=' '), ' '.join(data.keywords),
                                    data.title, data.article_text)))
        log.debug('Store {} to {}... {} KB'.format(post, path, round(os.path.getsize(path) // KB_SIZE)))
        texts.add(post)
    ending()


def ending():
    with open(TEXTS_INDEX, 'w') as fout:
        fout.write('\n'.join(map(str, texts)))


def signal_handler(signal, frame):
    log.debug("KeyboardInterrupt.")
    ending()
    exit()
