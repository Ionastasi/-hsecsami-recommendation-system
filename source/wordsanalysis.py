#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

'''
Не перезаписывать то, что уже было проанализировано, без специального ключа
Индекс-файл для фич
Слова из нескольких частей (что-то, как-то) '\w+(-\w+)+'
Слова с числами, типа  Win7
Оставлять только первую нормальную форму
'''

import pymorphy2
import re
from collections import defaultdict

import log
from utils import *


FEATURES_DIR = '../data/features/'
TEXT_DIR = '../data/text/'
TEXTS_INDEX = TEXT_DIR + '.index'
CYRILLIC_REG = u"[\u0400-\u0500]+"
ENG_REG = u"[a-z]+"


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
    for article_id in articles:
        path = TEXT_DIR + str(article_id) + '.txt'
        frequency = article_analysis(path, morph)
        tf[article_id] = frequency
        for word in frequency.keys():
            idf[word] += 1
    return tf, idf


def write_tf(tf):
    articles = get_articles_id()
    for article_id in articles:
        path = FEATURES_DIR + str(article_id) + '.txt'
        with open(path, 'w') as fout:
            for word in tf[article_id].keys():
                print(word, tf[article_id][word], file=fout)


def write_idf(idf):
    path = FEATURES_DIR + "all_features.txt"
    idf = [[k, v] for v, k in idf.items()]
    idf.sort(reverse=True)
    with open(path, 'w') as fout:
        for weight, word in idf:
            print(word, weight, file=fout)


def write_tf_idf(tf, idf):
    write_tf(tf)
    write_idf(idf)


def main():
    morph = pymorphy2.MorphAnalyzer()
    tf, idf = all_articles_analysis(morph)
    write_tf_idf(tf, idf)


if __name__ == '__main__':
    main()
