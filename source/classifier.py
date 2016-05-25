#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn import metrics
import numpy as np
from time import time
from random import shuffle
from collections import namedtuple

from config import *
from utils import *

'''
посмотрть статистику, которая будет больше внимания уделять ошибка 1/2 рода, когда neg считается за pos
'''

TEST_COEF = 0.3

Articles = namedtuple('Articles', ['train', 'test'])
Marked = namedtuple('Marked', ['positive', 'negative'])

class DataSet:
    # what about numpy?..
    def __init__(self):
        self.data = list()
        self.target = list()

def get_marked():
    pos, neg = list(), list()
    normalized = get_normalized()
    with open(MARKS_FILE) as lines:
        for line in lines:
            post_id, mark = map(int, line.split())
            if post_id not in normalized:
                continue
            if mark == 1:
                pos.append([post_id, mark])
            else:
                neg.append([post_id, mark])
    total = len(neg) + len(pos)
    print("negative:", len(neg), round(len(neg)/total, 2))
    print("positive:", len(pos), round(len(pos)/total, 2))
    return Marked(positive=pos, negative=neg)

def get_a_structures():
    train = DataSet()
    test = DataSet()
    marks = get_marked()
    shuffle(marks.positive)
    shuffle(marks.negative)
    for arr in (marks.positive, marks.negative):
        for_test = TEST_COEF * len(arr)
        for i in range(len(arr)):
            post_id, mark = arr[i]
            with open(NORMALIZED_DIR + str(post_id) + '.txt') as file:
                cur_data = file.read()
            if (i <= for_test):
                test.data.append(cur_data)
                test.target.append(mark)
            else:
                train.data.append(cur_data)
                train.target.append(mark)
    print("train:", len(train.data))
    print("test:", len(test.data))
    return Articles(train=train, test=test)


def scorer(estimator, X, Y):
    metric = metrics.roc_auc_score
    return metric(Y, estimator.predict_proba(X)[:, 1])


def main():
    print('Making sets for train and test')
    full_struct = get_a_structures()
    train, test = full_struct.train, full_struct.test

    text_clf = Pipeline([('vect', CountVectorizer(stop_words='english')),
                         ('tfidf', TfidfTransformer()),
                         ('clf', SGDClassifier(loss='log', n_iter=5, random_state=42))
                        ])
    parameters = {'clf__penalty': ['l2', 'l1', 'elasticnet'],
                  'clf__l1_ratio': [0.0, 0.01, 0.05], # 0.10, 0.2, 0.3, 0.4, 0.5],
                  'clf__alpha': [0.001], #0.0001, 0.00001, 0.000001, 0.0000001],
                  'tfidf__use_idf': (True, False)
                 }

    searcher = GridSearchCV(estimator=text_clf,
                            param_grid=parameters,
                            scoring=scorer,
                            cv=5,
                            n_jobs=-1
                           )
    print('Training... ', end='')
    t = time()
    searcher.fit(train.data, train.target)
    print(round(time() - t, 3))

    print("\nbest score:", round(searcher.best_score_, 3))
    print("best parameters:", searcher.best_params_, sep='\n')
    best_cls = searcher.best_estimator_
    print("\npredicted quality".upper())
    predicted = best_cls.predict(test.data)
    print("score:", round(scorer(best_cls, test.data, test.target), 3))
    print("mean:", round(np.mean(predicted == test.target), 3))
    print(metrics.confusion_matrix(test.target, predicted))


if __name__ == "__main__":
    main()
