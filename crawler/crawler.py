#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


import argparse
import sys

import log
import download
import clean
from config import *

'''
Вводить имя файла в clean list без ключа --file, а сразу
'''


def parse_argument(argv):
    parser = argparse.ArgumentParser(
        prog='crawler',
        description='''Download and clean posts from geektimes.ru.'''
    )
    parser.add_argument(
        '--log',
        default='error',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="log level, 'error' is default value"
    )

    subparsers = parser.add_subparsers(
        dest='parser_mode'
    )

    update = subparsers.add_parser(
        'update',
        description="Downloading pages. You can download last posts or some range of posts.",
        help='downloading pages'
    )
    update.add_argument(
        '--print-ids',
        action='store_true',
        dest='print_ids',
        help="print articles' ids"
    )
    update_subs = update.add_subparsers(
        dest='update_mode'
    )
    update_last = update_subs.add_parser(
        'last',
        description="Download latest 1000 articles, if they have not been downloaded yet.",
        help='download last 1000 posts'
    )
    update_range = update_subs.add_parser(
        'range',
        description='''Download range of posts.
                       Stops if starts downloading already downloaded posts.
                       Of course, you should set the range by --from and --to.''',
        help='download range of posts'
    )
    update_range.add_argument(
        '--from',
        required=True,
        type=int,
        dest='start_down',
        help='start of range'
    )
    update_range.add_argument(
        '--to',
        required=True,
        type=int,
        dest='end_down',
        help='end of range'
    )


    clean = subparsers.add_parser(
        'clean',
        help='cleaning pages',
        description='''Extract text of articles and meta information.
                       You can clean all pages, or some range of them, or some list.'''
    )
    clean_subs = clean.add_subparsers(
        dest='clean_mode'
    )
    clean_all = clean_subs.add_parser(
        'all',
        help='parse all htmls',
        description="Process articles, it they have been cleaned before."
    )
    clean_range = clean_subs.add_parser(
        'range',
        help='clean range of htmls',
        description='''Clean range of htmls., skipping already cleaned htmls.
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

    update.add_argument(
        '--force',
        action='store_true',
        dest='update_force',
        help='download pages even if they were downloaded earlier'
    )
    clean.add_argument(
        '--force',
        action='store_true',
        dest='clean_force',
        help='clean pages even if they were cleaned earlier'
    )

    if 'update' in sys.argv:
        if 'range' not in sys.argv and 'last' not in sys.argv:
            update.print_help()
            sys.exit(1)
    elif 'clean' in sys.argv:
        if 'range' not in sys.argv and 'all' not in sys.argv and 'list' not in sys.argv:
            clean.print_help()
            sys.exit(1)
    #else:
    #    parser.print_help()
    #    sys.exit(1)

    return parser.parse_args()


def main():
    args = parse_argument(sys.argv)
    if not args:
        return

    log.config(log.level(args.log_level))

    if args.parser_mode == 'update':
        if args.update_mode == 'last':
            download.download_last(args.print_ids, args.update_force)
        if args.update_mode == 'range':
            download.download_range(args.start_down, args.end_down,
                                    args.print_ids, args.update_force)

    if args.parser_mode == 'clean':
        if args.clean_mode == 'list':
            ids = list(map(int, open(args.clean_file).readlines()))
        elif args.clean_mode == 'all':
            htmls = list(map(int, open(HTMLS_INDEX).readlines()))
            if not htmls:
                exit()
            ids = [x for x in range(min(htmls), max(htmls) + 1)]
        elif args.clean_mode == 'range':
            first = min(args.start_clean, args.end_clean)
            last = max(args.start_clean, args.end_clean)
            ids = [x for x in range(first, last + 1)]
        clean.clean_list(ids, args.clean_force)

if __name__ == '__main__':
    main()
