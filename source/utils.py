from config import *

def get_articles_id():
    with open(TEXTS_INDEX) as file:
        return set(map(int, file.readlines()))

los=log
penalty=