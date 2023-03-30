import random
import logging
from collections import defaultdict

def match_case(txt, as_txt):
    if as_txt.isupper():
        return txt.upper()
    elif as_txt.islower():
        return txt
    elif as_txt[0].isupper() and as_txt[1:].islower():
        return txt[0].upper() + txt[1:]
    return txt

class Replace():
    def __init__(self,f,name):
        self.name = name
        self.n = 0
        self.replacements = defaultdict(list)
        self.stats = defaultdict(int)
        with open(f,'r') as fd:
            for l in fd:
                toks = l.rstrip().split('\t')
                self.replacements[toks[0]] = toks[1:]
        logging.info('Built replace {} : {}'.format(name,f))

    def __call__(self,txt):
        txt_lc = txt.lower()
        if txt_lc not in self.replacements:
            return None, None
        txts_lc = self.replacements[txt_lc]
        random.shuffle(txts_lc)
        txt_new = match_case(txts_lc[0], txt)
        self.stats[txt_new] += 1
        #logging.debug('{} => {} [{}]'.format(txt,txt_new,self.name))
        self.n += 1
        return txt_new, self.name

    def report(self):
        logging.info('Replacements:')
        logging.info('{}\t{}'.format(self.n,self.name))


