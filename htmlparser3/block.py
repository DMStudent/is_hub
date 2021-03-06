# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re

from .utils import normalize_whitespace
from .utils import get_text_len
import logging
import editdistance
from .block_tree import TreeNode
from collections import Counter
from enum import Enum
from twisted.conch.test.test_helper import HEIGHT

TITLE_H1_TAG='h1'

class BlockType(Enum):
    NAV      = 1            # 导航块
    SECONND_NAV = 2         # 二级导航
    CRUMB = 3               # 面包屑
    TITLE_H1 = 4               # 标题
    SECOND_TITLE = 5        # 二级标题
    HEADER = 6
    ANNOUNCE = 7            # 声明块
    COPYRIGHT = 8           # 版权块
    ADS = 9                 # 广告快 
    FRIENDLY_LINK = 10       # 友情链接
    LOGIN = 11         # 登陆块
    SEARCH = 12             # 搜索块
    TOPIC_SHARED = 13       # 分享块
    DIGEST = 14             # 摘要块
    HOT_RECOMMEND = 15      # 推荐块 
    RELEVENCE_LINK = 16     # 相关链接块
    NEXTPAGE = 17           # 下一页 
    RIGHT_OR_LEFT_SIDE = 18         # 侧边栏
    BANNER = 19
    BOTTOM = 20 
    USER_INPUT = 21
    BBS_USER_INFO = 22
    UNKNOWN = 23
    FILTERED = 24
     
class WebkitStyle(object):
    def __init__(self, top, left, width, height):
        self.top = top
        self.left = left
        self.width = width
        self.height = height
    @classmethod
    def create_webkitstyle_from_str(cls, str):
        #top:2479px;left:231px;width:650;height:35;
        items = str.split(";")
        top = 0
        left = 0
        height = 0
        width = 0
        for item in items:
            _item = item.split(":")
            if _item[0]== "top":
                
                top = round(float(_item[1].split('px')[0]))
            if _item[0] == "left":
                left = round(float(_item[1].split('px')[0]))
            if _item[0] == "height":
                height = round(float(_item[1]))
            if _item[0] == "width":
                width = round(float(_item[1]))
        return cls(top, left, width, height)            
str="top:2479px;left:231px;width:650;height:35;"
style = WebkitStyle.create_webkitstyle_from_str(str)

class text_tag_info(object):
    def __init__(self):
        self.start_postion = 0;
        self.length = 0
        self.text = ""
    
class Block(TreeNode):
    """Object representing one block of text in HTML."""
    def __init__(self, path):
        super(Block, self).__init__()
        self.path = path
        self.xpath = path.xpath
        self.dom = path.dom
        self.visible = True
        self.chars_count_in_links = 0
        self.webkit_style = None
        self.class_attr = None
        
        self.all_text_node_list = []
        self.none_link_text_node_list = []
        
        
        self.all_link_node_list = []
        self.img_link_node_list = []
        self.onclick_link_node_list = []
        self.onload_link_node_list = []
        self.none_img_link_node_list = []
        
        
        self.image_node_list = []
        self.input_node_list= []
        self.user_interact_list = []
       
  
        self.all_tags = []
        self.gap_tags = Counter()
        #all link tags
        
        self.title_text = ""
        self.has_title_tag = False
        self.text_after_title = ""
        
        self.tags_info_dict= {}
        self.other_blocks = [] 
        self.other_sub_blocks = []
        self.start_position = None
        self.children_xpath = []
        
        self.father = None
        self.firstchild = None
        self.nextsibling = None
        
        self.main_block_score = 0.0
        self.block_type =  BlockType.UNKNOWN
        self.attributes = {}
        self.filter_reason = ""
    
    def has_title(self, title):
        if not self.gap_tags or not title:
            return False
        if title in self.gap_tags:
            return True
        return False
    
    
    def none_image_link_node_list_withtext(self):
        _list= []
        for link_node in len(self.none_img_link_node_list):
            if not link_node.visible:
                continue
            if not link_node.text:
                continue
            _list.append(link_node)
        return _list
              
    @property
    def left_brother(self):
        _brother = self.father.firstchild
        if _brother == self:
            return None
        _last_brother = None
        while _brother is not None:
            _last_brother = _brother
            _brother = _brother.nextsibling
            if _brother == self:
                logging.info("wwj debug left_brother is %s-------------%s", self.text, _last_brother.text)
                return _last_brother
                
    @property 
    def all_children_sort_by_postion(self):
        
        #leaf code, has no children,return self
        if self.firstchild is None and  not self.other_sub_blocks:
            _list = []
            _list.append(self)
            return _list
        
        children_list = []
        child = self.firstchild
        while child is not None:
                #logging.info("wwj debug child block xpath:%s text:%s", child.xpath, child.text)
                if child.visible:
                    children_list.append(child)
                child = child.nextsibling 
                
        for block in self.other_sub_blocks:
            if block is not None and block.visible:
                #logging.info("wwj debug other_sub_blocks %s %s", block.xpath, block.text)
                children_list.append(block)  
        children_list.sort(key = lambda x: x.start_position)      
        return children_list
    
    @property 
    def new_all_children_sort_by_postion(self):
        # filter block no text and image
        #leaf code, has no children,return self
        if self.firstchild is None and  not self.other_blocks:
            _list = []
            _list.append(self)
            return _list
        
        children_list = []
        child = self.firstchild
        while child is not None:
                if child.text == "" and len(child.img_link_node_list)==0:
                    child = child.nextsibling
                    continue
                #logging.info("wwj debug child block xpath:%s text:%s", child.xpath, child.text)
                if child.visible:
                    children_list.append(child)
                child = child.nextsibling 
                
        for block in self.other_blocks:
            if block.text == "" and len(block.img_link_node_list) ==0:
                continue
            if block is not None and block.visible:
                #logging.info("wwj debug other_blocks %s %s", block.xpath, block.text)
                children_list.append(block)  
        children_list.sort(key = lambda x: x.start_position)      
        return children_list
    
    @property
    #only child has link_tag 
    def all_children_xpath_merged(self):
        all_children = self.all_children_sort_by_postion
        '''ul/li,dl, table/tbody'''
        regex_pattern = re.compile(r"ul\[\d+\]/li\[\d+\]|dl\[\d+\]|table\[\d+\]/tbody\[\d+\]")
        block_path_dict = {}
        last_child = None
        last_key= None
        if all_children:
         
            for child in all_children:
                #if not child.contains_text():
                #    continue
                #if len(child.link_tag)== 0:
                #    continue
                logging.info("wwj debug in all_children_merged first %s %d", child.xpath,len(all_children))
                line = re.findall(regex_pattern, child.xpath)
                if line:
                    pos = child.xpath.find(line[0])
                    key = child.xpath[0:pos+len(line[0])]
                    if key not in block_path_dict:
                        logging.info("wwj debug in all_children_merged matched patten key %s %s %s",
                                     key, last_child, block_path_dict)
                        block_path_dict[key] = []
                        self.children_xpath.append(block_path_dict[key])
                    else:
                        if key != last_key:
                            logging.info("wwj debug in all_children_merged matched patten key--------%s ",key)
                            self.block_path_dict[key] = []
                            self.children_xpath.append(block_path_dict[key])
                    block_path_dict[key].append(child.xpath)
                    last_key = key
                    last_child = child
                    logging.info("wwj debug last_child %s %s", last_child, block_path_dict)
                else:
                    logging.info("wwj debug in all_children_merged not matched patten %s %s %s", 
                                 child.xpath, child.text, child.all_children)
                    tmp_lst = []
                    _children = child.all_children
                    if _children:
                        for _child in _children:
                            if not _child.contains_text():
                                continue
                            grandchild = all_grandson(_child)
                            if grandchild :
                                for _grand in grandchild:
                                    if not _grand.contains_text():
                                        continue
                                    tmp_lst.append(_grand.xpath)
                    #if len(tmp_lst)>1:
                    self.children_xpath.append(tmp_lst)
        for xpath_lst  in self.children_xpath:
            logging.info("wwj debug finished all_children_merged len:%d %s", len(xpath_lst),xpath_lst)
        return self.children_xpath
                    
    @property 
    def all_children(self):
        children_list = []
        child = self.firstchild
        while child is not None:
                if child.visible:
                    children_list.append(child)
                child = child.nextsibling 
        return children_list
                
    def text_tag_distance(self):
        distance = 0
        self.sorted_tags_info_dict={}
        tmp_list=[]
        for key, value in sorted(self.tags_info_dict.iteritems(), key=lambda (k,v): (v.start_postion,k)):
            self.sorted_tags_info_dict[key] = value
            tmp_list.append([key, value])
            #logging.info("wwj debug sorted1 text_tags %s %d %d", key, value.start_postion,value.length)
            
        for i in xrange(len(tmp_list)-1):
            _distance = self.sorted_tags_info_dict.get(tmp_list[i+1][0]).start_postion - \
                self.sorted_tags_info_dict.get(tmp_list[i][0]).start_postion - self.sorted_tags_info_dict.get(tmp_list[i][0]).length
            
            #logging.info("wwj debug distance %d text:%s text:%s %s %s",_distance, self.sorted_tags_info_dict.get(tmp_list[i+1][0]).text,
            #             self.sorted_tags_info_dict.get(tmp_list[i][0]).text, tmp_list[i+1][0], tmp_list[i][0])
            distance += _distance
        return distance
               
    @property
    def is_heading(self):
        return bool(re.search(r"\bh\d\b", self.path.dom_path))

    @property
    def is_boilerplate(self):
        return self.class_type != "good"

    @property
    def text(self):  #all text
        text = ""
        self.all_text_node_list.sort(key = lambda x: x.start_position)  
        for node in self.all_text_node_list:
            if not node.visible:
                continue
            text += node.text
        return normalize_whitespace(text.strip())
    
    @property
    def nolink_text(self):
        text=""
        self.none_link_text_node_list.sort(key = lambda x: x.start_position)
        for node in self.none_link_text_node_list:
            if not node.visible:
                continue
            text += node.text
        return normalize_whitespace(text.strip())
    @property
    def long_text_node(self):  #block中最长的文本节点
        if not self.all_text_node_list:
            return None
        longest_text_node = max(self.all_text_node_list, key=lambda(item):get_text_len(item.text))
        return longest_text_node
        
    def all_text_len(self):
        return get_text_len(self.text)
        
    def __len__(self):
        return get_text_len(self.text)

    @property
    def words_count(self):
        return get_text_len(self.text)

    def contains_text(self):
        return bool(self.all_text_node_list)

    def text_nodes_textlen(self):
        text = ""
        for node in self.none_link_text_node_list: 
            if not node.visible:
                continue
            text += node.text
        return get_text_len(text)
    
    @property
    def text_nodes_text(self):
        text = "".join(self.nodes_text)
        #return text.strip()
        return normalize_whitespace(text.strip())
        
    

    def stopwords_count(self, stopwords):
        count = 0

        for word in self.text.split():
            if word.lower() in stopwords:
                count += 1

        return count

    def stopwords_density(self, stopwords):
        words_count = self.words_count
        if words_count == 0:
            return 0

        return self.stopwords_count(stopwords) / words_count

    def links_density(self):
        text_length = get_text_len(self.text)
        if text_length == 0 :
            return 0

        return self.chars_count_in_links / (text_length)
    
    def link_tags_density(self):
        if len(self.none_link_text_node_list)==0 and len(self.all_text_node_list)==0:
            return 0
        return len(self.all_link_node_list)*1.000/(len(self.all_text_node_list))
    
    def tag_density(self):
        text_length = self.all_text_len()
        line_number = None
        tag_len = len(self.all_tags)
        if text_length<50:
            line_number = 1
        else:
            line_number = text_length/50
        if text_length ==0:
            return 0
        return tag_len*1.000/line_number
    

def all_grandson(block):
    children = block.all_children
    grandchilds = []
    _lst = []
    _lst.append(block)
    if not children:
        return _lst
    for child in children:
        _lst += all_grandson(child)
        grandchilds+=_lst
    return grandchilds

def all_grandson_xpath(block):
    
    children = block.all_children
    grandchild_xpath = []
    if not children:
        grandchild_xpath.append(block.xpath)
        return grandchild_xpath
    for child in children:
        _lst = all_grandson_xpath(child)
        grandchild_xpath+=_lst
    return grandchild_xpath

class MainBlock(object):
    def __init__(self):
        self.blocks = []
        self.useful_link_nodes = []
        self.block_type = None
        self.visible = True
        self.main_block_score = 0
    
    def contains_text(self):
        return bool(self.all_text_node_list)
    
    @property
    def attributes(self):
        if not self.blocks:
            return None
        return self.blocks[0].attributes
    @property
    def xpath(self):
        if not self.blocks:
            return None
        return self.blocks[0].xpath
    
    @property
    def path(self):
        if not self.blocks:
            return None
        return self.blocks[0].path
    @property
    def gap_tags(self):
        gap_tags = Counter()
        for block in self.blocks:
            gap_tags+= block.gap_tags
        return gap_tags
            
    @property
    def webkit_style(self):
        webkit_style = WebkitStyle
        webkit_style.height = self.height
        webkit_style.width = self.width
        webkit_style.top = self.top
        webkit_style.left = self.left
        return webkit_style
        
    @property    
    def height(self):
        if not self.blocks:
            return
        top_block = min(self.blocks, key= lambda item:item.webkit_style.top)
        bottom_block = max(self.blocks, key= lambda item:(item.webkit_style.top+item.webkit_style.height))
        top_pos = top_block.webkit_style.top
        bottom_pos = bottom_block.webkit_style.top +bottom_block.webkit_style.height
        return bottom_pos-top_pos
    
    @property
    def width(self):
        if not self.blocks:
            return
        left_block = min(self.blocks, key= lambda item:item.webkit_style.left)
        right_block =  max(self.blocks, key= lambda item:(item.webkit_style.left+item.webkit_style.width))
        left_pos = left_block.webkit_style.left
        right_pos = right_block.webkit_style.left + right_block.webkit_style.width
        return right_pos-left_pos
    
    @property
    def left(self):
        if not self.blocks:
            return
        left_block = min(self.blocks, key= lambda item:item.webkit_style.left)
        return left_block.webkit_style.left
    
    @property
    def top(self):
        if not self.blocks:
            return
        top_block = min(self.blocks, key= lambda item:item.webkit_style.top)
        return top_block.webkit_style.top
    
    def set_useful_links(self, lst):
        self.useful_link_nodes = lst
    
    @property
    def start_position(self):
        if not self.blocks:
            return
        self.blocks.sort(key = lambda x: x.start_position)

        return self.blocks[0].start_position
    
    @property
    def useful_chars_count_in_links(self):
        count = 0
        if not self.useful_link_nodes:
            return count
        for link_obj in self.useful_link_nodes:
            logging.info("wwj debug useful link_obj text %s %d", 
                         link_obj.text, link_obj.text_len)
            count += link_obj.text_len
        return count
    
    @property
    def chars_count_in_links(self):
        count = 0
        for block in self.blocks:
            count += block.chars_count_in_links
        return count
    
    
    @property
    def all_link_node_list(self):
        _all_link_node_list = []
        for block in self.blocks:
            _all_link_node_list += block.all_link_node_list
        return _all_link_node_list
    
    @property
    def image_node_list(self):
        _image_node_list = []
        for block in self.blocks:
            _image_node_list += block.image_node_list
        return _image_node_list
    
    
    
    @property 
    def all_text_node_list(self):
        _all_text_node_list= []
        for block in self.blocks:
            _all_text_node_list += block.all_text_node_list
        return _all_text_node_list
    
    @property 
    def user_interact_list(self):
        _user_interact_list= []
        for block in self.blocks:
            _user_interact_list += block.user_interact_list
        return _user_interact_list
    
    @property 
    def input_node_list(self):
        _input_node_list= []
        for block in self.blocks:
            _input_node_list += block.input_node_list
        return _input_node_list
    
    @property 
    def none_link_text_node_list(self):
        _none_link_text_node_list= []
        for block in self.blocks:
            _none_link_text_node_list += block.none_link_text_node_list
        return _none_link_text_node_list
    @property
    def text(self):
        text = ""
        if len(self.blocks) == 0:
            return text
        for block in self.blocks:
            if block is not None:
                text += block.text
        return text
    
    @property
    def nolink_text(self):
        text=""
        self.none_link_text_node_list.sort(key = lambda x: x.start_position)
        for node in self.none_link_text_node_list:
            if not node.visible:
                continue
            text += node.text
        return normalize_whitespace(text.strip())
    
    def all_text_len(self):
        return get_text_len(self.text)
    
    def nolink_text_len(self):
        return get_text_len(self.nolink_text)
        
    def __len__(self):
        return get_text_len(self.text)

    @property
    def words_count(self):
        return get_text_len(self.text)
    
    @property
    def long_text_node(self):  #blockÖÐm~\~@m~U0m~Z~Dm~V~Gm~\0m~J~Bm~Bm
        if not self.all_text_node_list:
            return None
        longest_text_node = max(self.all_text_node_list, key=lambda(item):get_text_len(item.text))
        return longest_text_node
    
    def links_density(self):
        text_length = get_text_len(self.text)
        if text_length == 0 :
            return 0

        return self.chars_count_in_links / (text_length)
    
    
    def useful_links_density(self):
        text_length = get_text_len(self.text)
        if text_length == 0 :
            return 0
        logging.info("wwj debug useful_chars_count_in_links: %d ",
                     self.useful_chars_count_in_links)
        return self.useful_chars_count_in_links/(text_length)
        
    def link_tags_density(self):
        if len(self.all_text_node_list)==0:
            return 0
        return len(self.all_link_node_list)*1.000/(len(self.all_text_node_list))
    
    
    def tag_density(self):
        text_length = self.all_text_len()
        line_number = None
        tag_len = len(self.all_tags)
        if text_length<50:
            line_number = 1
        else:
            line_number = text_length/50
        if text_length ==0:
            return 0
        logging.info("wwj debug tag_density %s tags:%d line:%f density:%f %s",
                     self.xpath, tag_len, line_number, tag_len*1.000/line_number, self.text)
        return tag_len*1.000/line_number
        
    @property
    def all_children_xpath_merged(self):
        children_xpath = []
        for block in self.blocks:
            if len (block.link_tags) ==0:
                continue
            _lst = all_grandson_xpath(block)
            #logging.info("wwj debug main block children %s", _lst)
            children_xpath.append(_lst)
        return children_xpath
    

def merge_childrenxpath_by_tag(children_xpath):
    if not children_xpath:
        return children_xpath
    regex_pattern = re.compile(r"ul\[\d+\]/li\[\d+\]")
    mereged_children_xpath = []
    for child_xpath_lst in children_xpath:
        _if_list = True
        _new_xpath_lst = []
        for child_xpath in child_xpath_lst:
            match_str = re.findall(regex_pattern, child_xpath)
            if not match_str:
                _if_list = False
                break    
        if _if_list:
            pos = child_xpath_lst[0].find(match_str[0])
            xpath = child_xpath_lst[0][0:pos+len(match_str[0])]
            _new_xpath_lst.append(xpath)
            mereged_children_xpath.append(_new_xpath_lst)
        else:
            mereged_children_xpath.append(child_xpath_lst)
    return mereged_children_xpath
        
    
                
