 # -*- coding: utf-8 -*-
import logging
import re
import numpy
import copy
import copy
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.selector import Selector

from .block import Block, BlockType ,all_grandson_xpath, MainBlock, merge_childrenxpath_by_tag
from .block_identify import BlockIdentifier
from .html_parser import parse
from .page import Page
from utils import get_text_len
from collections import Counter
from .page_charactor import PC
from pty import CHILD
from .block_distance import block_sim_distance, block_structure_distance, block_link_density_distance, block_size_distance

BLACK_LIST={u'版权声明',u'免责声明'}     
#why ul is wrong
TITLE_TAGS = set(['h1','h2', 'h3','h4', 'h5'])
STRUCT_TAGS = set(['ul', 'dl', 'ol','hr','adress', 'script'])
#add p
NO_GAP_TAGS = set(['p','small','big','a', 'img', 'b', 'br', 'em', 'font', 'i', 's', 'span','strong', 'sub', 'sup', 'u', 'tt'])

class LevelTreeBuilder(object):
    
    def __init__(self):
        self.block_identifier = BlockIdentifier()
        self.middle_block_level = 0
        self.mostly_text_level = 0
        self.title_level = 0
        self.level_middle_blocks = dict()
    
    def block_prefilted(self, block, body_style):
        if self.block_identifier.is_invisible(block):
            return True
        if self.block_identifier.is_invalid_style(block, body_style):
            return True
        if self.block_identifier.is_issued_block(block):
            return True
        
    def build_level_elements(self, block_info):
        self.level_elements={}
        self.body_style = self.get_body_style()
        self.all_text_nodes_textlen = 0
        self.all_text_tags_count = 0
        self.all_text_len = 0
        
        for level in reversed(xrange(block_info.levels)):
            for block in self.block_info.level_elements[level]:
                if level not in self.level_elements:
                    self.level_elements[level]=[]
                # / has no webkit_style
                if block.webkit_style:
                    logging.info("wwj debug original elements %d %s %s len:%d width:%d height:%d",
                             level, block.xpath, block.text, block.all_text_len(), block.webkit_style.width,
                            block.webkit_style.height)
                
                self.level_elements[level].append(block)
                if block.visible:
                    self.all_text_nodes_textlen += block.text_nodes_textlen()
                    self.all_text_tags_count += len(block.all_text_node_list)
                    self.all_text_len += block.all_text_len()
        logging.info("[build_level_elements] Done,  ALL_TEXT len %d, all text tags count %d",self.all_text_len, 
                         self.all_text_tags_count)

    def build_level_tree(self, url, html_body):
        #page = Page(url, response.headers)
        page = Page(url, "")
        #phantomjs  spider   utf8
        #print "hihihihihihi", html_body
        body="<html><body><div>bb</div><p>p1</p><p><div>p2</div>hellokitty</p><div>2</div><ul>hello</ul></body>hihihi</html> "
        self.block_maker = parse(page, html_body, '', encoding='utf8')
        self.block_maker.block_info.build_level_nodes()

        self.block_info = self.block_maker.block_info
        self.build_level_elements(self.block_info)
        self.block_levels = self.block_info.levels
        print "----------------------before merge block"
        self.merge_block()
    
    def merge_block(self):
        lower_level = None
        set_lower_blocktype = False 
        check_h1_tag = False
        check_h2_tag = False
        check_h3_tag = False
        
        if self.block_maker.h1_tag_count>0:
            check_h1_tag = True
        if self.block_maker.h2_tag_count>0:
            check_h2_tag = True
        if self.block_maker.h3_tag_count>0:
            check_h3_tag = True


        for level in reversed(xrange(self.block_levels)):
            level_text_nodes_textlen = 0
            level_textlen = 0
            
            middle_block = self.get_level_middle_block(level)
            if middle_block is not None:
                logging.info("wwj debug get level middle block %d %s %s", 
                             level, middle_block.xpath, middle_block.text)
            self.level_middle_blocks[level] = middle_block
            if middle_block is not None :
                if not self.middle_block_level:
                    self.middle_block_level = level
                    logging.info("wwj debug first get max block level %d %s %s", level, middle_block.xpath, middle_block.text)
            logging.info("wwj debug get max block level %d %s ", level, middle_block)

         
            for block in self.level_elements[level]:    
                if not block.visible:
                    continue
                logging.info("wwj debug tmp level block:%d %s %s", level, block.xpath, block.text) 
                #set title_level
                if not self.title_level and check_h1_tag and block.has_title('h1'):
                    self.title_level = level
                elif  not self.title_level and not check_h1_tag and check_h2_tag and block.has_title('h2'):
                    self.title_level = level
                elif not self.title_level and not check_h1_tag and not check_h2_tag and block.has_title('h3'):
                    self.title_level = level

                level_textlen += block.all_text_len()
                level_text_nodes_textlen += block.text_nodes_textlen()
               
               
            if not self.mostly_text_level and \
                level_text_nodes_textlen >= 0.8 *self.all_text_nodes_textlen and \
                level_textlen > 0.8*self.all_text_len:
                if middle_block:
                    logging.info("Got almost text level:%d all_textlen:%d %d textnode_textlen:%d %d %d %d max-block:%s", 
                            level, level_textlen, self.all_text_len, 
                            level_text_nodes_textlen, self.all_text_nodes_textlen,
                            level_text_nodes_textlen >= 0.8 *self.all_text_nodes_textlen, 
                            level_textlen>0.8*self.all_text_len, middle_block.text,
                            )
                else:
                    logging.info("Got almost text level:%d all_textlen:%d %d textnode_textlen:%d %d %d %d max-block:None", 
                            level, level_textlen, self.all_text_len, 
                            level_text_nodes_textlen, self.all_text_nodes_textlen,
                            level_text_nodes_textlen >= 0.8 *self.all_text_nodes_textlen, 
                            level_textlen>0.8*self.all_text_len)
                if not self.mostly_text_level:
                    logging.info("wwj debug got mostly_text_level %d", level)
                    self.mostly_text_level = level
            # get block_type 
            print "=========================", self.middle_block_level ,self.mostly_text_level
            if self.middle_block_level or self.mostly_text_level:
                _level = max(self.middle_block_level, self.mostly_text_level)+1
                lower_level = min(self.block_info.levels-1, _level)
                if lower_level and not set_lower_blocktype:
                    set_lower_blocktype = True
                    # 将本层的other block的特征添加到对应的block上
                    self.add_other_block_charactor(lower_level)
                    for block in self.level_elements[lower_level]:
                        self.block_identifier.get_block_type(block, self.all_text_len, self.body_style)
                        for link_node in block.all_link_node_list:
                            if block.block_type!= BlockType.UNKNOWN or link_node.father_block_type is None:
                                link_node.father_block_type = block.block_type
                                link_node.filter_reason = block.filter_reason
                        # 如果有多个h1, 则不加权 
                        if block.block_type == BlockType.TITLE_H1 and self.block_maker.h1_tag_count ==1 :
                            block.main_block_score = 5
                        elif block.block_type != BlockType.UNKNOWN:
                            block.main_block_score = -2
                        elif block.block_type == BlockType.UNKNOWN:
                            block.main_block_score += 0
                        logging.info("wwj debug first got block type level lower:%d %s %s %d %s",
                                lower_level, block.xpath, block.block_type.name, block.main_block_score, block.text)
                for block in self.level_elements[level]:
                    # 将本层的other block的特征添加到对应的block上
                    self.add_other_block_charactor(level)
                    print "===========before get_block_type", block.xpath
                    self.block_identifier.get_block_type(block, self.all_text_len, self.body_style)
                    for link_node in block.all_link_node_list:
                            if block.block_type!= BlockType.UNKNOWN or link_node.father_block_type is None:
                                link_node.father_block_type = block.block_type
                                link_node.filter_reason = block.filter_reason
                    if block.block_type == BlockType.TITLE_H1 and self.block_maker.h1_tag_count ==1 :
                        block.main_block_score = 5
                    elif block.block_type != BlockType.UNKNOWN:
                        block.main_block_score = -2
                    elif block.block_type == BlockType.UNKNOWN:
                        block.main_block_score += 0
                    logging.info("wwj debug first got block type level:%d %s %s %d %s",
                            level, block.xpath, block.block_type.name, block.main_block_score, block.text) 
            
            # 如果页面有标题，则需要合并到标题层
            if check_h1_tag or check_h2_tag or check_h3_tag:
                if self.mostly_text_level and self.middle_block_level and self.title_level:
                    return self.level_middle_blocks[self.middle_block_level]
            else:
                if self.mostly_text_level and self.middle_block_level:
                    return self.level_middle_blocks[self.middle_block_level]
            self.merge_to_father(level)
        #
        if not self.mostly_text_level:
            self.mostly_text_level = self.block_levels -1
        if not self.middle_block_level:
            self.mostly_block_level = self.block_levels -1
    
    def add_other_block_charactor(self, level):
        for block in self.level_elements[level]:
            for other_block in block.other_blocks:
                self.block_identifier.get_block_type(other_block, self.all_text_len, self.body_style)
                for link_node in other_block.all_link_node_list:
                    if block.block_type!= BlockType.UNKNOWN or link_node.father_block_type is None:
                        link_node.father_block_type = other_block.block_type
                        link_node.filter_reason = other_block.filter_reason
                if other_block.block_type == BlockType.TITLE_H1 and self.block_maker.h1_tag_count ==1 :
                    other_block.main_block_score = 5
                elif other_block.block_type != BlockType.UNKNOWN:
                    other_block.main_block_score = -2
                elif  other_block.block_type == BlockType.UNKNOWN:
                    other_block.main_block_score = 0
                block.main_block_score += float(0.1 * other_block.main_block_score)
                logging.info("wwj debug add main_block_score to father11 %d %s %s other_block:%f block:%f other:%s block:%s",
                            level, other_block.xpath, block.xpath, other_block.main_block_score, block.main_block_score, other_block.text, block.text)
    
    def merge_to_father(self, level):
        for block in self.level_elements[level]:
            self.add_child_block_to_father(block)

    def get_body_style(self):
        self.body_style = self.block_info.level_elements[1][0].webkit_style
        return self.body_style
        
    def add_child_block_to_father(self, block):
        father = block.father
        if father is None:
            pass
        else:

            if father.has_title_tag:
                father.text_after_title += block.text
                logging.info("wwj debug father text_after_title father:%s child:%s text:%s all_text_after_title:%s" , 
                        father.xpath, block.xpath, block.text, father.text_after_title)
            if block.has_title_tag:
                #碰到一个新的title，text_after_title 置空，只需要统计最后一个title的text_after_title 即可 
                father.has_title_tag = 1
                father.text_after_title = block.text_after_title
                logging.info("wwj debug father text_after_title1111 father:%s child:%s text:%s text_after_title:%s", 
                        father.xpath, block.xpath, block.text, block.text_after_title)
            #*0.1 father的层次越高，child score 的影响相对越少

            # 如果是右边栏，则父节点的score 为正，（如果父节点也是右边栏的话，在下一层会判断出来）
            if block.block_type == BlockType.RIGHT_OR_LEFT_SIDE:
                father.main_block_score += -1*block.main_block_score
            else:
                father.main_block_score += float(0.1*block.main_block_score)
            
            father.input_node_list += block.input_node_list
            father.user_interact_list += block.user_interact_list
            father.all_link_node_list += block.all_link_node_list
            father.all_text_node_list += block.all_text_node_list
            father.none_link_text_node_list += block.none_link_text_node_list
            father.img_link_node_list += block.img_link_node_list
            father.onclick_link_node_list += block.onclick_link_node_list
            father.onload_link_node_list += block.onload_link_node_list
            father.none_img_link_node_list += block.onload_link_node_list
            father.image_node_list += block.image_node_list
 
            father.all_tags += block.all_tags
            father.gap_tags += block.gap_tags
            
            father.chars_count_in_links += block.chars_count_in_links
            father.tags_info_dict.update(block.tags_info_dict)
            if block.main_block_score!=0:
                logging.info("wwj debug add main_block_score to father %s %s %f %f %s %s", 
                        block.xpath, father.xpath, block.main_block_score, father.main_block_score,
                        block.text, father.text)
            logging.info("wwj debug add child TO FATHER:%s SELF:%s self.links:%d father:links:%d %s score-child %d score-father:%f", 
                                  father.xpath,block.xpath, len(block.all_link_node_list), len(father.all_link_node_list), block.text, block.main_block_score, father.main_block_score)
    
    def get_level_middle_block(self, level):
        body_style = self.get_body_style()
        max_block = None
        top = 525
        bottom = 825
        # not in the middle, some page in the left
        left = 520
        right= 620
        if body_style is not None:
            if body_style.height < 900:
                top = body_style.height*1/3
                bottom = body_style.height*1/5+top
        #middle 600 720, height=200 width=150
        all_blocks = []
              
        for block in self.level_elements[level]:
            if self.block_identifier.is_invisible(block) or self.block_identifier.is_invalid_style(block, self.body_style):
                continue
            all_blocks.append(block)
        i = 0
        can_blocks= []
        regex_pattern = re.compile(r"ul\[\d+\]/li\[\d+\]|dl\[\d+\]|table\[\d+\]/tbody\[\d+\]")
        for i, block in enumerate(all_blocks):
            if not block.contains_text():
                continue
            #filter ul/li TODO add more,todo,is wrong
            if re.findall(regex_pattern, block.xpath):
                logging.info("wwj debug find_middle_block regex %s",block.xpath)
                continue
            _father = block.father
            if _father is not None and _father.webkit_style is not None:
                if _father.webkit_style.height == block.webkit_style.height and _father.webkit_style.width == block.webkit_style.width:
                    continue
                
            if block.webkit_style.left <=left and  (block.webkit_style.left+block.webkit_style.width)> right \
                   and block.webkit_style.height > (bottom-top) and block.webkit_style.top <900:
                can_blocks.append(block)
                logging.info("wwj debug the block maybe can_blocks level:%d %s webkit_style:top:%d left:%d width:%d height:%d %s, father width:%d height %d", 
                             level, block.xpath, block.webkit_style.top,
                             block.webkit_style.left, block.webkit_style.width,  block.webkit_style.height, block.text, block.father.webkit_style.width, block.father.webkit_style.height)
            else:
                logging.info("wwj debug find_middle_block pos not in middle level:%d %s %s left:%d top:%d heigth:%d width:%d",
                             level, block.xpath, block.text, block.webkit_style.left, block.webkit_style.top,\
                             block.webkit_style.height, block.webkit_style.width)
        if len(can_blocks)==1:
            max_block = can_blocks[0]
            logging.info("wwj debug get_level_max_block can_blocks == 1 level:%d %s webkit_style: top:%d left:%d width:%d height:%d text:%s %d", 
                       level,max_block.xpath, max_block.webkit_style.top, max_block.webkit_style.left, max_block.webkit_style.width, max_block.webkit_style.height,
                         max_block.text, len(max_block.all_text_node_list))
        if len(can_blocks) >1:
            top_count = 0
            bottom_count = 0
            cover_count = 0
            cover_blocks = []
            for block in can_blocks:
                if (block.webkit_style.top+block.webkit_style.height)>= bottom and block.webkit_style.top <=top :
                    max_block = block
                    break
                if block.webkit_style.top >top :
                    bottom_count += 1             
                if (block.webkit_style.top+block.webkit_style.height)< bottom:
                    top_count += 1
                if (block.webkit_style.top+block.webkit_style.height)< bottom and block.webkit_style.top <top and (block.webkit_style.top+block.webkit_style.height)>top:
                    cover_count += 1
                    cover_blocks.append(block)
                if  (block.webkit_style.top+block.webkit_style.height)> bottom and block.webkit_style.top >top and block.webkit_style.top<bottom:
                    cover_count += 1
                    cover_blocks.append(block)
            
        
            #all in the top or bottom, pick the nearest one to middle block
            if bottom_count == len(can_blocks):
                max_block = can_blocks[0]
                logging.info("wwj debug get_level_max_block level all in the bottom:%d %s webkit_style: top:%d left:%d width:%d height:%d text:%s %d", 
                       level,max_block.xpath, max_block.webkit_style.top, max_block.webkit_style.left, max_block.webkit_style.width, max_block.webkit_style.height,
                         max_block.text, len(max_block.none_link_text_node_list))
            
            if top_count == len(can_blocks):
                max_block = can_blocks[-1]
                logging.info("wwj debug get_level_max_block level all in the top:%d %s webkit_style: top:%d left:%d width:%d height:%d text:%s %d", 
                       level,max_block.xpath, max_block.webkit_style.top, max_block.webkit_style.left, max_block.webkit_style.width, max_block.webkit_style.height,
                         max_block.text, len(max_block.none_link_text_node_list))
            
            #if only 1 block cover middle block
            if cover_count == 1:
                max_block = cover_blocks[0]
                logging.info("wwj debug get_level_max_block level:%d %s webkit_style: top:%d left:%d width:%d height:%d text:%s %d", 
                       level,max_block.xpath, max_block.webkit_style.top, max_block.webkit_style.left, max_block.webkit_style.width, max_block.webkit_style.height,
                         max_block.text, len(max_block.none_link_text_node_list))
        
        '''may be has same struct to brother'''
        #too complicated!
        if max_block:
            before_child = None
            next_child = None
            i = 0
            for i, block in enumerate(all_blocks):
                if block.xpath == max_block.xpath:
                    break
            if i>1:
                before_child = all_blocks[i-1]
            if i<len(all_blocks)-1:
                next_child = all_blocks[i+1]
            if  before_child is not None:
                xpath_list1 = all_grandson_xpath(before_child)
                xpath_list2 = all_grandson_xpath(max_block)

                if xpath_list1 and xpath_list2:
                    _structure_distance1 = block_structure_distance(xpath_list1, xpath_list2)
                    _size_distance1 = block_size_distance(before_child, max_block)
                    _link_density_distance = block_link_density_distance(max_block, before_child)
                    if _structure_distance1 < 0 and _link_density_distance<0.25 and _size_distance1<0.5:
                        logging.info("wwj debug in get max block distance1 %d %s",_structure_distance1, before_child.text )
                        if max_block is None and  self.level_middle_blocks.get(level+1, None):
                            max_block = self.level_middle_blocks[level+1].father
                        else:
                            max_block = None
                        if max_block is None and  self.level_middle_blocks.get(level+1, None):
                            max_block = self.level_middle_blocks[level+1].father
                        return max_block
                    
            if  next_child is not None:
                xpath_list1 = all_grandson_xpath(next_child)
                xpath_list2 = all_grandson_xpath(max_block)
                #logging.info("wwj debug in get max block distance1 next child %s %s",next_child.xpath, next_child.text )
                _structure_distance1 = block_structure_distance(xpath_list1, xpath_list2)
                _size_distance1 = block_size_distance(next_child, max_block)
                _link_density_distance = block_link_density_distance(block, next_child)
                if _structure_distance1<0 and _link_density_distance<0.25 and _size_distance1<0.5:
                    logging.info("wwj debug in get max block distance2 %d %s",_structure_distance1, next_child.text)
                    if max_block is None and  self.level_middle_blocks.get(level+1, None):
                        max_block = self.level_middle_blocks[level+1].father
                    else:
                        max_block = None
                    if max_block is None and  self.level_middle_blocks.get(level+1, None):
                        max_block = self.level_middle_blocks[level+1].father
                    return max_block
        
        if max_block is None and  self.level_middle_blocks.get(level+1) is not None:
            max_block = self.level_middle_blocks[level+1].father
        if max_block is not None:
            if max_block.webkit_style:
                logging.info("wwj debug get_level_max_block got final max_block level:%d %s height:%d text:%s", 
                       level,max_block.xpath,max_block.webkit_style.height,  max_block.text)
            else:
                logging.info("wwj debug get_level_max_block got final max_block level:%d  %s link_objs:%d, text_tags: %d text:%s", 
                       level,max_block.xpath,len(block.all_link_node_list), len(max_block.all_text_node_list),  max_block.text)
        return max_block


    
