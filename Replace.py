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
    def __init__(self,f,name,weight,max_returned=0):
        self.name = name
        self.weight = weight
        self.max_returned = max_returned
        self.replacements = defaultdict(list)
        with open(f,'r') as fd:
            for l in fd:
                toks = l.rstrip().split('\t')
                self.replacements[toks[0]] = toks[1:]
        logging.info('Built Replace {}: {}'.format(name,f))

    def __call__(self,txt):
        txt_lc = txt.lower()
        if txt_lc not in self.replacements:
            return [], None, None
        txts_lc = self.replacements[txt_lc]
        if self.max_returned and len(txts_lc) > self.max_returned:
            txts_lc = random.sample(txts_lc, self.max_returned)
        txts = [match_case(t, txt) for t in txts_lc]
        return txts, [self.name] * len(txts), [self.weight] * len(txts)


