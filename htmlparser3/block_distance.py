 # -*- coding: utf-8 -*-
import logging
import re
import numpy
import copy
import copy
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.selector import Selector

from block import Block, all_grandson_xpath, MainBlock, merge_childrenxpath_by_tag
from block_identify import BlockIdentifier
from html_parser import parse
from .page import Page
from .utils import get_text_len
from collections import Counter
from page_charactor import PC
from pty import CHILD

BLACK_LIST={u'版权声明',u'免责声明'}     
#why ul is wrong
TITLE_TAGS = set(['h1','h2', 'h3','h4', 'h5', 'h6'])
STRUCT_TAGS = set(['ul', 'dl', 'ol','hr','adress', 'script'])
#add p
NO_GAP_TAGS = set(['p','small','big','a', 'img', 'b', 'br', 'em', 'font', 'i', 's', 'span','strong', 'sub', 'sup', 'u', 'tt'])



def block_sim_distance(current_block, last_block):
    current_gap_tags = copy.deepcopy(current_block.gap_tags)
    last_gap_tags = copy.deepcopy(last_block.gap_tags)
    gap_between_blocks =set() 
    gap_more = set()
    current_gap_tags.subtract(last_gap_tags)
    
    num_patten = re.compile(r"\[\d\]")
    current_block_xpath_without_num = re.sub(num_patten,"", current_block.xpath)
    last_block_xpath_without_num = re.sub(num_patten,"", last_block.xpath)
    #regex_pattern = re.compile(r"ul\[\d+\]/li\[\d+\]")
    regex_pattern = re.compile(r"ul/li|dl")
    result1 = re.search(regex_pattern, current_block_xpath_without_num)
    result2 = re.search(regex_pattern, last_block_xpath_without_num)
    #TODO return when first met
    if result1 and result2 and result1.group()== result2.group() and result1.start()== result2.start():
        logging.info("block has strong list tag, merge %s %s", current_block.xpath, last_block.xpath)
        return -100
    
    
    for tag in current_gap_tags:
        if current_gap_tags[tag] <0 :
            gap_between_blocks.add(tag)
        if current_gap_tags[tag] >0:
            gap_more.add(tag)
        
        if gap_more&TITLE_TAGS :
            logging.info("current block has title should separate current_block:xpath:%s current_block.text:%s last_block.xpath:%s, last_block.text:%s gap_more:%s", 
                    current_block.xpath, current_block.text, last_block.xpath, last_block.text, gap_more)
            return 100

        if gap_between_blocks&TITLE_TAGS and last_block.has_title_tag and get_text_len(last_block.text_after_title)<5:
            logging.info("last block has title, current block should merge to last, text_after_title %s last_block:%s %s gaps:%s last:%s", 
                         last_block.text_after_title, last_block.xpath, last_block.text, gap_between_blocks&TITLE_TAGS, last_gap_tags)
            return -100
            
    force_seprate_gaps = gap_between_blocks & STRUCT_TAGS
   

    if force_seprate_gaps:
        logging.info("wwj debug force_seprate_gaps %s", force_seprate_gaps)
        return 100
    
    if  ((not gap_between_blocks) or gap_between_blocks.issubset(NO_GAP_TAGS)) and \
        ((not gap_more) or gap_more.issubset((NO_GAP_TAGS))):
        logging.info("wwj debug there is only no_gap_tag %s between two blocks block1:%s %s --------block2:%s %s", 
                     gap_between_blocks, current_block.xpath, current_block.text, last_block.xpath, last_block.text)
        return -100 
    logging.info("wwj debug there is more than  no_gap_tag %s  %s, between two blocks block1:%s %s --------block2: %s %s", 
                     gap_between_blocks, gap_more, current_block.xpath, current_block.text, last_block.xpath, last_block.text)
    max_tag_density = max(current_block.tag_density(), last_block.tag_density())
    if max_tag_density==0:
        return 0
    else:
        logging.info("wwj debug block_sim_distance gap_between_blocks:%s distance:%f current all_tags:%s last_all_tags:%s  current:%f last:%f current:%s------------last:%s ",
                 gap_between_blocks,
                 abs(current_block.tag_density()-last_block.tag_density())/max_tag_density, 
                 current_block.all_tags, last_block.all_tags,
                 current_block.tag_density(), last_block.tag_density(),
                 current_block.text, last_block.text)
        return abs(current_block.tag_density()-last_block.tag_density())/max_tag_density
    #return (abs(block1.links_density()-block2.links_density()))
def block_structure_distance(children_xpath1, children_xpath2):
    patten = re.compile(r"\[\d+\]")
    children1_dom_lst = []
    children2_dom_lst = []
    if not children_xpath1 or not children_xpath2:
        return 100
    for xpath in children_xpath1:
        dom_path = re.sub(patten,"", xpath)
        children1_dom_lst.append(dom_path)
    for xpath in children_xpath2:
        dom_path = re.sub(patten,"", xpath)
        children2_dom_lst.append(dom_path)        
    if children1_dom_lst == children2_dom_lst:
        logging.info("wwj debug in block_structure_distance has same structure %s----%s", 
                     children_xpath1, children_xpath2)
        return -100
    logging.info("wwj debug in block_structure_distance has different structure %s----%s", 
                     children_xpath1, children_xpath2)
    return 100

def block_link_density_distance(block1, block2):
    return (abs(block1.links_density()-block2.links_density()))

def block_size_distance(block1, block2):
    if block1.webkit_style.height ==0  or block2.webkit_style.height == 0:
        return -100
    return abs(block1.webkit_style.height-block2.webkit_style.height)/max(block1.webkit_style.height, block2.webkit_style.height)
