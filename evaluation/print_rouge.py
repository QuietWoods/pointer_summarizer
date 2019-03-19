# -*- coding: utf-8 -*-
# @Time    : 2019/1/10 20:54
# @Author  : QuietWoods
# @FileName: print_rouge.py
# @Software: PyCharm

import rouge
import json
import os
import copy
import sys


class BasicRouge(object):
    def __init__(self, dirname):

        self.hyp_dir_path = os.path.join(dirname, 'rouge_dec_dir')
        self.ref_dir_path = os.path.join(dirname, 'rouge_ref')

        self.rouge = rouge.Rouge()

    def dir_files_scores(self):
        dec_dir = self.hyp_dir_path
        refs_dir = self.ref_dir_path
        total_scores = {}
        i = 0
        for fname in os.listdir(dec_dir):
            with open(os.path.join(dec_dir, fname), 'r', encoding='utf-8') as f:
                hyp = f.read()
                # print(hyp)
            with open(os.path.join(refs_dir, fname.replace('decoded.txt', 'reference.txt')), 'r', encoding='utf-8') as f:
                ref = f.read()
                # print(ref)
            file_score = self.rouge.get_scores(hyp, ref)[0]

            if total_scores:
                for k, v in file_score.items():
                    for index, value in v.items():
                        total_scores[k][index] += value
                        assert (type(value) == float)
            else:
                total_scores = copy.deepcopy(file_score)

            # total_scores.append(file_score)
            i += 1
        print("total_score:", total_scores)
        for k, v in total_scores.items():
            for index, value in v.items():
                total_scores[k][index] /= i
        print("average total_score_merge:", total_scores)
        with open("title_average_total_score_merge.json", "w", encoding='utf-8') as w:
            json.dump(total_scores, w, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    dirname = sys.argv[1]
    if not os.path.exists(dirname):
        print('error: {} not exits.'.format(dirname))
        sys.exit(-1)
    cls = BasicRouge(dirname=dirname)
    cls.dir_files_scores()
