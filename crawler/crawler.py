#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


import argparse
import sys

import log
import download
import clean


DIR_HTML = '../data/html/'
HTMLS_INDEX = '../data/html/.index'


def parse_argument(argv):
    parser = argparse.ArgumentParser(
        prog='crawler',
        description='''Download and cleaning pages from geektimes.ru
                       and a few from habrahabr.ru and megamozg.ru
                       because of reforwarding.'''
    )

    parser.add_argument(
        '--log',
        default='error',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="changing log level, 'error' for default"
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
        dest='update_print_ids',
        help='set this if you want ids printed out'
    )
    update_subs = update.add_subparsers(
        dest='update_mode'
    )
    update_last = update_subs.add_parser(
        'last',
        description="Download last 1000 posts, if they wasn't downloaded earlier.",
        help='download last 1000 posts'
    )
    update_range = update_subs.add_parser(
        'range',
        description='''Download posts in some range.
                       Stops if starts downloading already downloaded posts.
                       Of course, you should set the range by --from and --to.''',
        help='download posts in some range'
    )
    update_range.add_argument(
        '--from',
        required=True,
        type=int,
        dest='start_down',
        help='where range of downloading starts'
    )
    update_range.add_argument(
        '--to',
        required=True,
        type=int,
        dest='end_down',
        help='where range of downloading ends'
    )


    clean = subparsers.add_parser(
        'clean',
        help='cleaning pages',
        description='''Clean pages from tags and etc.
                       You can clean all pages, or some range of them, or some list.'''
    )
    clean_subs = clean.add_subparsers(
        dest='clean_mode'
    )
    clean_all = clean_subs.add_parser(
        'all',
        help='parse all htmls',
        description="Clean all htmls from tags and etc, that wasn't  cleaned earlier."
    )
    clean_range = clean_subs.add_parser(
        'range',
        help='parse htmls in some range',
        description='''Clean htmls in some range, skipping already cleaned htmls.
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
        help='parse htmls from some list',
        description='''Clean htmls from some list you give with --file key.'''
    )
    clean_list.add_argument(
        '--file',
        required=True,
        type=str,
        dest='clean_file',
        help='cleaning posts from list in this file'
    )

    update.add_argument(
        '--force',
        action='store_true',
        dest='update_force',
        help='downloading pages even if they were downloaded earlier'
    )
    clean.add_argument(
        '--force',
        action='store_true',
        dest='clean_force',
        help='cleaning pages even if they were cleaned earlier'
    )

    if 'update' in sys.argv:
        if 'last' not in sys.argv and 'range' not in sys.argv:
            update.print_help()
            sys.exit(1)
    elif 'clean' in sys.argv:
        if 'all' not in sys.argv and 'range' not in sys.argv:
            clean.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


def main():
    args = parse_argument(sys.argv)

    log.config(log.level(args.log_level))

    if args.parser_mode == 'update':
        if args.update_mode == 'last':
            download.download_last()
        if args.update_mode == 'range':
            download.download_range(min(args.start_down, args.end_down),
                                    max(args.start_down, args.end_down))

    if args.parser_mode == 'clean':
        if args.clean_mode == 'all':
            htmls = list(map(int, open(HTMLS_INDEX).readlines()))  # 1234.html -> 1234
            if htmls:
                clean.clean_range(min(htmls), max(htmls))
        if args.clean_mode == 'range':
            clean.clean_range(min(args.start_clean, args.end_clean),
                              max(args.start_clean, args.end_clean))

if __name__ == '__main__':
    main()
