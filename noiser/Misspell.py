import random
import logging
import unicodedata
from collections import defaultdict

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
    'a': 'aaàáâä',
    'e': 'eeéèêë',
    'i': 'iiíìîï',
    'o': 'ooóòôö',
    'u': 'uuúùûü',
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
    letter_norm = unicodedata.normalize('NFD', letter)
    letter_norm = letter_norm.encode('ascii', 'ignore')
    if letter_norm not in DIACRITIC_CHANGE:
        return None
    new_letters = list(DIACRITIC_CHANGE[letter_norm])
    if letter_norm in new_letters:
        new_letters.remove(letter_norm)
    random.shuffle(new_letters)
    if is_upper:
        new_letters[0] = new_letters[0].upper()
    return new_letters[0]

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

    def __init__(self):
        self.w_char_repeat = 1
        self.w_char_delete = 5
        self.w_char_reduce = 100
        self.w_char_swap = 5
        self.w_char_keyboard = 2
        self.w_char_diacritic = 10
        self.w_word_lowercase = 100
        self.w_word_uppercase = 1
        self.w_vowel_change = 10
        self.w_consonne_double = 10
        self.stats_types = defaultdict(int)
        logging.info('Built Misspell')

    def __call__(self, word):
        words, weights, types = [], [], []

        ### repeat char i
        i = random.randrange(0,len(word))
        words.append(word[:i+1] + word[i:])
        types.append('char:repeat')
        weights.append(self.w_char_repeat)

        ### delete char i
        if len(word) > 1:
            i = random.randrange(0,len(word))
            words.append(word[:i] + word[i+1:])
            types.append('char:delete')
            weights.append(self.w_char_delete)

        ### delete char i
        if len(word) > 1:
            i = random.randrange(1,len(word))
            if word[i] == word[i-1]:
                words.append(word[:i] + word[i+1:])
                types.append('char:reduce')
                weights.append(self.w_char_reduce)
            
        ### swap chars i <=> i+1
        if len(word) > 1:
            i = random.randrange(0,len(word)-1)
            s = list(word)
            s[i], s[i+1] = s[i+1], s[i]
            words.append(''.join(s))
            types.append('char:swap')
            weights.append(self.w_char_swap)
            
        ### replace char i by close in keyboard
        i = random.randrange(0,len(word))
        near_letter = change_keyboard(word[i])
        if near_letter is not None:
            types.append('char:keyboard')
            words.append(word[:i] + near_letter + word[i+1:])
            weights.append(self.w_char_keyboard)

        ### replace char i by same with other diacritics
        i = random.randrange(0,len(word))
        new_letter = change_diacritic(word[i])
        if new_letter is not None:
            types.append('char:diacritic')
            words.append(word[:i] + new_letter + word[i+1:])
            weights.append(self.w_char_diacritic)

        ### vowel change
        i = random.randrange(0,len(word))
        new_vowel = change_vowel(word[i])
        if new_vowel is not None:
            types.append('vowel:change')
            words.append(word[:i] + new_vowel + word[i+1:])
            weights.append(self.w_vowel_change)

        ### consonne double
        if len(word) > 2:
            i = random.randrange(1,len(word)-1)
            new_letter = consonne_double(word[i])
            if new_letter is not None:
                types.append('consonne:double')
                words.append(word[:i] + new_letter + word[i+1:])
                weights.append(self.w_consonne_double)
            
        ### uppercase word
        if len(word)>1 and (word.islower() or (word[0].isupper() and word[1:].islower())):
            types.append('word:uppercase')
            words.append(word.upper())
            weights.append(self.w_word_uppercase)

        ### lowercase word
        if len(word)>1 and (word.isupper() or (word[0].isupper() and word[1:].islower())):
            types.append('word:lowercase')
            words.append(word.lower())
            weights.append(self.w_word_lowercase)

        ##############################
        ### select noise to inject ###
        ##############################
        i = random.choices([i for i in range(len(words))],weights)[0]
        self.stats_types[types[i]] += 1
        #logging.debug('{} => {} [{}]'.format(word,words[i],types[i]))
        return words[i], types[i]
    
    def report(self):
        logging.info('Noise types:')
        for k, v in sorted(self.stats_types.items(), key=lambda item: item[1], reverse=True): #if reverse, sorted in descending order
            logging.info('{}\t{}'.format(v,k))
