#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


from html.parser import HTMLParser
import os
import urllib.request


import log


DIR_HTML = '../data/html/'
LINK_PREFIX = "http://geektimes.ru/post/"
KB_SIZE = 1024


class Parser_page_all(HTMLParser):  # posts from all-page
    def __init__(self):
        HTMLParser.__init__(self)
        self.posts = list()


    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            attrs = dict(attrs)
            if 'class' in attrs :
                if 'post ' in attrs['class'] and 'shortcuts_item' in attrs['class']:
                # 'post shortcuts_item', 'post translation shortcuts_item', may be smth else
                # and it can't be 'posts shortcuts_item'
                    self.posts.append(int(attrs['id'][5:]))  # post_271508 -> 271508


    def parse(self, page):
        self.feed(page)
        return self.posts


def downloaded_html_files():
    flist = set([int(x[:-5]) for x in os.listdir(DIR_HTML)])  # 271508.html -> 271508
    return flist



def download(post_id):
    try:
        url = LINK_PREFIX + str(post_id)
        response = urllib.request.urlopen(url)
        log.debug('Load "{}"... {} {}'.format(url, response.reason, response.getcode()))

    except (urllib.error.URLError, urllib.error.HTTPError) as exception:
        if exception.code == 404:
            log.debug('Load "{}"... {} {}'.format(url, exception.reason, exception.code))
        else:
            log.error('Load "{}"... {} {}'.format(url, exception.reason, exception.code))

    else:
        if response.getcode() == 200:
            path = '{}{}.html'.format(DIR_HTML, post_id)
            text = response.read().decode('utf-8')
            with open(path, 'w') as fout:
                fout.write(text)
            log.debug('Store {} to {}... {} KB'.format(url, path, round(os.path.getsize(path) // KB_SIZE)))


def download_100():
    files = downloaded_html_files()
    files2 = list(files)
    files2.sort(reverse=True)
    for p in range(100):
        url = 'http://geektimes.ru/all/page{}/'.format(p + 1)
        response = urllib.request.urlopen(url)
        log.debug('Load "{}"... {} {}'.format(url, response.reason, response.getcode()))
        text = response.read().decode('utf-8')
        posts_to_check = Parser_page_all().parse(text)
        for post in posts_to_check:
            if post not in files:
                download(post)


def download_range(first, last):
    html_files = downloaded_html_files()
    for post in range(first, last + 1):
        if post not in html_files:
            download(post)
