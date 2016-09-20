#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

import pymorphy2
import re
import log
from collections import defaultdict
import math
import argparse
import os

import log
from config import *
from utils import *


REG = r'\w+[-\w+]*'
EMPIRICAL_REG = r'[\u0400-\u0500a-z\d-]{2,}'
EMP_RUS_REG = r'[\u0400-\u0500a-z\d-]{4,}'
EMP_ENG_REG = r'[a-z\d-]{2,}'
EMP_BAD_REG = r'([\d-]+|.*-)'

BANNES_POS = ['NPRO', 'PRED', 'PREP', 'CONJ', 'PRCL', 'INTJ']  # auxiliary parts of speech

def parse_argument():
    normalizing = argparse.ArgumentParser(
        prog='normalizing',
        description="Making the bag of words with normal forms.",
    )
    normalizing.add_argument(
        '--log',
        default='error',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="log level, 'error' is default value"
    )
    normalizing.add_argument(
        '--empirical',
        action='store_true',
        dest='empirical',
        help="what kind of regular expression is used"
    )
    normalizing.add_argument(
        '--clean',
        action='store_true',
        dest='clean',
        help="delete all normalized articles"
    )

    return normalizing.parse_args()


def store_index(normalized):
    with open(NORMALIZED_INDEX, 'w') as file:
        file.write('\n'.join(map(str, normalized)))


def get_marked():
    result = set()
    with open(MARKS_FILE) as lines:
        for line in lines:
            post_id, mark = map(int, line.split())
            result.add(post_id)
    return result


def delete_normalized():
    with open(NORMALIZED_INDEX, 'w') as file:
        file.write('')
    for file in os.listdir(NORMALIZED_DIR):
        if file.endswith('.txt'):
            os.remove(NORMALIZED_DIR + file)

def get_words_from_line(line, morph, empirical):
    store_list = list()
    line = line.lower().replace(chr(1105), chr(1077))  # ё -> е
    if not empirical:
        all_words = re.findall(REG, line)
    else:
        all_words = re.findall(EMPIRICAL_REG, line)
    for word in all_words:
        parsed_word = morph.parse(word)[0]
        if not empirical:
            if (parsed_word.tag.POS not in BANNES_POS):
                store_list.append(parsed_word.normal_form)
        else:
            normal = parsed_word.normal_form
            if (not re.match(EMP_BAD_REG, normal) and
                    (re.match(EMP_RUS_REG, normal) or re.match(EMP_ENG_REG, normal))):
                store_list.append(normal)
    return store_list


def make_normalized_file(post_id, morph, empirical):
    input_file = TEXT_DIR + str(post_id) + '.txt'
    output_file = NORMALIZED_DIR + str(post_id) + '.txt'
    output_title_file = NORMALIZED_DIR + str(post_id) + '_title.txt'
    with open(input_file, encoding='utf-8') as fin:
        lines = fin.readlines()

        # title
        words = get_words_from_line(lines[4], morph, empirical=True)
        with open(output_title_file, 'w') as fout:
            fout.write('\n'.join(words))

        # keywords
        words = get_words_from_line(lines[2], morph, empirical)
        with open(output_file, 'a') as fout:
            for step in range(5):  # keywords have higher weight
                fout.write('\n'.join(words))

        # articles text
        words = get_words_from_line(' '.join(lines[6:]), morph, empirical)
        with open(output_file, 'a') as fout:
            fout.write('\n'.join(words))
    log.debug("Post {} normalized".format(post_id))


def normalize(empirical=False):
    morph = pymorphy2.MorphAnalyzer()
    cleaned = load_cleaned()
    marked = get_marked()
    normalized = get_normalized()
    for post_id in (cleaned & marked - normalized):
        make_normalized_file(post_id, morph, empirical)
        normalized.add(post_id)
    store_index(normalized)


if __name__ == '__main__':
    args = parse_argument()
    log.config(log.level(args.log_level))
    if args.clean:
        delete_normalized()
    else:
        normalize(args.empirical)
