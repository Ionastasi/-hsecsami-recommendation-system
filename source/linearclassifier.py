#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ionastasi@gmail.com

from sklearn import linear_model as lm

from utils import *

FEATURES_DIR = '../data/features/'


def get_idf():
    idf = dict()
    path = FEATURES_DIR + 'all_features.txt'
    with open(path, encoding='utf-8') as file:
        for line in file.readlines():
            word, weight = line.split()
            idf[word] = float(weight)
    return idf


def get_tf(article_id):
    tf = dict()
    path = FEATURES_DIR + str(article_id) + '.txt'
    with open(path, encoding='utf-8') as file:
        for line in file.readlines():
            word, weight = line.split()
            tf[word] = float(weight)
    return tf


def get_marks():
    marks = dict()
    with open('../data/marks.txt') as file:
        for line in file.readlines():
            article_id, mark = map(int, line.split())
            if mark == 1:
                marks[article_id] = 1
            else:
                marks[article_id] = -1
    return marks


def accurancy(y_test, y_pred):
    s = 0
    for i in range(len(y_test)):
        s += (y_test[i] == y_pred[i])
    return s / len(y_test) if len(y_test) > 0 else 1.0


def precision(y_test, y_pred):
    tp = 0
    pcp = 0
    for i in range(len(y_pred)):
        if y_pred[i] == 1:
            pcp += 1
            if y_test[i] == 1:
                tp += 1
    return tp / pcp if pcp > 0 else 1.0


def recall(y_test, y_pred):
    tp, tcp = 0, 0
    for i in range(len(y_test)):
        if y_test[i] == 1:
            tcp += 1
            if y_pred[i] == 1:
                tp += 1
    return tp / tcp if tcp > 0 else 1.0


def f_score(y_test, y_pred):
    p = precision(y_test, y_pred)
    r = recall(y_test, y_pred)
    return 2 * p * r / (p + r)


def get_feature_vector(article_id, idf):
    tf = get_tf(article_id)
    vector = list()
    for word in list(idf.keys())[20000:30000]:
        if word in tf:
            vector.append(tf[word])
        else:
            vector.append(0)
    return vector


def learning():
    idf = get_idf()
    articles = list(get_articles_id())
    ids_col = len(articles)
    train_ids = articles[:ids_col * 4 // 5]
    test_ids = articles[ids_col * 4 // 5 + 1:]
    marks = get_marks()
    train_marks, test_marks, train_vectors, test_vectors = list(), list(), list(), list()
    for article_id in articles:
        print('append ', article_id)
        if article_id in train_ids:
            train_marks.append(marks[article_id])
            train_vectors.append(get_feature_vector(article_id, idf))
        else:
            test_marks.append(marks[article_id])
            test_vectors.append(get_feature_vector(article_id, idf))

    print('learning')
    classifier = lm.LinearRegression()
    classifier.fit(train_vectors, train_marks)
    print('predicting')
    pred_marks = classifier.predict(test_vectors)
    for i in range(len(pred_marks)):
        if pred_marks[i] >= 0:
            pred_marks[i] = 1
        else:
            pred_marks[i] = -1

    print('F-score = {f}'.format(f = f_score(test_marks, pred_marks)))


def main():
    learning()
    return
    print('accurancy = {accurancy}'.format(accurancy = accurancy(y_test, y_pred)))
    print('precision = {precision}'.format(precision = precision(y_test, y_pred)))
    print('recall = {recall}'.format(recall = recall(y_test, y_pred)))
    print('F-score = {f}'.format(f = f_score(y_test, y_pred)))

if __name__ == "__main__":
    main()