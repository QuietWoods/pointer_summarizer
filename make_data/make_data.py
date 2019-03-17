# -*- coding: utf-8 -*-
# @Time    : 2019/3/14 10:04
# @Author  : QuietWoods
# @FileName: make_data.py
# @Software: PyCharm
import sys
import os
import json
import hashlib
import struct
import collections
from tensorflow.core.example import example_pb2

import jieba

jieba.load_userdict('../dict/中药材词典.txt')
jieba.load_userdict('../dict/医学术语词典.txt')
jieba.load_userdict('../dict/结构词典.txt')


cp_single_close_quote = u'\u2019'  # unicode
cp_double_close_quote = u'\u201d'
END_TOKENS = ['。', '！', '？', '...', "'", "`", '"', cp_single_close_quote, cp_double_close_quote,
              ")"]  # acceptable ways to end a sentence

# 在.bin文件中我们使用这些来分隔句子
SENTENCE_START = '<s>'
SENTENCE_END = '</s>'

all_train_patents = "../patent_lists/patent_train.txt"
all_val_patents = "../patent_lists/patent_val.txt"
all_test_patents = "../patent_lists/patent_test.txt"

chinese_tokenized_patents_dir = "chinese_patents_tokenized"
finished_files_dir = "finished_files"
chunks_dir = os.path.join(finished_files_dir, "chunked")

# 中文专利标题的条数
num_expected_chinese_patents = 11414

VOCAB_SIZE = 200000
CHUNK_SIZE = 1000  # 数据块的大小


def chunk_file(set_name):
    in_file = 'finished_files/%s.bin' % set_name
    reader = open(in_file, "rb")
    chunk = 0
    finished = False
    while not finished:
        chunk_fname = os.path.join(chunks_dir, '%s_%03d.bin' % (set_name, chunk))  # new chunk
        with open(chunk_fname, 'wb') as writer:
            for _ in range(CHUNK_SIZE):
                len_bytes = reader.read(8)  # eight bits equal one byte
                if not len_bytes:
                    finished = True
                    break
                str_len = struct.unpack('q', len_bytes)[0]
                example_str = struct.unpack('%ds' % str_len, reader.read(str_len))[0]
                writer.write(struct.pack('q', str_len))
                writer.write(struct.pack('%ds' % str_len, example_str))
            chunk += 1


def chunk_all():
    # Make a dir to hold the chunks
    if not os.path.isdir(chunks_dir):
        os.mkdir(chunks_dir)
    # Chunk the data
    for set_name in ['train', 'val', 'test']:
        print("Splitting %s data into chunks..." % set_name)
        chunk_file(set_name)
    print("Saved chunked data in %s" % chunks_dir)


def segments_title_file(input, output):
    """
    对json文本分词
    :param input: 未分词文本
    :param output: 分词后的文本
    :return:
    """
    with open(input, 'r', encoding='utf-8') as fin, open(output, 'w', encoding='utf-8') as fout:
        data = json.load(fin)
        tokenized_data = collections.OrderedDict()
        tokenized_data['src_claim'] = segment_text(data['src_claim'])
        tokenized_data['label_IT'] = deal_IT_USE(data['label_IT'])
        tokenized_data['label_USE'] = deal_IT_USE(data['label_USE'])
        tokenized_data['src_title'] = segment_text(data['src_title'])
        tokenized_data['label_title'] = segment_text(data['label_title'])
        tokenized_data['id'] = data['id']
        # print(tokenized_data)
        json.dump(tokenized_data, fout, ensure_ascii=False, indent=4)


def segment_text(input_str):
    """
    分词
    :param input_str:
    :return:
    """
    if input_str:
        input_str = ' '.join(jieba.cut(input_str))
    return input_str


def deal_IT_USE(input_str):
    """
    处理专利的新词和功效词
    :param input_str:
    :return:
    """
    if input_str:
        input_str = ' '.join(input_str.split('；'))
    return input_str


def tokenize_patents(patents_dir, tokenized_patents_dir):
    """使用结巴分词工具映射专利文本到一个分词版本目录
    ### patents_dir: r"G:\data\patent\tmp\title_data"
    ### tokenized_patents_dir: r"G:\data\patent\tmp\title_data_tokenized"
    """
    print("Preparing to tokenize %s to %s..." % (patents_dir, tokenized_patents_dir))
    patents = os.listdir(patents_dir)
    # make IO list file
    print("Making list of files to tokenize...")
    mapping = []
    for s in patents:
        mapping.append((os.path.join(patents_dir, s), os.path.join(tokenized_patents_dir, s)))
    print("Tokenizing %i files in %s and saving in %s..." % (len(patents), patents_dir, tokenized_patents_dir))
    # 根据路径映射，进行专利文本分词
    for patent in mapping:
        segments_title_file(patent[0], patent[1])
    del mapping
    print("jieba Tokenizer has finished.")

    # 检查分词后的专利数量和源专利数量是否一致
    num_orig = len(os.listdir(patents_dir))
    num_tokenized = len(os.listdir(tokenized_patents_dir))
    if num_orig != num_tokenized:
        raise Exception(
            "The tokenized patents directory %s contains %i files, but it should contain the same number as %s (which has %i files). Was there an error during tokenization?" % (
            tokenized_patents_dir, num_tokenized, patents_dir, num_orig))
    print("Successfully finished tokenizing %s to %s.\n" % (patents_dir, tokenized_patents_dir))


def load_json_file(json_file):
    with open(json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    return data


def read_text_file(text_file):
    lines = []
    with open(text_file, "r", encoding='utf-8') as f:
        for line in f:
            lines.append(line.strip())
    return lines

def hashhex(s):
    """Returns a heximal formated SHA1 hash of the input string."""
    h = hashlib.sha1()
    h.update(s)
    return h.hexdigest()


def get_url_hashes(url_list):
    return [hashhex(url) for url in url_list]


def fix_missing_period(line):
    """Adds a period to a line that is missing a period"""
    if line == "": return line
    if line[-1] in END_TOKENS: return line
    # print line[-1]
    return line + " 。"


def get_art_abs(patent_file, is_extra_info=False):
    data = load_json_file(patent_file)
    #
    if is_extra_info:
        abstract = data['label_IT'] + data['lable_USE'] + data['src_claim']
    else:
        abstract = data['src_claim']
    article = fix_missing_period(abstract)
    # Make abstract into a signle string, putting <s> and </s> tags around the sentences
    abstract = "%s %s %s" % (SENTENCE_START, data['label_title'], SENTENCE_END)

    return article, abstract


def write_to_bin(patent_list_file, out_file, makevocab=False):
    """根据专利号列表，把专利标题训练数据写入文本中"""
    print("Making bin file for patents listed in %s..." % patent_list_file)
    patent_lists = read_text_file(patent_list_file)
    patent_fnames = [s + ".json" for s in patent_lists]
    num_patents = len(patent_fnames)

    if makevocab:
        vocab_counter = collections.Counter()

    with open(out_file, 'wb') as writer:
        for idx, s in enumerate(patent_fnames):
            if idx % 1000 == 0:
                print("Writing patent %i of %i; %.2f percent done" % (
                idx, num_patents, float(idx) * 100.0 / float(num_patents)))

            # 根据当前的专利号去已经分词的目录中找对应的专利文本
            if os.path.isfile(os.path.join(chinese_tokenized_patents_dir, s)):
                patent_file = os.path.join(chinese_tokenized_patents_dir, s)
            else:
                print(
                    "Error: Couldn't find tokenized patent file %s in tokenized patent directories %s. Was there an error during tokenization?" % (
                    s, chinese_tokenized_patents_dir))
                # 再次检查分词目录包含的专利文本数量是否等于未分词专利数量
                print("Checking that the tokenized patents directories %s contains correct number of files..." % (
                    chinese_tokenized_patents_dir))
                check_num_patents(chinese_tokenized_patents_dir, num_expected_chinese_patents)
                raise Exception(
                    "Tokenized patents directories %s contains correct number of files but patent file %s found." % (
                    chinese_tokenized_patents_dir, s))

            # 写入.bin file
            article, abstract = get_art_abs(patent_file, False)
            # Write to tf.Example
            tf_example = example_pb2.Example()
            tf_example.features.feature['article'].bytes_list.value.extend([bytes(article, encoding='utf-8')])
            tf_example.features.feature['abstract'].bytes_list.value.extend([bytes(abstract, encoding='utf-8')])
            tf_example_str = tf_example.SerializeToString()
            str_len = len(tf_example_str)
            writer.write(struct.pack('q', str_len))
            writer.write(struct.pack('%ds' % str_len, tf_example_str))

            # Write the vocab to file, if applicable
            if makevocab:
                art_tokens = article.split(' ')
                abs_tokens = abstract.split(' ')
                abs_tokens = [t for t in abs_tokens if
                              t not in [SENTENCE_START, SENTENCE_END]]  # remove these tags from vocab
                tokens = art_tokens + abs_tokens
                tokens = [t.strip() for t in tokens]  # strip
                tokens = [t for t in tokens if t != ""]  # remove empty
                vocab_counter.update(tokens)

    print("Finished writing file %s\n" % out_file)

    # 将词表写入本地文本
    if makevocab:
        print("Writing vocab file...")
        with open(os.path.join(finished_files_dir, "vocab"), 'w', encoding='utf-8') as writer:
            for word, count in vocab_counter.most_common(VOCAB_SIZE):
                writer.write(word + ' ' + str(count) + '\n')
        print("Finished writing vocab file")


def check_num_patents(patents_dir, num_expected):
    num_patents = len(os.listdir(patents_dir))
    if num_patents != num_expected:
        raise Exception(
            "patents directory %s contains %i files but should contain %i" % (patents_dir, num_patents, num_expected))


if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print("USAGE: python make_data.py <chinese_patents_dir>")
    #     sys.exit()
    # chinese_patents_dir = sys.argv[1]

    chinese_patents_dir = r"G:\data\patent\tmp\title_data"
    chinese_tokenized_patents_dir = r"G:\data\patent\tmp\title_data_tokenized"

    # 检查专利目录包含正确的专利数量
    check_num_patents(chinese_patents_dir, num_expected_chinese_patents)

    # 创建新目录
    if not os.path.exists(chinese_tokenized_patents_dir): os.makedirs(chinese_tokenized_patents_dir)
    if not os.path.exists(finished_files_dir): os.makedirs(finished_files_dir)

    # 利用结巴分词，输出到分词后的目录中
    # tokenize_patents(chinese_patents_dir, chinese_tokenized_patents_dir)

    # 读取分词后的专利标题，做一些处理后写入bin文件
    write_to_bin(all_test_patents, os.path.join(finished_files_dir, "test.bin"))
    write_to_bin(all_val_patents, os.path.join(finished_files_dir, "val.bin"))
    write_to_bin(all_train_patents, os.path.join(finished_files_dir, "train.bin"), makevocab=True)

    # 将数据集分别切块
    chunk_all()
