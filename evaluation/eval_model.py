""" Evaluate the baselines ont ROUGE/METEOR"""
import argparse

from os.path import join, exists

from evaluate import eval_meteor, eval_rouge


def main(args):
    dec_dir = join(args.decode_dir, 'rouge_dec_dir')

    ref_dir = join(args.decode_dir, 'rouge_ref')
    assert exists(ref_dir)

    if args.rouge:
        dec_pattern = r'(\d+_decoded).txt'
        ref_pattern = r'(\d+_reference).txt'
        output = eval_rouge(dec_pattern, dec_dir, ref_pattern, ref_dir)
        metric = 'rouge'
    else:
        dec_pattern = r'\d+_decoded.txt'
        ref_pattern = r'\d+_reference.txt'
        output = eval_meteor(dec_pattern, dec_dir, ref_pattern, ref_dir)
        metric = 'meteor'
    print(output)
    with open(join(args.decode_dir, '{}.txt'.format(metric)), 'w') as f:
        f.write(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Evaluate the output files for the RL full models')

    # choose metric to evaluate
    metric_opt = parser.add_mutually_exclusive_group(required=True)
    metric_opt.add_argument('--rouge', action='store_true',
                            help='ROUGE evaluation')
    metric_opt.add_argument('--meteor', action='store_true',
                            help='METEOR evaluation')

    parser.add_argument('--decode_dir', action='store', required=True,
                        help='directory of decoded summaries')

    args = parser.parse_args()
    main(args)
