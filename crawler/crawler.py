#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com


import argparse
import sys

import log
import download
import clean


def parse_argument(argv):
    parser = argparse.ArgumentParser(
        prog='crawler',
        description='Download and cleaning pages from geektimes.ru, also a bit from habrahabr.ru and megamozg.ru.'
    )
    parser.add_argument(
        '--log',
        default='debug',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="changing log level, 'debug' for default"
    )

    subparsers = parser.add_subparsers(
        dest='parser_mode'
    )
    parser_update = subparsers.add_parser(
        'update',
        description="Download last 1000 posts, if they wasn't downloaded earlier.",
        help='the same that down_last'
    )
    parser_down = subparsers.add_parser(
        'down',
        description="Download last 1000 posts, if they wasn't downloaded earlier.",
        help='the same that down_last'
    )
    parser_down_last = subparsers.add_parser(
        'down_last',
        description="Download last 1000 posts, if they wasn't downloaded earlier.",
        help='download last 1000 posts'
    )

    parser_down_range = subparsers.add_parser(
        'down_range',
        description='''Download posts in some range.
                       Stops if starts downloading already downloaded posts.
                       Of course, you should set the range by --from and --to.''',
        help='download posts in some range'
    )
    parser_down_range.add_argument(
        '--from',
        required=True,
        type=int,
        dest='start_down',
        help='where range of downloading starts'
    )
    parser_down_range.add_argument(
        '--to',
        required=True,
        type=int,
        dest='end_down',
        help='where range of downloading ends'
    )
    parser_clean = subparsers.add_parser(
        'clean',
        help='the same that clean_all',
        description="Clean all htmls from tags and etc, that wasn't  cleaned earlier."
    )
    parser_clean_all = subparsers.add_parser(
        'clean_all',
        help='parse all htmls',
        description="Clean all htmls from tags and etc, that wasn't  cleaned earlier."
    )
    parser_clean_range = subparsers.add_parser(
        'clean_range',
        help='parse htmls in some range',
        description='''Clean htmls in some range, skipping already cleaned htmls.
                       Of course you should set the range by --from and --to.'''
    )
    parser_clean_range.add_argument(
        '--from',
        type=int,
        required=True,
        dest='start_clean',
        help='where range of cleaning starts'
    )
    parser_clean_range.add_argument(
        '--to',
        type=int,
        required=True,
        dest='end_clean',
        help='where range of cleaning ends'
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


def main():
    args = parse_argument(sys.argv)

    log.config(log.level(args.log_level))

    if args.parser_mode in ('update', 'down', 'down_last'):
        download.download_100()
    elif args.parser_mode == 'down_range':
        download.download_range(min(args.start_down, args.end_down),
                                max(args.start_down, args.end_down))
    elif args.parser_mode in ('clean', 'clean_all'):
        clean.clean_all()
    elif args.parser_mode == 'clean_range':
        clean.clean_range(min(args.start_clean, args.end_clean),
                          max(args.start_clean, args.end_clean))

if __name__ == '__main__':
    main()
