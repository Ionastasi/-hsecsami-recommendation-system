from datetime import datetime
from config import *


def load_dates(path):
    post_to_date = dict()
    with open(path) as file:
        for x in file.readlines():
            post, date = x.split()
            post_to_date[int(post)] = datetime.strptime(date, DATE_FORMAT)
    return post_to_date
