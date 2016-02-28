#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
from urllib.request import urlopen
import os
from io import StringIO

import log


LINK_PREFIX = 'https://geektimes.ru/post/'
DIR_HTML = '../data/html/'
DIR_TEXT = '../data/text/'
KB_SIZE = 1024


class Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_published_tag = False
        self.in_h1_tag = False
        self.in_span_tag = False
        self.in_text = False
        self.in_polling = False
        self.in_poll_title = False
        self.in_label = False
        self.article_text = StringIO()
        self.keywords = ''
        self.title = ''
        self.published = ''


    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == 'meta':
            if 'name' in attrs and attrs['name'] == 'keywords':
                self.keywords = attrs['content']

        if tag == 'div':
            if 'class' in attrs:
                if attrs['class'] == 'published':
                    self.in_published_tag = True
                if attrs['class'] == 'content html_format':
                    self.in_text = True
                if attrs['class'] == 'clear' and self.in_text:
                    self.in_text = False
                if attrs['class'] == 'polling':
                    self.in_text = False  # cause we always have polling in article end
                    self.in_polling = True
                if attrs['class'] == 'poll_title':
                    self.in_poll_title = True

        # polling points
        if tag == 'label' and self.in_polling:
            self.in_label = True

        # article title
        if tag == 'h1':
            if 'class' in attrs and attrs['class'] == 'title':
                self.in_h1_tag = True
        if tag == 'span' and self.in_h1_tag:
            self.in_span_tag = True


    def handle_endtag(self, tag):
        if tag == 'div':
            if self.in_published_tag:
                self.in_published_tag = False
            if self.in_poll_title:
                self.in_poll_title = False
            elif self.in_polling:
                self.in_polling = False

        if tag == 'label' and self.in_label:  # polling points
            self.in_label = False

        if tag == 'span' and self.in_span_tag:  # article title
            self.in_span_tag = False
            self.in_h1_tag = False

        if tag == 'br' and self.in_text:  # break-lines for more readable
            self.article_text.write('\n')


    def handle_data(self, data):
        if self.in_published_tag:
            self.published = data

        if self.in_span_tag:
            self.title = data

        if self.in_text:
            self.article_text.write(data.strip())

        if self.in_poll_title:
            self.article_text.write('\n' + data)

        if self.in_label:  # polling points
            self.article_text.write('\n' + data)


    def parse(self, page):
        self.feed(page)
        return [self.published, self.keywords, self.title, self.article_text.getvalue()]


def get_info(post):
    html = open('{}{}.html'.format(DIR_HTML, post), encoding='utf-8')
    page = html.read()
    return Parser().parse(page)


def clean_all():
    list_html = [x[:-5] for x in os.listdir(DIR_HTML)]
    if list_html:
        clean_range(min(list_html), max(list_html))


def clean_range(first, last):
    list_html = [int(x[:-5]) for x in os.listdir(DIR_HTML)]
    list_text = set([int(x[:-4]) for x in os.listdir(DIR_TEXT)])
    first, last = int(first), int(last)
    for post in range(first, last + 1):
        if post not in list_html or post in list_text:
            continue
        info = get_info(post)
        log.debug('Parse post {}.'.format(post))
        path = '{}{}.txt'.format(DIR_TEXT, post)
        with open(path, 'w') as fout:
            fout.write('\n\n'.join(info))
        log.debug('Store {} to {}... {} KB'.format(post, path, round(os.path.getsize(path) // KB_SIZE)))
