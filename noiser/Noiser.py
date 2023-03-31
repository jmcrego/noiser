import random
import logging
from collections import defaultdict
from noiser.Misspell import Misspell
from noiser.Replace import Replace

tag_OK = '-'
tag_MISSPELL = 'MISSPELL'
tag_INFLECT = 'INFLECT'
tag_HPHONE = 'HPHONE'

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
        n_noised = 0
        err = [tag_OK] * len(tok)
        n_noises = random.randrange(0,min(self.args.max_total+1,int(len(tok)*self.args.max_ratio)+1))
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
                            err[i] = tag_INFLECT
                            n_noised += 1
                    elif self.hphone is not None:
                        new_tok, new_type = self.hphone(tok[i])
                        if new_tok is not None and self.seen[tok[i]+'=>'+new_tok] < self.args.max_occ:
                            self.seen[tok[i]+'=>'+new_tok] += 1
                            logging.debug('{} => {} ({}) [{}]'.format(tok[i],new_tok,self.seen[tok[i]+'=>'+new_tok], new_type))
                            tok[i] = new_tok
                            err[i] = tag_HPHONE
                            n_noised += 1
                    
                if err[i] == tag_OK and tok[i].isalpha(): ### all chars must be alphabetic (words containing this type of chars are not allowed: 6!#%&?)
                    new_tok, new_type = self.misspell(tok[i])
                    if new_tok is not None and self.seen[tok[i]+'=>'+new_tok] < self.args.max_occ:
                        self.seen[tok[i]+'=>'+new_tok] += 1
                        logging.debug('{} => {} ({}) [{}]'.format(tok[i],new_tok,self.seen[tok[i]+'=>'+new_tok], new_type))
                        tok[i] = new_tok
                        err[i] = tag_MISSPELL
                        n_noised += 1
                
                if n_noised >= n_noises:
                    break
        ### stats
        self.nl += 1
        self.nt += len(tok)
        self.nl_noised += n_noised > 0
        self.nt_noised += n_noised
        self.stats[n_noised] += 1
        return tok, err

    def report(self):
        logging.info('Output {} lines ({} noised, {:.2f}%) with {} tokens ({} noised, {:.2f}%)'.format(self.nl,self.nl_noised,100.0*self.nl_noised/self.nl,self.nt,self.nt_noised,100.0*self.nt_noised/self.nt))
        self.misspell.report(self.nt_noised)
        if self.inflect is not None:
            self.inflect.report(self.nt_noised)
        if self.hphone is not None:            
            self.hphone.report(self.nt_noised)
        logging.info('#sentences by number of noisy tokens:')
        for k, v in sorted(self.stats.items(), key=lambda item: item[0], reverse=False): #if reverse, sorted in descending order
            logging.info('{}\t{}'.format(v,k))
