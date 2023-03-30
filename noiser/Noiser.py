import random
import logging
from collections import defaultdict
from noiser.Misspell import Misspell
from noiser.Replace import Replace

class Noiser():
    def __init__(self, args, inflect=None, hphone=None):
        self.args = args
        self.misspell = Misspell()
        self.inflect = Replace(inflect,'inflect') if inflect is not None else None
        self.hphone = Replace(hphone,'hphone') if hphone is not None else None
        self.seen = defaultdict(int)
        self.nl, self.nt, self.nl_noised, self.nt_noised = 0, 0, 0, 0
        self.stats = defaultdict(int)
        
    def __call__(self,tok):
        err = [0] * len(tok)
        n_noises = random.randrange(0,min(self.args.max_total_noises+1,int(len(tok)*self.args.max_ratio_noises)+1))
        if n_noises:
            indexs = [i for i in range(len(tok))]
            random.shuffle(indexs)
            for i in indexs:
                if random.random() < 0.3 :
                    if self.inflect is not None and random.random() < 0.5:
                        new_tok, new_type = self.inflect(tok[i])
                        if new_tok is not None and self.seen[tok[i]+'=>'+new_tok] < self.args.max_occ:
                            self.seen[tok[i]+'=>'+new_tok] += 1
                            logging.debug('{} => {} ({}) [{}]'.format(tok[i],new_tok,self.seen[tok[i]+'=>'+new_tok], new_type))
                            tok[i] = new_tok
                            err[i] = 1
                    elif self.hphone is not None:
                        new_tok, new_type = self.hphone(tok[i])
                        if new_tok is not None and self.seen[tok[i]+'=>'+new_tok] < self.args.max_occ:
                            self.seen[tok[i]+'=>'+new_tok] += 1
                            logging.debug('{} => {} ({}) [{}]'.format(tok[i],new_tok,self.seen[tok[i]+'=>'+new_tok], new_type))
                            tok[i] = new_tok
                            err[i] = 1
                    
                if err[i] == 0 and tok[i].isalpha(): ### all chars must be alphabetic (words containing this type of chars are not allowed: 6!#%&?)
                    new_tok, new_type = self.misspell(tok[i])
                    if new_tok is not None and self.seen[tok[i]+'=>'+new_tok] < self.args.max_occ:
                        self.seen[tok[i]+'=>'+new_tok] += 1
                        logging.debug('{} => {} ({}) [{}]'.format(tok[i],new_tok,self.seen[tok[i]+'=>'+new_tok], new_type))
                        tok[i] = new_tok
                        err[i] = 1
                
                if sum(err) >= n_noises:
                    break
        ### stats
        self.nl += 1
        self.nt += len(tok)
        self.nl_noised += sum(err)>0
        self.nt_noised += sum(err)
        self.stats[sum(err)] += 1
        return tok, err

    def report(self):
        logging.info('output {} lines ({} noised) with {} tokens ({} noised)'.format(self.nl,self.nl_noised,self.nt,self.nt_noised))
        self.misspell.report()
        self.inflect.report()
        self.hphone.report()
        for k, v in sorted(self.stats.items(), key=lambda item: item[0], reverse=False): #if reverse, sorted in descending order
            logging.info('len={}\t{}'.format(k,v))
