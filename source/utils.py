from datetime import datetime
from config import *

def load_dates(path):
    post_to_date = dict()
    with open(path) as lines:
        for line in lines:
            post, date = line.split()
            post_to_date[int(post)] = datetime.strptime(date, DATE_FORMAT)
    return post_to_date


def load_cleaned():
    with open(TEXTS_INDEX) as file:
        return set(map(int, file.readlines()))
