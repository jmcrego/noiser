#coding: utf-8
import re
import sys
import logging
import edit_distance

PUNCTUATION = ',.!?:;'

#\w indicates: alphanumeric characters (as defined by str.isalnum()) as well as the underscore (_)
SPACES_PUNCT = re.compile(r'\s+(['+PUNCTUATION+'])')
NUM_SPACES_PERC = re.compile(r'(\d)\s+(%)')
WORD_PUNCT_WORD = re.compile(r'(\b[\w\'\-]+\b)(['+PUNCTUATION+'])(\b[\w\'\-]+\b)')
WORD_ENDNOPUNCT = re.compile(r'(\b[\w\'\-]+\b)$')
BEGIN_ISWORD = re.compile(r'^\w[\w\'\-]{1,}\b') #beginning word with minimum sized of 2 chars
NONVALID_CHARS = re.compile(r'[^a-zA-ZÀ-ÖØ-öø-ÿ\s]') ###this regex matches any character that is not (^) a lowercase or uppercase letter (a-zA-Z), accented characters (À-ÖØ-öø-ÿ), or a space (\s).

class Preprocess():
    def __init__(self, stream, config):
        self.stream = stream
        self.min_char_rate = config['min_char_rate'] #minimum rate of valid chars (see NONVALID_CHARS regex)
        self.min_char_len = config['min_char_len']
        self.max_char_len = config['max_char_len']

    def __iter__(self):
        for txt in self.stream:
            charsalpha = NONVALID_CHARS.sub('', txt) #remove NONVALID_CHARS
            rate = 1.0 * len(charsalpha) / len(txt) if len(txt) else 0.

            if rate < self.min_char_rate:
                logging.debug('FILT:RATE {:.5f} [{}]'.format(rate, charsalpha))
                continue
                
            changed = False
            txt1 = SPACES_PUNCT.sub(r'\1', txt)
            if txt1 != txt:
                changed = True
                logging.debug('PRE:SPACES_PUNCT {}'.format(txt1))
                
            txt2 = NUM_SPACES_PERC.sub(r'\1\2', txt1)
            if txt2 != txt1:
                changed = True
                logging.debug('PRE:NUM_SPACES_PERC {}'.format(txt2))

            txt3 = WORD_PUNCT_WORD.sub(r'\1\2 \3', txt2)
            if txt3 != txt2:
                changed = True
                logging.debug('PRE:WORD_PUNCT_WORD {}'.format(txt3))
                
            txt4 = WORD_ENDNOPUNCT.sub(r'\1.', txt3)
            if txt4 != txt3:
                changed = True
                logging.debug('PRE:WORD_ENDNOPUNCT {}'.format(txt4))

            txt5 = txt4[0].upper() + txt4[1:] if BEGIN_ISWORD.match(txt4) and txt4[0].islower() else txt4
            if txt5 != txt4:
                changed = True
                logging.debug('PRE:BEGIN_ISWORD_UPPERCASE {}'.format(txt5))
            
            if len(txt5) < self.min_char_len:                
                continue
            
            if self.max_char_len > 0 and len(txt5) > self.max_char_len:
                continue
            
            changed = changed or txt5!=txt4
            if changed:
                logging.debug('PRE {}'.format(txt5))
            yield txt5
                

class InputStream:
    """Read lines from an input stream."""
    def __init__(self, fin=None):
        self._fin = fin

    def __iter__(self):
        with open(self._fin, 'r') if self._fin is not None else sys.stdin as f:
            for l in f:
                l = l.rstrip("\r\n")
                logging.debug('RAW {}'.format(l))
                yield l

if __name__ == '__main__':

    fin = None if len(sys.argv) == 1 else sys.argv[1]
    datastream = InputStream(fin=fin)
    datastream = Preprocess(datastream, {'min_char_rate': 0.5, 'min_char_len': 1, 'max_char_len': 0})
    for l in datastream:
        print('{}'.format(l))
