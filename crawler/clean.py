#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


import argparse
import sys
from html.parser import HTMLParser
from urllib.request import urlopen
from datetime import datetime, date, timedelta
from collections import namedtuple
import os
from io import StringIO

import log
from config import *
from utils import *

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


class ArticleParser(HTMLParser):
    def __init__(self, date):
        HTMLParser.__init__(self)
        self._in_published_tag = False
        self._in_span_tag = False
        self._in_text = False
        self._in_polling = False
        self._in_poll_title = False
        self._in_label = False

        self._date_downloaded = date
        self._article_text = StringIO()
        self._keywords = list()
        self._title = str()
        self._date_published = str()


    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == 'meta':
            if attrs.get('name') == 'keywords':
                self._keywords = attrs['content'].split()

        if tag == 'div':
            div_class = attrs.get('class')
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
            self._date_published = parse_str_date(self._date_downloaded, data.strip())

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
        return ArticleData(
            self._date_published,
            self._keywords,
            self._title,
            self._article_text.getvalue()
        )


def parse_argument():
    clean = argparse.ArgumentParser(
        prog='clean',
        description='''Extract text of articles and meta information.
                       You can clean all pages, some range of them, or some list.'''
    )
    clean.add_argument(
        '--log',
        default='error',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="log level, 'error' is default value"
    )
    clean.add_argument(
        '--force',
        action='store_true',
        dest='clean_force',
        help='clean pages even if they were cleaned earlier'
    )
    clean_subs = clean.add_subparsers(
        dest='clean_mode'
    )
    clean_all = clean_subs.add_parser(
        'all',
        help='parse all htmls',
        description="Process articles, if they have not been cleaned before."
    )
    clean_range = clean_subs.add_parser(
        'range',
        help='clean range of htmls',
        description='''Clean range of htmls, skipping already cleaned htmls.
                       Of course you should set the range by --from and --to.'''
    )
    clean_range.add_argument(
        '--from',
        type=int,
        required=True,
        dest='start_clean',
        help='where range of cleaning starts'
    )
    clean_range.add_argument(
        '--to',
        type=int,
        required=True,
        dest='end_clean',
        help='where range of cleaning ends'
    )
    clean_list = clean_subs.add_parser(
        'list',
        help='clean listed articles with listed ids',
        description='''Clean htmls from some list you give with --file key.'''
    )
    clean_list.add_argument(
        dest='clean_file',
        metavar='file',
        type=str,
        help='cleaning posts from list in this file')


    if 'range' not in sys.argv and 'all' not in sys.argv and 'list' not in sys.argv:
        clean.print_help()
        return

    return clean.parse_args()


def parse_str_date(date, day_to_parse):
    # Possible date formats:
    # сегодня в 12:00
    # вчера в 12:00
    # 1 января в 12:00
    # 1 января 2014 в 12:00
    *date_prefix, time = day_to_parse.split()
    hour, minute = map(int, time.split(':'))
    if date_prefix[0] == "сегодня":
        year, month, day = date.year, date.month, date.day
    elif date_prefix[0] == "вчера":
        d = date - timedelta(1)
        year, month, day = d.year, d.month, d.day
    else:
        day = int(date_prefix[0])
        month = RU_MONTH_TO_NUM[date_prefix[1]]  # января -> 1
        if date_prefix[2] != 'в':
            year = int(date_prefix[2])
        else:
            year = date.year
    result = datetime(year, month, day, hour, minute)
    return result


def parse_html(post, load_date):
    path = '{}.html'.format(HTML_DIR + str(post))
    with open(path, encoding='utf-8') as file:
        page = file.read()
    return ArticleParser(load_date).parse(page)


def clean_list(ids_list, texts, post_to_date, force=False):
    for post in ids_list:
        if post not in post_to_date:
            log.debug("Can't parse post {}. File doesn't exist.".format(post))
            continue
        if not force and post in texts:
            log.debug("Skip post {}. It's already processed.".format(post))
            continue
        data = parse_html(post, post_to_date[post])
        log.debug('Parse post {}.'.format(post))
        path = TEXT_DIR + str(post) + '.txt'
        to_write = [data.date.isoformat(sep=' '), ' '.join(data.keywords),
                    data.title, data.article_text]
        with open(path, 'w') as file:
            file.write('\n\n'.join(to_write))  # two break-lines for more readable
        log.debug('Store {} to {}... {} KB'.format(post, path,
                                                   round(os.path.getsize(path) // KB_SIZE)))
        texts.add(post)


def get_cleaned_posts():
    with open(TEXTS_INDEX) as file:
        return set(map(int, file.readlines()))


def write_cleaned_posts(texts):
    with open(TEXTS_INDEX, 'w') as file:
        file.write('\n'.join(map(str, texts)))


def main():
    texts = get_cleaned_posts()
    post_to_date = load_dates(HTMLS_INDEX)
    if not post_to_date:
        return

    args = parse_argument()
    if not args:
        return

    log.config(log.level(args.log_level))

    try:
        if args.clean_mode == 'list':
            with open(args.clean_file) as file:
                ids = list(map(int, file.readlines()))
        elif args.clean_mode == 'all':
            ids = post_to_date.keys()
            if not args.clean_force:
                ids &= texts
        elif args.clean_mode == 'range':
            ids = (x for x in range(args.start_clean, args.end_clean + 1))

        clean_list(ids, texts, post_to_date, args.clean_force)

    except KeyboardInterrupt:
        log.debug("KeyboardInterrupt.")
    except Exception as exc:
        exception, value, traceback = sys.exc_info()
        log.critical(value)
    finally:
        write_cleaned_posts(texts)

if __name__ == '__main__':
    main()
