#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn import metrics
import sklearn
import numpy as np

from config import *
from utils import *

class DataSet:
    # what about numpy?..
    def __init__(self):
        self.data = list()
        self.target = list()
        self.target_names = list()


def later_i_will_use_it():
    # grid search
    parameters = {'tfidf__use_idf': (True, False),
                  'clf__alpha': (1e-2, 1e-3),
                  'cls__penalty': ('none', 'l2', 'l1', 'elasticnet')
                 }
    gs_clf = GridSearchCV(text_clf, parameters, n_jobs=-1)
    gs_clf = gs_clf.fit(train.data, train.target)
    train.target_names[gs_clf.predict(['God is love'])]
    predicted = gs_clf.predict(test.data)
    np.mean(predicted == test.target)
    print('Best parameters:')
    params = gs_clf.get_params()
    print(params['estimator__vect'])
    print(params['estimator__tfidf'])
    print(params['estimator__clf'])
    best_parameters, score, _ = max(gs_clf.grid_scores_, key=lambda x: x[1])
    for param_name in sorted(parameters.keys()):
        print("%s: %r" % (param_name, best_parameters[param_name]))
    print(score)


def get_a_structure(subset='train'):
    result = DataSet()
    with open('../data/marks.txt') as file:
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


def main():
    print(sklearn.__version__)
    print('Making a train set')
    train = get_a_structure(subset='train')
    print('Making a test set')
    test = get_a_structure(subset='test')

    text_clf = Pipeline([('vect', CountVectorizer(stop_words='english')),
                         ('tfidf', TfidfTransformer(use_idf=False)),
                         ('clf', SGDClassifier(penalty='l2',
                                               alpha=1e-3, n_iter=5, random_state=42))
                        ])
    print('Start training')
    text_clf = text_clf.fit(train.data, train.target)
    print('Start predicting')
    predicted = text_clf.predict(test.data)
    print('Score =', np.mean(predicted == test.target))

    print(metrics.classification_report(test.target, predicted,
                                        target_names=test.target_names))
    print(metrics.confusion_matrix(test.target, predicted))


if __name__ == "__main__":
    main()
