#from __future__ import absolute_import
#from __future__ import division, print_function, unicode_literals
# -*- coding: utf8 -*-

'''
Created on May 8, 2016

@author: wuwenjun
'''
import logging


import re
import os
import sys
import pkgutil


MULTIPLE_WHITESPACE_PATTERN = re.compile(r"\s+", re.UNICODE)
def normalize_whitespace(string):
    """Translates multiple white-space into single space."""
    return MULTIPLE_WHITESPACE_PATTERN.sub(" ", string)

def is_chinese(c):
    import re
    re_words = re.compile(u"[\u4e00-\u9fa5]+")
    results =  re.findall(re_words, c)
    if results:
        return True
    return False

def char_type(c):
    eng = (c >='a' and c <= 'z' ) or (c >='A' and c <= 'Z')
    num =(c>=0 and c<=9)
    if eng : 
        return 1
    elif is_chinese(c):
        return 2
    elif num:
        return 3 
    return 4

def word_counts(text):
    cnt=0
    text=text.strip()
    last_type = -1
    for i in range(len(text)):
        type = char_type(text[i])
        if type != last_type and (type == 1 or type==3) :
            cnt += 1
        if type == 2 : 
            cnt += 1
        last_type = type
    return cnt

def get_text_len(text):
    cnt=0
    text=text.strip()
    last_type = -1
    for i in range(len(text)):
        type = char_type(text[i])
        if type == 1:
            if type!=last_type:
                cnt += 1
        else:
            cnt += 1
        last_type = type
    return cnt 
    



    
    
def get_chinese_text(text):
    import re
    re_words = re.compile(u"[\u4e00-\u9fa5]+")
    results =  re.findall(re_words, text)
    chinese_text = ''.join(results)
    return  chinese_text


def is_blank(string):
    """
    Returns `True` if string contains only white-space characters
    or is empty. Otherwise `False` is returned.
    """
    return not bool(string.lstrip())


def get_stoplists():
    """Returns a collection of built-in stop-lists."""
    path_to_stoplists = os.path.dirname(sys.modules["justext"].__file__)
    path_to_stoplists = os.path.join(path_to_stoplists, "stoplists")

    stoplist_names = []
    for filename in os.listdir(path_to_stoplists):
        name, extension = os.path.splitext(filename)
        if extension == ".txt":
            stoplist_names.append(name)

    return frozenset(stoplist_names)


def get_stoplist(language):
    """Returns an built-in stop-list for the language as a set of words."""
    file_path = os.path.join("stoplists", "%s.txt" % language)
    try:
        stopwords = pkgutil.get_data("justext", file_path)
    except IOError:
        raise ValueError(
            "Stoplist for language '%s' is missing. "
            "Please use function 'get_stoplists' for complete list of stoplists "
            "and feel free to contribute by your own stoplist." % language
        )

    return frozenset(w.decode("utf8").lower() for w in stopwords.splitlines())

text="Copyright 2016 Sohu.com Inc. All Rights Reserved."
print get_text_len(text.decode("utf8"))
