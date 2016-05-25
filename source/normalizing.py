#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

import pymorphy2
import re
import log
from collections import defaultdict
import math

from config import *
from utils import *

REG = r'[\u0400-\u0500a-z\d-]{2,}'
RUS_REG = r'[\u0400-\u0500a-z\d-]{4,}'
ENG_REG = r'[a-z\d-]{2,}'
BAD_REG = r'([\d-]+|.*-)'


def store_index(normalized):
    with open(NORMALIZED_INDEX, 'w') as file:
        file.write('\n'.join(map(str, normalized)))


def make_normalized_file(post_id, morph):
    normal_words = list()
    input_file = TEXT_DIR + str(post_id) + '.txt'
    output_file = NORMALIZED_DIR + str(post_id) + '.txt'
    with open(input_file, encoding='utf-8') as fin:
        lines = fin.readlines()
        for line in lines[5:]:  # on this line article begins
            for word in re.findall(REG, line.lower()):
                normal = morph.parse(word)[0].normal_form
                if (not re.match(BAD_REG, normal) and
                       (re.match(RUS_REG, normal) or re.match(ENG_REG, normal))):
                    normal_words.append(normal)
    with open(output_file, 'w') as fout:
        fout.write('\n'.join(normal_words))
    print("Post {} normalized".format(post_id))


def get_marked():
    result = set()
    with open(MARKS_FILE) as lines:
        for line in lines:
            post_id, mark = map(int, line.split())
            result.add(post_id)
    return result


def main():
    morph = pymorphy2.MorphAnalyzer()
    cleaned = load_cleaned()
    marked = get_marked()
    normalized = get_normalized()
    for post_id in (cleaned & marked - normalized):
        make_normalized_file(post_id, morph)
        normalized.add(post_id)
    store_index(normalized)

if __name__ == '__main__':
    main()
