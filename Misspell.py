import random
import logging
import unicodedata
from collections import defaultdict

PUNCTUATION = ',.!?:;()\'"'
PUNCTUATION_CHANGE = {
    ',': '',
    '.': '',
    '!': '',
    '?': '',
    ':': '',
    ';': '',
    '(': '',
    ')': '',
    '\'': '',
    '"': '',
}

CONSONNE_DOUBLE = 'dcflsptmnrg' #bkz

VOWEL_CHANGE = {
    'a': 'eiouy',
    'e': 'aiouy',
    'i': 'aeouy',
    'o': 'aeiuy',
    'u': 'aeioy',
    'y': 'aeiou',
}

DIACRITIC_CHANGE = {
    'a': 'aàáâä',
    'e': 'eéèêë',
    'i': 'iíìîï',
    'o': 'oóòôö',
    'u': 'uúùûü',
}

DIACRITIC_NORM = {
    'a': 'a', 'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a',
    'e': 'e', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
    'i': 'i', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'o': 'o', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o',
    'u': 'u', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
}

KEYBOARD_CHANGE = {
    'q': 'was',
    'w': 'qesad',
    'e': 'wrdsfa',
    'r': 'tfdgs',
    't': 'rygfhd',
    'y': 'tuhgjf',
    'u': 'yijhkg',
    'i': 'uokjl',
    'o': 'iplkj',
    'p': "olk",
    'a': 'szqwxe',
    's': 'adxwezcqrf',
    'd': 'fscerxvwtzg',
    'f': 'dgvrtcbeyxs',
    'g': 'fhbtyvnrucd',
    'h': 'gjnyubmtiv',
    'j': 'hkmuinyo',
    'k': 'jliomu',
    'l': 'kopim',
    'z': 'xasd',
    'x': 'zcsdaf',
    'c': 'vxdfsg',
    'v': 'cbfgdh',
    'b': 'vnghfj',
    'n': 'bmhjgk',
    'm': 'njkhl',
}

def change_diacritic(letter):
    is_upper = letter.isupper()
    if is_upper:
        letter = letter.lower()
    if letter not in DIACRITIC_NORM:
        return None
    letter_norm = DIACRITIC_NORM[letter]
    if letter_norm not in DIACRITIC_CHANGE:
        return None
    new_letters = list(DIACRITIC_CHANGE[letter_norm])
    if letter in new_letters:
        new_letters.remove(letter)
    random.shuffle(new_letters)
    new_letter = new_letters[0]
    if is_upper:
        new_letter = new_letter.upper()
    return new_letter

def change_keyboard(letter):
    is_upper = letter.isupper()
    if is_upper:
        letter = letter.lower()
    if letter not in KEYBOARD_CHANGE:
        return None
    new_letters = list(KEYBOARD_CHANGE[letter])
    if letter in new_letters:
        new_letters.remove(letter)
    random.shuffle(new_letters)
    if is_upper:
        new_letters[0] = new_letters[0].upper()
    return new_letters[0]    

def change_vowel(letter):
    is_upper = letter.isupper()
    if is_upper:
        letter = letter.lower()
    if letter not in VOWEL_CHANGE:
        return None
    new_letters = list(VOWEL_CHANGE[letter])
    if letter in new_letters:
        new_letters.remove(s[i])
    random.shuffle(new_letters)
    if is_upper:
        new_letters[0] = new_letters[0].upper()
    return new_letters[0]

def consonne_double(letter):
    is_upper = letter.isupper()
    if is_upper:
        letter = letter.lower()
    if letter not in CONSONNE_DOUBLE:
        return None
    new_letter = letter + letter
    if is_upper:
        new_letter.upper()
    return new_letter

class Misspell():

    def __init__(self, weights):
        self.weights = weights
        logging.info('Built Misspell')

    def punctuation(self, txt, join):
        if txt in PUNCTUATION:
            p = random.random()
            if sum(join) == 2: #True, True
                if p < 0.5:
                    return txt, [False, True], 'punct:Lsplit'
                else:
                    return txt, [True, False], 'punct:Rsplit'
            elif sum(join) == 1:
                if join[0]: #True, False
                    if p < 0.5:
                        return txt, [False, False], 'punct:Lsplit'
                    else:
                        return txt, [False, True], 'punct:LsplitRjoin'
                elif join[1]: #False, True
                    if p < 0.5:
                        return txt, [False, False], 'punct:Rsplit'
                    else:
                        return txt, [True, False], 'punct:LjoinRsplit'
            else: #False, False
                if p < 1./3.:
                    return txt, [True, False], 'punct:Ljoin'
                elif p < 2./3.:
                    return txt, [False, True], 'punct:Rjoin'
                else:
                    return txt, [True, True], 'punct:LjoinRjoin'
        return None, None, None
                
    def __call__(self, word):
        words, types, weights = [], [], []
        
        ### repeat char i
        i = random.randrange(0,len(word))
        words.append(word[:i+1] + word[i:])
        types.append('char:repeat')
        weights.append(self.weights['char_repeat'])

        ### delete char i
        if len(word) > 1:
            i = random.randrange(0,len(word))
            words.append(word[:i] + word[i+1:])
            types.append('char:delete')
            weights.append(self.weights['char_delete'])

        ### reduce char i (i-1, i => i-1)
        if len(word) > 1:
            i = random.randrange(1,len(word))
            if word[i] == word[i-1]:
                words.append(word[:i] + word[i+1:])
                types.append('char:reduce')
                weights.append(self.weights['char_reduce'])
    
        ### swap chars i <=> i+1
        if len(word) > 1:
            i = random.randrange(0,len(word)-1)
            s = list(word)
            if s[i] != s[i+1]:
                s[i], s[i+1] = s[i+1], s[i]
                words.append(''.join(s))
                types.append('char:swap')
                weights.append(self.weights['char_swap'])
            
        ### replace char i by close in keyboard
        i = random.randrange(0,len(word))
        near_letter = change_keyboard(word[i])
        if near_letter is not None:
            types.append('char:keyboard')
            words.append(word[:i] + near_letter + word[i+1:])
            weights.append(self.weights['char_keyboard'])

        ### replace char i by same with other diacritics
        i = random.randrange(0,len(word))
        new_letter = change_diacritic(word[i])
        if new_letter is not None:
            types.append('char:diacritic')
            words.append(word[:i] + new_letter + word[i+1:])
            weights.append(self.weights['char_diacritic'])

        ### vowel change
        i = random.randrange(0,len(word))
        new_vowel = change_vowel(word[i])
        if new_vowel is not None:
            types.append('vowel:change')
            words.append(word[:i] + new_vowel + word[i+1:])
            weights.append(self.weights['vowel_change'])

        ### consonne double
        if len(word) > 2:
            i = random.randrange(1,len(word)-1)
            new_letter = consonne_double(word[i])
            if new_letter is not None:
                types.append('consonne:double')
                words.append(word[:i] + new_letter + word[i+1:])
                weights.append(self.weights['consonne_double'])
            
        ### uppercase word
        if len(word)>1 and (word.islower() or (word[0].isupper() and word[1:].islower())):
            types.append('word:uppercase')
            words.append(word.upper())
            weights.append(self.weights['word_uppercase'])

        ### lowercase word
        if len(word)>1 and (word.isupper() or (word[0].isupper() and word[1:].islower())):
            types.append('word:lowercase')
            words.append(word.lower())
            weights.append(self.weights['word_lowercase'])

        ### uppercase char
        i = random.randrange(0,len(word))
        if len(word) > 1 and word[i].islower():
            types.append('char:uppercase')
            words.append(word[0:i] + word[i].upper() + word[i+1:])
            weights.append(self.weights['char_uppercase'])

        ### lowercase char
        i = random.randrange(0,len(word))
        if len(word) > 1 and word[i].isupper():
            types.append('char:lowercase')
            words.append(word[0:i] + word[i].lower() + word[i+1:])
            weights.append(self.weights['char_lowercase'])

        ### uppercase first char in word
        if len(word)>1 and word.islower():
            types.append('word:uppercase:first')
            words.append(word[0].upper() + word[1:])
            weights.append(self.weights['word_uppercase_first'])
            
        ### lowercase first char in word
        if len(word)>1 and word[0].isupper() and word[1:].islower():
            types.append('word:lowercase:first')
            words.append(word.lower())
            weights.append(self.weights['word_lowercase_first'])
            
        return words, types, weights
    
