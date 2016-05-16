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

from config import *
from utils import *

MARKS_FILE = '../data/marks.txt'

class DataSet:
    # what about numpy?..
    def __init__(self):
        self.data = list()
        self.target = list()
        self.target_names = list()


def get_a_structure(subset='train'):
    result = DataSet()
    with open(MARKS_FILE) as file:
        lines = file.readlines()
    for_train = 4 * len(lines) // 5
    if subset == 'train':
        lines = lines[for_train:]
    else:
        lines = lines[:for_train]
    for line in lines:
        post_id, mark = map(int, line.split())
        with open(NORMALIZED_DIR + str(post_id) + '.txt') as file:
            result.data.append(file.read())
        result.target.append(mark)
        if mark == 1:
            result.target_names.append('Good')
        else:
            result.target_names.append('Bad')
    return result


def scorer(estimator, X, Y):
    metric = metrics.roc_auc_score
    return metric(Y, estimator.predict_proba(X)[:, 1])


def main():
    print('Making a train set')
    train = get_a_structure(subset='train')
    print('Making a test set')
    test = get_a_structure(subset='test')

    text_clf = Pipeline([('vect', CountVectorizer(stop_words='english')),
                         ('tfidf', TfidfTransformer()),
                         ('clf', SGDClassifier(loss='log', n_iter=5, random_state=42))
                        ])
    parameters = {'clf__penalty': ['l1'], #['none', 'l2', 'l1', 'elasticnet'],
                  'clf__l1_ratio': [0.0], #[0.0, 0.01, 0.05, 0.10, 0.2, 0.3, 0.4, 0.5],
                  'clf__alpha': [0.001], #[0.001, 0.0001, 0.00001, 0.000001, 0.0000001],
                  'tfidf__use_idf': [True] #(True, False)
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

    print("\nbest score:", searcher.best_score_)
    print("best parameters:", searcher.best_params_, sep='\n')
    best_cls = searcher.best_estimator_
    print("\npredicted quality".upper())
    predicted = best_cls.predict(test.data)
    print("score:", scorer(best_cls, test.data, test.target))
    print("mean:", np.mean(predicted == test.target))
    print(metrics.classification_report(test.target, predicted,
                                         target_names=test.target_names))
    print(metrics.confusion_matrix(test.target, predicted))


if __name__ == "__main__":
    main()
