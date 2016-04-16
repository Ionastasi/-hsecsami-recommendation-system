#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

import pymorphy2
import re
import log
from collections import defaultdict
import math


FEATURES_DIR = '../data/features/'
TEXT_DIR = '../data/text/'
TEXTS_INDEX = TEXT_DIR + '.index'
CYRILLIC_REG = u"[\u0400-\u0500]+"
ENG_REG = u"[a-z]+"


def get_articles_id():
    with open(TEXTS_INDEX) as file:
        return list(map(int, file.readlines()))  # set, actually


def article_analysis(filename, morph):
    print('Analysing {}'.format(filename))
    words_frequency = defaultdict(int)
    with open(filename, encoding='utf-8') as file:
        lines = file.readlines()[5:]  # on this line article begins
    for line in lines:
        for word in line.lower().split():
            for w in re.findall(CYRILLIC_REG, word) + re.findall(ENG_REG, word):
                interpretations = set(x.normal_form for x in morph.parse(w))
                for interpret in interpretations:
                    words_frequency[interpret] += 1
    return words_frequency


def all_articles_analysis(morph):
    tf = dict()
    idf = defaultdict(int)
    articles = get_articles_id()
    for article_id in articles[:10]:
        path = TEXT_DIR + str(article_id) + '.txt'
        result = article_analysis(path, morph)
        tf[article_id] = result
        for word in result.keys():
            idf[word] += 1
    articles_num = len(articles)
    for word in idf.keys():
        idf[word] = math.log(articles_num / idf[word])
    return tf, idf


def calculate_features(tf, idf):  # _and_write_ ?
    articles = get_articles_id()
    for article_id in articles[:10]:
        print('Featuring {}'.format(article_id))
        path = FEATURES_DIR + str(article_id) + '.txt'
        with open(path, 'w') as file:
            for word in tf[article_id].keys():
                weight = tf[article_id][word] * idf[word]
                file.write('{} {}\n'.format(word, weight))
    path = FEATURES_DIR + "all_features.txt"
    with open(path, 'w') as file:
        for word in idf.keys():
            file.write('{} {}\n'.format(word, idf[word]))

def main():
    morph = pymorphy2.MorphAnalyzer()
    tf, idf = all_articles_analysis(morph)
    calculate_features(tf, idf)


if __name__ == '__main__':
    main()