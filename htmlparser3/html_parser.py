from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re
import lxml.html
import lxml.sax
import logging
import json
from scrapy import signals

from lxml.html.clean import Cleaner
from xml.sax.handler import ContentHandler
from .page import Page
from .utils import get_text_len
from __builtin__ import False

from .core import BlockMaker,html_to_dom ,PathInfo
from .core import preprocessor
from collections import Counter
MAX_LINK_DENSITY_DEFAULT = 0.2
LENGTH_LOW_DEFAULT = 70
LENGTH_HIGH_DEFAULT = 200
STOPWORDS_LOW_DEFAULT = 0.30
STOPWORDS_HIGH_DEFAULT = 0.32
NO_HEADINGS_DEFAULT = False
# Short and near-good headings within MAX_HEADING_DISTANCE characters before
# a good paragraph are classified as good unless --no-headings is specified.
MAX_HEADING_DISTANCE_DEFAULT = 200
DEFAULT_ENCODING = 'utf8'
DEFAULT_ENC_ERRORS = 'replace'
CHARSET_META_TAG_PATTERN = re.compile(br"""<meta[^>]+charset=["']?([^'"/>\s]+)""",
    re.IGNORECASE)

def parse(page, body ,stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT, no_headings=NO_HEADINGS_DEFAULT,
        encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS, preprocessor=preprocessor):
    html_text = body
    dom = html_to_dom(html_text, default_encoding, encoding, enc_errors)
    dom = preprocessor(dom)

    block_maker = BlockMaker.make_blocks(dom)
    return block_maker
