# -*- coding: utf-8 -*-
# @Time    : 2019/2/23 23:02
# @Author  : QuietWoods
# @FileName: make_title_data.py
# @Software: PyCharm
import os
import json
import collections

# 专利文本目录
PATENT_DIR = r"G:\data\patent\tmp\patent_corpus_deduplicate"


def extract_title_train_data(source):
    """
    从专利语料中提取出权利要求的第一句话，关键词项，功效项，原始标题和人工标题。
    :param source:
    :return:
    """
    result = collections.OrderedDict()
    if source['src_claim']:
        result['src_claim'] = source['src_claim'].split('。')[0] + '。'
    else:
        result['src_claim'] = None
    if source['label_IT']:
        result['label_IT'] = '；'.join(source['label_IT'].split('；')[:3])
    else:
        result['label_IT'] = None
    if source['label_USE']:
        result['label_USE'] = '；'.join(source['label_USE'].split('；')[:3])
    else:
        result['label_USE'] = None
    if source['src_title']:
        result['src_title'] = source['src_title']
    else:
        result['src_title'] = None
    if source['label_title']:
        result['label_title'] = source['label_title']
    else:
        result['label_title'] = None
    return result


def make_title_train_data(patent_dir, title_dir):
    """
    组建标题改写训练数据
    :param patent_dir:
    :param title_dir:
    :return:
    """
    if not os.path.exists(patent_dir) or not os.path.exists(title_dir):
       return None
    for num, fname in enumerate(os.listdir(patent_dir)):
        with open(os.path.join(patent_dir, fname), 'r', encoding='utf-8') as fin:
            data = json.load(fin)
            title_data = extract_title_train_data(data)
            title_data['id'] = fname.split('.')[0]
            with open(os.path.join(title_dir, fname), 'w', encoding='utf-8') as fout:
                json.dump(title_data, fout, ensure_ascii=False, indent=4)
                if num % 1000 == 0:
                    print(num)


def make_title_train_csv(title_data_dir, title_csv_dir):
    """
    组建标题改写训练数据,csv
    :param title_data_dir:
    :param title_csv_dir:
    :return:
    """
    if not os.path.exists(title_data_dir) or not os.path.exists(title_csv_dir):
       return None

    fout = open(os.path.join(title_csv_dir, 'title_train_data.csv'), 'w', encoding='utf-8')

    for num, fname in enumerate(os.listdir(title_data_dir)):
        row_title = []
        with open(os.path.join(title_data_dir, fname), 'r', encoding='utf-8') as fin:
            data = json.load(fin)
            row_title.append(data['id'])
            row_title.append(data['src_claim'])
            row_title.append(data['label_IT'] if data['label_IT'] else '')
            row_title.append(data['label_USE']if data['label_USE'] else '')
            row_title.append(data['src_title'])
            row_title.append(data['label_title'])
        fout.write("{}\n".format('\t'.join(row_title)))

        if num % 1000 == 0:
            print(num)

    fout.close()


if __name__ == "__main__":
    title_dir_str = r"G:\data\patent\tmp\title_data"
    # make_title_train_data(PATENT_DIR, title_dir_str)
    make_title_train_csv(title_dir_str, r"G:\data\patent\tmp\title_csv_data")




