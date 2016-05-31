#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import SGDClassifier
from sklearn.grid_search import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.cross_validation import LeaveOneOut
from sklearn import metrics
import numpy as np
from time import time
from random import shuffle
from collections import namedtuple
import argparse

import log
from config import *
from utils import *

Articles = namedtuple('Articles', ['train', 'test'])
Marked = namedtuple('Marked', ['positive', 'negative'])
BestClassifier = namedtuple('BestClassifier', ['clf', 'name'])


def parse_argument():
    classifier = argparse.ArgumentParser(
        prog='classifier',
        description="Training the linear classifier for articles.",
    )
    classifier.add_argument(
        '--log',
        default='error',
        choices=['critical', 'error',  'debug'],
        dest='log_level',
        help="log level, 'error' is default value"
    )
    classifier.add_argument(
        '--steps',
        type=int,
        default=1,
        dest='steps',
        help="run learning of classifiers several times"
    )

    return classifier.parse_args()


class DataSet:
    # what about numpy?..
    def __init__(self):
        self.data = list()
        self.titles = list()
        self.target = list()
        self.target_names = list()


class ClassifierData:
    def __init__(self):
        self.name = ''
        self.clf = ''
        self.parameters = ''


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
    return Marked(positive=pos, negative=neg)


def get_a_structures(test_part=0.2):
    train = DataSet()
    test = DataSet()
    marks = get_marked()
    shuffle(marks.positive)
    shuffle(marks.negative)
    first_elements = True;  # i need two first elements in 'test' to be from differents classes
    name = 'Positive'
    for arr in (marks.positive, marks.negative):
        for_test = test_part * len(arr)
        for i in range(len(arr)):
            post_id, mark = arr[i]
            with open(NORMALIZED_DIR + str(post_id) + '.txt') as file:
                cur_data = file.read()
            with open(NORMALIZED_DIR + str(post_id) + '_title.txt') as file:
                cur_title = file.read()
            if (i <= for_test):
                test.data.append(cur_data)
                test.titles.append(cur_title)
                test.target.append(mark)
                test.target_names.append(name)
                if not (name == 'Negative' and first_elements):
                    continue
                first_elements = False
                test.data[0], test.data[-1] = test.data[-1], test.data[0]
                test.target[0], test.target[-1] = test.target[-1], test.target[0]
                test.target_names[0], test.target_names[-1] = test.target_names[-1], test.target_names[0]
            else:
                train.data.append(cur_data)
                train.titles.append(cur_title)
                train.target.append(mark)
                train.target_names.append(name)
        name = 'Negative'
    return Articles(train=train, test=test)


def scorer(estimator, X, Y):
    metric = metrics.roc_auc_score
    return metric(Y, estimator.predict_proba(X)[:, 1])


def choose_the_classifier(classifiers_to_check, data, target):
    best_classifier = None
    best_score = 0;
    best_name = ''
    for cur_classifier in classifiers_to_check:
        log.debug('Now training ' + cur_classifier.name)
        searcher = GridSearchCV(estimator=cur_classifier.clf,
                                param_grid=cur_classifier.parameters,
                                scoring=scorer,
                                cv=3,
                                n_jobs=-1
                                )
        t = time()
        searcher.fit(data, target)
        t = time() - t
        log.debug("{} min, {} sec".format(int(t // 60), round(t % 60, 3)))
        cur_best_score = searcher.best_score_
        log.debug("best score (auc): {}".format(round(cur_best_score, 3)))
        log.debug("best parameters: {}".format(searcher.best_params_))
        if cur_best_score > best_score:
            best_score = cur_best_score
            best_classifier = searcher.best_estimator_
            best_name = cur_classifier.name
    return BestClassifier(clf=best_classifier, name=best_name)


def train_classifier(step_num=1):
    average = 0
    for step in range(step_num):
        print("==STEP {}==".format(step + 1))

        sgd, multi_nb, bernoulli_nb = ClassifierData(), ClassifierData(), ClassifierData()
        sgd.name = 'SGDClassifier'
        multi_nb.name = 'MultinomialNB'
        bernoulli_nb.name = 'BernoulliNB'
        sgd.clf = Pipeline([('cnt', TfidfVectorizer()),
                            ('clf', SGDClassifier(loss='log'))
                           ])
        multi_nb.clf = Pipeline([('cnt', TfidfVectorizer()),
                                 ('clf', MultinomialNB())
                                ])
        bernoulli_nb.clf = Pipeline([('cnt', CountVectorizer()),
                                     ('clf', BernoulliNB(binarize=0.0))
                                    ])
        sgd.parameters = {'clf__penalty': ['l2', 'l1', 'elasticnet'],
                          'clf__l1_ratio': [0.0, 0.01, 0.05, 0.10, 0.2, 0.3, 0.4, 0.5],
                          'clf__alpha': [0.001, 0.0001, 0.00001, 0.000001, 0.0000001],
                          'cnt__use_idf': (True, False),
                         }
        multi_nb.parameters = {'clf__alpha': [0.001, 0.0001, 0.00001, 0.000001, 0.0000001],
                               'cnt__use_idf': (True, False),
                              }
        bernoulli_nb.parameters = {'clf__alpha': [0.001, 0.0001, 0.00001, 0.000001, 0.0000001],
                                  }
        all_classifiers = [sgd, multi_nb, bernoulli_nb]

        full_struct = get_a_structures()
        train, test = full_struct.train, full_struct.test

        print('Training... ', end='')
        t = time()
        log.debug("Train with titles:")
        best_titles_clf = choose_the_classifier(all_classifiers, train.titles, train.target)
        log.debug("Train with text:")
        for clf in all_classifiers:
            clf.parameters['cnt__max_df'] = [0.85, 0.9, 0.95, 1.0]
            clf.parameters['cnt__min_df'] = [0.01, 0.05, 0.10, 0.15, 1]
        best_texts_clf = choose_the_classifier(all_classifiers, train.data, train.target)
        t = time() - t
        print("{} min, {} sec".format(int(t // 60), round(t % 60, 3)))


        print("\npredicted quality".upper())
        print("best for titles:", best_titles_clf.name)
        print("best for text:", best_texts_clf.name)
        pred_titles = best_titles_clf.clf.predict_proba(test.titles)
        pred_texts = best_texts_clf.clf.predict_proba(test.data)
        predicted_proba = list()
        predicted_target = list()
        for i in range(len(test.data)):
            prob_neg = 0.5 * (pred_titles[i][0] + pred_texts[i][0])
            prob_pos = 0.5 * (pred_titles[i][1] + pred_texts[i][1])
            predicted_proba.append(prob_pos)
            if prob_neg > prob_pos:
                predicted_target.append(-1)
            else:
                predicted_target.append(1)


        cur_auc = metrics.roc_auc_score(test.target, predicted_proba)
        average += cur_auc
        print("auc:", round(cur_auc, 3))
        print(metrics.confusion_matrix(test.target, predicted_target))
        print(metrics.classification_report(test.target, predicted_target,
                                             target_names=test.target_names))

    print('==AVERAGE SCORE==')
    print(round(average / step_num, 3))


if __name__ == "__main__":
    args = parse_argument()
    log.config(log.level(args.log_level))

    train_classifier(step_num=args.steps)
