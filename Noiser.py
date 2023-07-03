import sys
import yaml
import time
import random
import logging
import argparse
import pyonmttok
from Misspell import Misspell
from Replace import Replace
from Preprocess import Preprocess, InputStream
from collections import defaultdict

INITIAL_VALUE = 0
JOINER = '￭'
#NO_JOINER = '·'
#NOISED = '+'
#NO_NOISED = '-'

def read_config(file):
    with open(file, 'r') as stream:
        try:
            d=yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logging.error(e)
            sys.exit()
    return d

class Tok():
    def __init__(self, t, noised=False, ljoin=None, rjoin=None):
        self.ljoin = t.startswith(JOINER)
        self.rjoin = t.endswith(JOINER)
        self.noised = noised
        self.tok = t
        if ljoin is not None and ljoin:
            self.tok = JOINER + self.tok
        if rjoin is not None and rjoin:
            self.tok = self.tok + JOINER
            
    def __call__(self, joiners=False):
        beg = 1 if not joiners and self.ljoin else 0
        end = -1 if not joiners and self.rjoin else len(self.tok)
        return self.tok[beg:end]

def factory_INITIAL_VALUE():
    return INITIAL_VALUE

class Noiser():
    def __init__(self, stream, config):
        weights = defaultdict(int, config['weights'])
        global INITIAL_VALUE
        INITIAL_VALUE = -config['every']
        mode = 'conservative' #'aggressive'
        self.onmttok = pyonmttok.Tokenizer(mode, joiner_annotate=True)
        
        self.stream = stream
        self.hphone = Replace(config['hphone'],'hphone',weights['hphone'],max_returned=1) if 'hphone' in config else None
        self.inflect = Replace(config['inflect'],'inflect',weights['inflect'],max_returned=1) if 'inflect' in config else None
        self.misspell = Misspell(weights)
        self.every = config['every']
        self.max_noises_per_sentence = config['max_noises_per_sentence']
        self.max_noise_ratio = config['max_noise_ratio']
        self.punctuation = config['punctuation']
        if config['seed'] > 0:
            random.seed(config['seed'])
            
        self.types2n = defaultdict(int)
        self.n_tokens = 0
        self.n_noises2n = defaultdict(int)
        self.n_sentences = 0
        self.pair2lastsent = defaultdict(factory_INITIAL_VALUE)
    
    def __iter__(self):
        tic = time.time()
        for raw in self.stream:
            toks = [Tok(t) for t in self.onmttok(raw)]
            self.n_sentences += 1
            self.n_tokens += len(toks)
            logging.debug('TOK1 {}'.format([t(joiners=True) for t in toks]))
        
            noises_injected = []
            n_noises_to_inject = random.randrange(0,min(self.max_noises_per_sentence+1,int(1+len(toks)*self.max_noise_ratio)))
            if n_noises_to_inject == 0:
                self.n_noises2n[len(noises_injected)] += 1
                yield raw, raw
                continue

            indexs = [i for i in range(len(toks))]
            random.shuffle(indexs)
            for index in indexs:
                
                if len(noises_injected) >= n_noises_to_inject:
                    break

                if not toks[index]().isalpha(): ### toks[index] is NOT an alpha word
                    if self.punctuation:
                        txt, type = self.misspell.punctuation(toks[index](joiners=True)) ### in this case txt contains joiners
                        if txt is not None:
                            tok_txt = toks[index](joiners=True)+' '+txt
                            self.pair2lastsent[tok_txt] = self.n_sentences
                            self.types2n[type] += 1
                            toks[index] = Tok(txt, noised=True)
                            noises_injected.append(tok_txt+' '+type)
                            logging.debug('REPLACE {} {} [{}]'.format(tok_txt, type, self.pair2lastsent[tok_txt]))
                        
                else: ### toks[index] is an alpha word
                    replacement_txts = []
                    replacement_types = []
                    replacement_weights = []
                
                    txts, types, weights = self.inflect(toks[index]())
                    for i,txt in enumerate(txts):
                        tok_txt = toks[index]()+' '+txt
                        if self.n_sentences - self.pair2lastsent[tok_txt] >= self.every:
                            replacement_txts.append(txt)
                            replacement_types.append(types[i])
                            replacement_weights.append(weights[i])

                    txts, types, weights = self.hphone(toks[index]())
                    for i,txt in enumerate(txts):
                        tok_txt = toks[index]()+' '+txt
                        if self.n_sentences - self.pair2lastsent[tok_txt] >= self.every:
                            replacement_txts.append(txt)
                            replacement_types.append(types[i])
                            replacement_weights.append(weights[i])
                    
                    txts, types, weights = self.misspell(toks[index]())
                    for i,txt in enumerate(txts):
                        tok_txt = toks[index]()+' '+txt
                        if self.n_sentences - self.pair2lastsent[tok_txt] >= self.every:
                            replacement_txts.append(txt)
                            replacement_types.append(types[i])
                            replacement_weights.append(weights[i])

                    if len(replacement_txts):
                        i = random.choices([i for i in range(len(replacement_txts))], replacement_weights)[0]
                        tok_txt = toks[index]()+' '+replacement_txts[i]
                        self.pair2lastsent[tok_txt] = self.n_sentences
                        self.types2n[replacement_types[i]] += 1
                        toks[index] = Tok(replacement_txts[i], noised=True, ljoin=toks[index].ljoin, rjoin=toks[index].rjoin)
                        noises_injected.append(tok_txt+' '+replacement_types[i])
                        logging.debug('REPLACE {} {} [{}]'.format(tok_txt, replacement_types[i], self.pair2lastsent[tok_txt]))
            
            self.n_noises2n[len(noises_injected)] += 1
            noised = self.onmttok.detokenize([t(joiners=True) for t in toks])
            if noised != raw:
                logging.debug('TOK2 {}'.format([t(joiners=True) for t in toks]))
                logging.debug("OUT {}".format(noised))
            yield noised, raw#, noises_injected
        toc = time.time()
        self.report(toc-tic)

    def report(self,sec):
        logging.info('Output {} lines ({} tokens) in {:.2f} seconds [{:.2f} lines/sec]'.format(self.n_sentences, self.n_tokens, sec, self.n_sentences/sec))
        logging.info('Number of sentences by number of noisy tokens:')
        for k, v in sorted(self.n_noises2n.items(), key=lambda item: item[0], reverse=False): #if reverse, sorted in descending order
            logging.info('{}\t{}-noise/s'.format(v,k))
        logging.info('Number of words noised by type of noise:')
        for k, v in sorted(self.types2n.items(), key=lambda item: item[1], reverse=True): #if reverse, sorted in descending order
            logging.info('{}\t{}'.format(v,k))
        
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help="yaml config file")
    parser.add_argument('-i', type=str, default=None, help="input file (stdin)")
    parser.add_argument('-debug', action='store_true', help='Debug mode')
    args = parser.parse_args()
    logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=getattr(logging, 'INFO' if not args.debug else 'DEBUG'), filename=None)

    config = read_config(args.config)
    logging.info("config = {}".format(config))
    datastream = InputStream(fin=args.i)
    if 'preprocess' in config:
        datastream = Preprocess(datastream, config['preprocess'])
    if 'noiser' in config:
        datastream = Noiser(datastream, config['noiser'])
    for n, l in datastream:
        print(n + "\t" + l)

