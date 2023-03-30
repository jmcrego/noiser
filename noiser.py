import sys
import time
import json
import random
import logging
import argparse
import pyonmttok
from collections import defaultdict
from Noiser import Noiser

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--max_ratio_noises', type=float, default=0.5, help='max ratio noises per sentence (0.5)')
    parser.add_argument('--max_total_noises', type=int, default=5, help='max total noises per sentence (5)')
    parser.add_argument('--max_seen', type=int, default=100, help='max occurrences for the pair original/noised word (100)')
    parser.add_argument('--seed', type=int, default=0, help='seed for randomness (0)')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()
    logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=getattr(logging, 'INFO' if not args.debug else 'DEBUG'), filename=None)
    if args.seed != 0:
        random.seed(args.seed)
    
    onmttok = pyonmttok.Tokenizer('conservative', joiner_annotate=False)
    noiser = Noiser(args,inflect='../corrector/resources/Morphalou3.1_CSV.csv.inflect', homophone='../corrector/resources/Morphalou3.1_CSV.csv.homophone')
    
    tic = time.time()
    for l in sys.stdin:
        tok, err = noiser(onmttok(l.rstrip()))
        print(json.dumps({'tokens': tok, 'err_tags': err}, ensure_ascii=False))
    toc = time.time()
    logging.info('Done {:.2f} seconds'.format(toc-tic))
    noiser.report()
    

