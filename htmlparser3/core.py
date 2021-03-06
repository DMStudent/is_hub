# -*- coding: utf8 -*-

"""
Copyright (c) 2011 Jan Pomikalek

This software is licensed as described in the file LICENSE.rst.
"""

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re
import copy
import lxml.html
import lxml.sax
from .element import LinkNode, TextNode, ImageNode, UserInteractNode, InputNode,  FONT_TAGS
from lxml.html.clean import Cleaner
from xml.sax.handler import ContentHandler
from .block import Block
from ._compat import unicode, ignored
from .utils import is_blank, get_stoplist, get_stoplists
from .utils import get_text_len
from .utils import normalize_whitespace
from collections import deque
import logging
import string
from .block import WebkitStyle
from .block import text_tag_info
MAX_LINK_DENSITY_DEFAULT = 0.2
LENGTH_LOW_DEFAULT = 70
LENGTH_HIGH_DEFAULT = 200
STOPWORDS_LOW_DEFAULT = 0.30
STOPWORDS_HIGH_DEFAULT = 0.32
NO_HEADINGS_DEFAULT = False
# Short and near-good headings within MAX_HEADING_DISTANCE characters before
# a good paragraph are classified as good unless --no-headings is specified.
MAX_HEADING_DISTANCE_DEFAULT = 200
# article is html5 tag
BLOCK_TAGS = [
    'html','body','div','table','tbody','tr','td','th','dl','section','ul',
]
#SUB_BLOCK_TAGS = []
TITLE_TAGS = ['h1', 'h2','h3','h4', 'h5', 'h6']
BIG_TITLE_TAGD = ['h1', 'h2', 'h3']
USER_INTERACTION_TAGS=['select', 'button', 'textarea', 'form']

TEXT_PUNCTUATION={',','.','，', '。'}

TAG_IGNORED = {'br', 'center'}

DEFAULT_ENCODING = 'utf8'
DEFAULT_ENC_ERRORS = 'replace'
CHARSET_META_TAG_PATTERN = re.compile(br"""<meta[^>]+charset=["']?([^'"/>\s]+)""",
    re.IGNORECASE)

from .block_tree import Tree


def html_to_dom(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """Converts HTML to DOM."""
    if isinstance(html, unicode):
        decoded_html = html
        # encode HTML for case it's XML with encoding declaration
        forced_encoding = encoding if encoding else default_encoding
        html = html.encode(forced_encoding, errors)
    else:
        decoded_html = decode_html(html, default_encoding, encoding, errors)

    try:
        dom = lxml.html.fromstring(decoded_html)
    except ValueError:
        dom = lxml.html.fromstring(html)

    return dom


def decode_html(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """
    Converts a `html` containing an HTML page into Unicode.
    Tries to guess character encoding from meta tag.
    """
    if isinstance(html, unicode):
        return html

    if encoding:
        return html.decode(encoding, errors)

    match = CHARSET_META_TAG_PATTERN.search(html)
    if match:
        declared_encoding = match.group(1).decode("ASCII")
        logging.info("wuwenjun debug declared_encoding %s", declared_encoding)
        # proceed unknown encoding as if it wasn't found at all
        with ignored(LookupError):
            return html.decode(declared_encoding, errors)

    # unknown encoding
    try:
        logging.info(default_encoding)
        # try UTF-8 first
        return html.decode(default_encoding)
    except UnicodeDecodeError:
        # try lucky with default encoding
        try:
            return html.decode("gb2312", errors)
        except UnicodeDecodeError as e:
            raise Exception("Unable to decode the HTML to Unicode: " + unicode(e))


def preprocessor(dom):
    "Removes unwanted parts of DOM."
    options = {
        "processing_instructions": False,
        "remove_unknown_tags": False,
        "safe_attrs_only": False,
        "page_structure": False,
        "annoying_tags": False,
        "frames": False,
        "meta": False,
        "links": False,
        "javascript": True,
        "scripts": True,
        "comments": True,
        "style": False,
        "embedded": False,
        "forms": False,
        #"kill_tags":("head") has strange problem
        "kill_tags": ("head",),
    }
    logging.info("wwj debug clean header")
    cleaner = Cleaner(**options)

    return cleaner.clean_html(dom)


class BlockMaker(ContentHandler):
    """
    A class for converting a HTML page represented as a DOM object into a list
    of paragraphs.
    """

    @classmethod
    def make_blocks(cls, root):
        """Converts DOM into paragraphs."""
        handler = cls()
        '''handler interface'''
        lxml.sax.saxify(root, handler)
        return handler

    def __init__(self):
        self.path = PathInfo()
        self.block_info = Tree("BLOCK")
        self.user_node_info = Tree("UserNode")
        self.block = None
        self.other_block = None
        self.link_node = None
        #to set after_is_text
        self.last_link_obj = None
        self.user_interact_node = None
        self.br = False
        self.all_text_nodes_textlen = 0
        self.all_text_tags_count = 0
        self.start_position = 0
        self._start_new_block()
        self.tag = None
        
        
        self.before_is_text = False
        self.after_is_text = False
        self.before_text = ""
        self.after_text = ""
        
        self.is_title_tag = False
        self.h1_tag_count = 0
        self.h2_tag_count = 0
        self.h3_tag_count = 0

    def _start_new_block(self):
        self.block = Block(self.path)
        self.block.start_position = self.start_position
        self.block_info.append(self.block)
    
    def _end_new_block(self):

        self.other_block = None
        self.link_node = None
        self.user_interact_node = None
        self.block_info.pop()
        father_block = self.block_info.top()
        if father_block is not None:
            self.block = father_block
            
    
    def startElementNS(self, name, qname, attrs):
        name = name[1]
        if name in TAG_IGNORED:
            return
        self.path.append(name)
        xpath_sections = self.path.xpath.split("/")
        webkit_style = None
        self.element_visible = True
        _attributs = {}
        class_attr = attrs.get((None, 'class'), "")
        for key in attrs.keys():
            _attributs[key[1]] = attrs[key]
        
        if (None, 'webkit_style') in attrs.keys():
            webkit_str=attrs[(None, 'webkit_style')]
            webkit_style = WebkitStyle.create_webkitstyle_from_str(webkit_str)
            # 注意：这里是宽度和高度都为0
            if float(webkit_style.height) == float(0) and float(webkit_style.width) == float(0):
                #logging.info("wwj debug invisible %s", self.path.xpath)
                self.element_visible = False
        
        #<a href> <div> text</div></a>
        if name not in FONT_TAGS:
            self.after_is_text = False
            self.last_link_obj = None
            if name !='a':
                self.before_is_text = False
         
        '''
        <a href="http://www.baidu.com">
        <div>
            <p>text </p>
        <div>
        </a>
        '''
        if name in BLOCK_TAGS and (self.link_node is None) and (self.other_block is None):
            self._start_new_block()
            self.block.class_attr = class_attr
            if webkit_style :
                self.block.webkit_style = webkit_style
                self.block.visible = self.element_visible
                self.block.attributes = _attributs
                '''add xpath to gap_tags'''
                for path in xpath_sections:
                    if path:
                        tag_name = path.split('[')[0]
                        self.block.gap_tags[tag_name]+=1
        else:
            if not self.link_node :
                        
                if self.other_block is None:
                    self.other_block = Block(self.path)
                    self.other_block.class_attr = class_attr 
                    self.other_block.visible = self.element_visible
                    self.other_block.webkit_style = webkit_style
                    self.other_block.start_position = self.start_position
                    self.other_block.attributes = _attributs
                    for path in xpath_sections:
                        if path :
                            tag_name = path.split('[')[0]
                            self.other_block.gap_tags[tag_name]+=1
                    
                    self.block.other_blocks.append(self.other_block)
                    logging.info("wwj debug create other_block %s %s", 
                                 self.other_block.xpath, self.block.xpath)
                      
                
            #if name == "br":
            # the <br><br> is a paragraph separator and should not be included in the number of tags within the paragraph
            #    self.block.tags_count += 1
                
            self.br = bool(name == "br")
            if self.block is not None:
                self.block.all_tags.append(self.path.xpath)
            if self.other_block is not None:
                self.other_block.all_tags.append(self.path.xpath)
            if name == 'a':
                if (None, 'href') in attrs.keys():
                    href_value  = attrs[(None, 'href')].lower()
                    #if not link.startswith("#"): 
                    self.tag = attrs[(None, 'href')]
                    #if self.element_visible:
                    self.link_node = LinkNode(self.start_position, self.element_visible,self.path, self.block, self.other_block, href_value)
                    self.link_node.before_is_text = self.before_is_text
                    self.link_node.attributes = _attributs
                        
                    if webkit_style:
                        self.link_node.webkit_style = webkit_style

                    
                    if (None, 'onclick') in attrs.keys():
                        self.link_node.has_onclick = True
                        self.block.onclick_link_node_list.append(self.link_node) if self.block is not None else 1
                        self.other_block.onclick_link_node_list.append(self.link_node) if self.other_block is not None else 1
                    
                    if (None, 'onload') in attrs.keys():
                        self.link_node.has_onload = True
                        self.block.onload_link_node_list.append(self.link_node) if self.block is not None else 1
                        self.other_block.onload_link_node_list.append(self.link_node) if self.other_block is not None else 1

                    if self.block is not None:
                        self.block.all_link_node_list.append(self.link_node)
                        self.link_node.block = self.block
                    
                    if self.other_block is not None:
                        self.other_block.all_link_node_list.append(self.link_node)
                        self.link_node.other_block = self.other_block

                            
            if name == 'img':
                if self.link_node:
                    if self.element_visible:
                        self.link_node.visible = 1
                    self.link_node.image_count += 1 
                    self.block.img_link_node_list.append(self.link_node)
                    self.other_block.img_link_node_list.append(self.link_node) if self.other_block is not None else 1
                image_node = ImageNode(self.start_position, self.element_visible, self.path, self.block, self.other_block)
                self.block.image_node_list.append(image_node) if self.block is not None else 1
                self.other_block.image_node_list.append(image_node) if self.other_block is not None else 1
            
            if name in TITLE_TAGS:
                self.is_title_tag = True
                self.block.has_title_tag = True
                if self.other_block:
                    self.other_block.has_title_tag = True

            if name == 'h1':
                self.h1_tag_count+=1
            if name == 'h2':
                self.h2_tag_count+=1
            if name == 'h3':
                self.h3_tag_count+=1


            if name == "input":
                #input标签没有charactor。有value属性等等 
                _input_node = InputNode(self.start_position, self.element_visible, self.path, self.block, self.other_block)
                _input_node.attributes = _attributs
                if (None, 'type') in attrs.keys():
                    _type  = attrs[(None, 'type')].lower()
                    _input_node.set_type(_type)
                if self.block:
                    self.block.input_node_list.append(_input_node)
                if self.other_block:
                    self.other_block.input_node_list.append(_input_node)
            #<form><button> </button><form>
            #if name in USER_INTERACTION_TAGS and self.user_interact_node is None:
            if name in USER_INTERACTION_TAGS:
                logging.info("wwj debug got USER_INTERACTION_TAGS %s", self.path.xpath)
                self.user_interact_node = UserInteractNode(name, self.start_position, self.element_visible, self.path, self.block, self.other_block)
                self.user_interact_node.attributes = _attributs
                self.user_node_info.append(self.user_interact_node)
                if self.block:
                    self.block.user_interact_list.append(self.user_interact_node)
                if self.other_block:
                    self.other_block.user_interact_list.append(self.user_interact_node)

       
        #add gap tag
        if self.element_visible:
            path_sections = self.path.xpath.split("/")
            if len(path_sections)>0:
                tag = (path_sections[-1]).split('[')[0]
                if self.block is not None:
                    self.block.gap_tags[tag]+=1
                if self.other_block is not None:
                    self.other_block.gap_tags[tag]+=1

    def endElementNS(self, name, qname):
        name = name[1]
        if name in TAG_IGNORED:
            return
        # 判断是否是other_block 结束
        if self.other_block is not None and self.path.xpath == self.other_block.xpath:
            logging.info("wwj debug self.other_block ends %s", name)
            self.other_block = None
        
        self.path.pop()

        if name in USER_INTERACTION_TAGS:
            self.user_node_info.pop()
            self.user_interact_node = self.user_node_info.top()

        if name in BLOCK_TAGS and self.link_node is None and self.other_block is  None:
            self._end_new_block()

        if name not in FONT_TAGS:
            if name !='a':
                self.before_is_text = False 
                self.after_is_text = False
                self.after_text = ""
        
        if name == 'a':
            self.last_link_obj = self.link_node
            self.link_node = None
            self.after_is_text = True
        
        if name in TITLE_TAGS:
            self.is_title_tag = False  
           
    def endDocument(self):
        self._end_new_block()
    
    def characters(self, content):

        if is_blank(content):
            return
        content = content.strip()
        if self.block.title_text:
            logging.info("wwj debug text_after_title %s title:%s after:%s", self.block.xpath, self.block.title_text, content)
            self.block.text_after_title += content
        if self.is_title_tag:
            self.block.title_text += content 
            logging.info("wwj debug title text %s", content)
                
            if self.other_block is not None:
                self.other_block.title_text += content
        
        #clear white space 
        if self.link_node :
            if not self.link_node.text:
                self.link_node.start_position = self.start_position
            self.link_node.add_text(content)
            self.link_node.before_text = self.before_text
        else:
            self.before_is_text = True
            self.before_text = content
        
        if self.last_link_obj and self.after_is_text:
            self.last_link_obj.after_is_text = True
       
        if self.user_interact_node:
            self.user_interact_node.text += content

        text_node = TextNode(self.start_position, self.element_visible, self.path, self.block, self.other_block, content) 
        logging.info("wwj debug add text_node %s %s %d", 
                    self.block.xpath, text_node.text, text_node.visible)
        self.block.all_text_node_list.append(text_node) if self.element_visible else 1
        self.other_block.all_text_node_list.append(text_node) if (self.element_visible and self.other_block is not None) else 1
                
        if (not self.link_node) and self.element_visible:
                self.block.none_link_text_node_list.append(text_node)
        
        if (self.other_block is not None) and (not self.link_node) and self.element_visible :
            self.other_block.none_link_text_node_list.append(text_node)

        if not self.link_node:
            # handle </br> 2 texts may have same xpath
            if self.path.xpath in self.block.tags_info_dict:
                self.block.tags_info_dict[self.path.xpath].length += get_text_len(content)
                
                    
                if self.other_block is not None:
                    if self.path.xpath not in self.other_block.tags_info_dict:
                        self.other_block.tags_info_dict[self.path.xpath] = text_tag_info()
                    self.other_block.tags_info_dict[self.path.xpath].length += get_text_len(content)
            else:
                #self.block.text_tags.append(self.path.xpath)
                text_tag_info_ = text_tag_info()
                text_tag_info_.start_position = self.start_position
                text_tag_info_.length = get_text_len(content)
                text_tag_info_.text  = content
                self.block.tags_info_dict[self.path.xpath] = text_tag_info_ 
                self.all_text_tags_count +=1 
                self.all_text_nodes_textlen += get_text_len(content)
                
                
                if self.other_block is not None:
                    self.other_block.tags_info_dict[self.path.xpath] = text_tag_info_ 
                
                    
        has_punc = False
        for i in content:
            if i in TEXT_PUNCTUATION:
            #if i in string.punctuation:#only english
                has_punc=True
                break
        if has_punc:
            pass
        if self.link_node and self.link_node.visible:
            self.block.chars_count_in_links += get_text_len(content)
            if self.other_block:
                self.other_block.chars_count_in_links += get_text_len(content)
        
        self.start_position += get_text_len(content)

class PathInfo(object):
    def __init__(self):
        # list of triples (tag name, order, children)
        self._elements = []

    @property
    def dom(self):
        return ".".join(e[0] for e in self._elements)

    @property
    def xpath(self):
        return "/" + "/".join("%s[%d]" % e[:2] for e in self._elements)

    def append(self, tag_name):
        children = self._get_children()
        order = children.get(tag_name, 0) + 1
        children[tag_name] = order

        xpath_part = (tag_name, order, {})
        self._elements.append(xpath_part)

        return self

    def _get_children(self):
        if not self._elements:
            return {}

        return self._elements[-1][2]

    def pop(self):
        self._elements.pop()
        return self
