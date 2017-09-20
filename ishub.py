 # -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.INFO)
import re
import numpy
import copy
import sys

#from app.hub_spider.htmlparser.block_maker import BlockMaker
from htmlparser3.block import Block, BlockType, all_grandson_xpath, MainBlock, merge_childrenxpath_by_tag
from htmlparser3.block_identify import BlockIdentifier
from htmlparser3.html_parser import parse
from htmlparser3.utils import get_text_len
from collections import Counter
from htmlparser3.page_charactor import PC
from pty import CHILD
from htmlparser3.link_filter import LinkFilter
from htmlparser3.core import PathInfo
from htmlparser3.build_tree import LevelTreeBuilder
from htmlparser3.block_distance import block_sim_distance, block_link_density_distance, block_structure_distance
from page_type_predict import PageTypePredictor

#only used to compute block similay
def add_gap_tags_to_block(blocks, child):
    if not blocks:
        return child
    merged_block = copy.copy(child)
    _current_tags = copy.copy(merged_block.gap_tags)
    for _block in blocks:
        merged_block.all_tags += _block.all_tags
        merged_block.all_text_node_list += _block.all_text_node_list
        merged_block.chars_count_in_links += _block.chars_count_in_links
        _current_tags.subtract(_block.gap_tags)
        for tag in _current_tags:
            count = _current_tags[tag]
            if count < 0 and tag not in merged_block.gap_tags:
                merged_block.gap_tags[tag] = abs(count)
    return merged_block
          
class IsHub(object):
    def __init__(self, model_file):
        self.tree_builder = LevelTreeBuilder()
        self.link_filter = LinkFilter()
        self.block_identifier = BlockIdentifier()
        self.can_main_block = None
        self.main_block = None
        self.middle_block_level = None
        self.mostly_text_level = None
        self.level_middle_blocks = None
        self.level_elements = None
        self.block_info = None
        self.all_text_len = None
        self.page_predictor = PageTypePredictor(model_file)
    
    def block_filtered(self, block):
        if not block.webkit_style:
            return False
        if not block.contains_text() and len(block.image_node_list) == 0:
            logging.info("Block Filtered By no text and image :%s %s %s", block.xpath, block.block_type.name, block.text)
            return True
        if block.block_type != BlockType.UNKNOWN and block.block_type != BlockType.TITLE_H1:
            logging.info("Block Filtered By Type:%s %s %s ", 
                         block.xpath, block.block_type.name, block.text)
            for link_node in block.all_link_node_list:
                link_node.father_block_type = block.block_type
            return True

        if  self.filter_top_block_bystyle(self.block_identifier.first_crumb_webkit_style, block) :
            logging.info("Block Filtered by Top before crumb block_top:%d block_left:%d  crumb_top:%d crumb_left:%d %s %s", 
                         block.webkit_style.top, block.webkit_style.left,self.block_identifier.first_crumb_webkit_style.top, self.block_identifier.first_crumb_webkit_style.left,
                        block.xpath, block.text)
            for link_node in block.all_link_node_list:
                link_node.father_block_type = BlockType.FILTERED
                link_node.filter_reason ="BEFORE_FIRST_CRUMB"
            return True
        if self.filter_top_block_bystyle(self.block_identifier.title_h1_webkit_style, block):
            logging.info("Block Filtered by Top before title %d %d %s %s", 
                         block.webkit_style.top, block.webkit_style.left, block.xpath, block.text)
            
            for link_node in block.all_link_node_list:
                link_node.father_block_type = BlockType.FILTERED
                link_node.filter_reason ="BEFORE_FIRST_TITLE_H1"
            return True
   
        return False
    
        
    def get_can_main_block(self, level):
        if level not in self.level_elements:
            return None
        can_blocks = []
        
        _middle_block = self.level_middle_blocks[level]
        # 如果该层中间块不被过滤（主要根据块类型），则直接返回中间块
        #if not self.block_filtered(_middle_block):
        #    return _middle_block
        
        _main_block = MainBlock()
        for block in self.level_elements[level]:
            if not block.webkit_style:
                continue
            if self.block_filtered(block):
                continue
            # 除了基本的过滤条件外，在一层选取时还根据坐标进行过滤
            if block.webkit_style.height < 100:
                logging.info("In get_can_main_block, Block Filtered by Height %d %s %s", 
                             block.webkit_style.height, block.xpath, block.text)
                continue
            if block.webkit_style.left >1440/2:
                logging.info("In get_can_main_block , Block Filtered by Left %d %s", 
                             block.webkit_style.height, block.xpath)
                continue
            # todo more
            if block.webkit_style.top >900:
                continue
            
            can_blocks.append(block)
            _main_block.blocks.append(block)
            logging.info("wwj debug add can_main_block level:%d %s %s top:%d left:%d width:%d height:%d %f %s score:%f", 
                         level, block.xpath, block.text, block.webkit_style.top, block.webkit_style.left,
                        block.webkit_style.width, block.webkit_style.height, 
                         block.links_density(), block.block_type.value, block.main_block_score)
       
        # 不一定只返回一个block，可以返回多个连续的block
        if len(can_blocks) ==0 :
            return None
        # not sort by width 
        '''
        #can_blocks.sort(key=lambda k: k.webkit_style.width, reverse=True)
        for block in can_blocks:
            logging.info("wwj debug block.width %s %d %f height:%d %s", 
                    block.xpath, block.webkit_style.width, block.main_block_score, block.webkit_style.height, block.text)
        # 返回score值最大的block，为候选块
        block = max(can_blocks, key=lambda(item):item.main_block_score)  
        logging.info("wwj debug get_main_block from first level %s %s %d %d %d %f link_objs_len %d score:%d %s", 
                         block.xpath, block.text, block.webkit_style.left,
                        block.webkit_style.width, block.webkit_style.height, 
                         block.links_density(), len(block.all_link_node_list), block.main_block_score, block.class_attr)
        '''
        return _main_block
        #return block
      
    def merge_can_mainblock_by_distance(self, all_children):
        if not all_children:
            return []
        last_child = None
        last_index = None
        merged_blocks = []
        new_blocks = []
        for index, child in all_children.items():
            logging.info("wwj debug merge_can_mainblock_by_distance first the child is %s %s", 
                        child.xpath, child.text)
            if last_child is None:
                logging.info("wwj debug last_child is None")
                new_blocks.append(child)
                merged_blocks.append(new_blocks)
                last_child = child
                last_index = index
            else:
                _distance = None
                if index-last_index!= 1:
                    logging.info("last child and child is not ajacement %d %d last_child:%s child:%s last_child.text:%s child.text:%s",
                                  last_index, index, last_child.xpath, child.xpath, last_child.text, child.text)
                    _distance = 100
                else:
                    _distance = block_sim_distance(child, last_child)       
                links_density_distance = block_link_density_distance(last_child, child)
                if _distance == -100:
                    logging.info("wwj debug merge_can_mainblock_by_distance strong distance should merge _distance:%f links_density_distance:%f, child:%s \
                                -----------last_child:%s merged_blocks len %d",
                              _distance,links_density_distance, child.text, last_child.text, len(merged_blocks)) 
                    #last_child = add_gap_tags_to_block(new_blocks, child)
                    last_child = child
                    last_index = index
                    new_blocks.append(child)
                    if len(new_blocks)>0 and new_blocks[-1].has_title_tag:
                        new_blocks[-1].text_after_title += child.text
                else:
                    if _distance >0.3 or links_density_distance > 0.25:
                        logging.info("wwj debug merge_can_mainblock_by_distance should seprate distance struct_distance %f, link_distance:%f :child:%s-----------last_child:%s",
                              _distance, links_density_distance, child.text, last_child.text) 
                        new_blocks = []
                        new_blocks.append(child)
                        merged_blocks.append(new_blocks)
                        last_child = child
                        last_index = index
                    else:
                        logging.info("wwj debug merge_can_mainblock_by_distance should merge _distance:%f links_density_distance:%f, child:%s-----------last_child:%s",
                              _distance,links_density_distance, child.text, last_child.text) 
                        #last_child = add_gap_tags_to_block(new_blocks, child)
                        last_child = child
                        last_index = index
                        new_blocks.append(child)
            
        if merged_blocks:
            logging.info("wwj debug merge_can_mainblock_by_distance all_len:%d  first_len:%d", 
                     len(merged_blocks),len(merged_blocks[0]))
        return    merged_blocks
    
    def filter_top_block_bystyle(self, _webkit_style, block):
        if _webkit_style is None:
            return False
        if not block.webkit_style:
            return False
        if (block.webkit_style.top+block.webkit_style.height) < _webkit_style.top:
            #logging.info("wwj debub tmp %s webkit_style.top %d block.webkit_style.top:%d height:%d", \
            #             block.text, _webkit_style.top, block.webkit_style.top, block.webkit_style.height)
            return True
        return False
          
    def filter_child_blocks(self, blocks, level):
        children = {}
        child_blocks = []
        for block in blocks:
            child_blocks += block.new_all_children_sort_by_postion
        
        for child in child_blocks:
            if child.block_type is None:
                #other_block's child has no block_type
                logging.info("wwj debug no block_type %d %s %s",level, child.xpath, child.text)
                self.block_identifier.get_block_type(child, self.all_text_len, self.body_style)
            
            if self.block_filtered(child):
                continue
            logging.info("Block Not Filter %s %s %s %d %d if_contains_text:%d score:%f", 
                         child.block_type.name, child.xpath, child.text, child.webkit_style.left, child.webkit_style.top, child.contains_text(),child.main_block_score)
            index = child_blocks.index(child)
            children[index]=child
        return children
            
    def traverse_tree(self, main_block, level):
        ''' digui'''
        #if level > max(self.middle_block_level, self.mostly_text_level):
        #    return
        #if level > self.block_info.levels - 1:
        #    return
        
        logging.info("wwj debug in traverse_tree %d %s", level, main_block.text)
        for block in main_block.blocks:
            _block_child_len = 0
            block_child_text_len = 0
            for child in block.new_all_children_sort_by_postion:
                block_child_text_len += child.all_text_len()
        # mostly text in block self, not in block.children
        if block_child_text_len < 0.5*main_block.all_text_len():
            self.main_block = main_block
            logging.info("wwj debug merged_blocks block_child_text_len <0.5*alllen %d, all_len %d", 
                             block_child_text_len, main_block.all_text_len())
            return

        index_children = self.filter_child_blocks(main_block.blocks, level)
        # has 1 children, just traverse down
        if len(index_children)==1:
            self.main_block = MainBlock()
            self.main_block.blocks.append(index_children.values()[0])
            logging.info("wwj debug in traverse_tree, index_children len is 1 %s %s",index_children.values()[0].xpath, index_children.values()[0].text)
            #self.traverse_tree(self.main_block, level+1)
            return
        
        merged_blocks = self.merge_can_mainblock_by_distance(index_children) 
        logging.info("wwj debug merged_blocks %d, all children count %d", 
                     len(merged_blocks), len(index_children))
        
        #no merge item, just return, and why 10
        if len(merged_blocks) ==len(index_children) and len(index_children)>10:
            logging.info("wwj debug no merged sub blocks, just return")
            self.main_block = MainBlock()
            for block in index_children.values():
                self.mainblock.blocks.append(block)
            return 
        #merged to 1, just return
        if len(merged_blocks) == 1:
            self.main_block = MainBlock()
            for block in merged_blocks[0]:
                self.main_block.blocks.append(block)
            logging.info("wwj debug sub blocks merged to 1, just return")
            return
        for blocks in merged_blocks:
            for block in blocks:
                logging.info("wwj debug merged_blocks info %s %s %s", 
                             block.xpath, block.text, id(blocks))
        _main_block = self.block_identifier.get_mainblock_from_list(merged_blocks, self.all_text_len, self.body_style, self.h1_tag_count)     
        if _main_block is None:
            logging.info("wwj debug main_block is None")
            if level+1 in self.tree_builder.level_middle_blocks:
                _next_level_mid_block = self.tree_builder.level_middle_blocks[level+1]
                if _next_level_mid_block is not None:
                    self.main_block = MainBlock()
                    self.main_block.blocks.append(_next_level_mid_block)
            else:
                self.main_block = main_block
            return 
        else:
            self.main_block = _main_block
        
        if level > max(self.middle_block_level, self.mostly_text_level):
            return
        #just retun
        #self.traverse_tree(self.main_block, level+1)
        
    def get_main_block(self, url, html_body):
        #build level tree
        self.tree_builder.build_level_tree(url, html_body)
        self.block_identifier = self.tree_builder.block_identifier
        self.middle_block_level = self.tree_builder.middle_block_level
        self.mostly_text_level = self.tree_builder.mostly_text_level
        self.title_level = self.tree_builder.title_level
        self.level_middle_blocks = self.tree_builder.level_middle_blocks
        self.level_elements = self.tree_builder.level_elements
        self.block_info = self.tree_builder.block_info
        self.all_text_len = self.tree_builder.all_text_len
        self.body_style = self.tree_builder.body_style
        self.h1_tag_count = self.tree_builder.block_maker.h1_tag_count
        
        self.main_block = None
        logging.info("Get main_block mostly_text_level %d, middle_block_level %d title_level %d", self.mostly_text_level, self.middle_block_level, self.title_level)
        self.can_main_block = MainBlock()
        
        first_level = None

        if self.middle_block_level == 0:
            # 没有找到中间块层。todo 用最顶层?
            # 返回block(body )
            # 如果页面连body都没有
            if len(self.level_elements) <3:
                self.can_main_block = None
                return
            
            first_level = 2
            self.can_block = self.level_elements[2][0]
        else:
            if self.title_level:
                first_level = min(self.middle_block_level, self.mostly_text_level, self.title_level)
            else:
                first_level = min(self.middle_block_level, self.mostly_text_level)
            self.can_block = self.level_middle_blocks[first_level]
            logging.info("wwj debug got can_middle_block %s %d %d", self.can_block.text, self.can_block.all_text_len(),self.can_block.chars_count_in_links)
        _main_block = self.get_can_main_block(first_level)
        
        if _main_block is None:
            self.can_main_block.blocks.append(self.can_block)
        else:
            logging.info("wwj debug get main_block from first level %s", _main_block.text)
            self.can_main_block = _main_block
        self.traverse_tree(self.can_main_block, first_level)

    def get_block_distance_ratio(self, children_xpath):
        #[[/a/b,c/d],[a/b]]
        all_count = 0
        same_struct_count = 0
        last_child = None
        ratio = 0
        if children_xpath is not None:
            for child in children_xpath:
                if last_child is not None: 
                    distance = block_structure_distance(last_child, child)
                    if distance < 0:
                        same_struct_count +=1
                last_child = child
                all_count+=1
            if all_count >1:
                ratio = same_struct_count*1.00/(all_count-1)
                logging.info("wwj debug block same link_tag child ratio %f %d ",
                             same_struct_count*1.00/(all_count-1), all_count )
            else:
                logging.info("wwj debug block same link_tag child ratio 0")
        return ratio
    
    def set_link_distribution(self, main_block):
        self.link_tags_density = 0
        self.links_density = 0
        self.height_difference = 2
        self.pos_distribution = 1
        self.first_top_ratio = 1
        self.end_top_ratio = 1
        self.link_count = 0
        self.link_area_cov = 0
        
        link_count = 0
        link_text_len = 0
        link_nodes = []
        map_x = dict()
        map_y = dict()
        _all_text_len = main_block.all_text_len()
        _link_nodes_textlen = 0
        for link_node in main_block.all_link_node_list:
            if self.link_filtered(link_node):
                continue
            logging.info("wwj debug got final link:%s href:%s",link_node.text, link_node.href)
            link_count += 1
            link_nodes.append(link_node)
            link_text_len += link_node.text_len
            _link_nodes_textlen += link_node.text_len
            x_key = int(link_node.webkit_style.left/10)
            y_key = int(link_node.webkit_style.top/10)
            if x_key not in map_x:
                map_x[x_key] = []
            if y_key not in map_y:
                map_y[y_key] = []
            map_x[x_key].append(link_node)
            map_y[y_key].append(link_node)
        if not link_nodes:
            return 
        if _all_text_len:
            self.links_density = _link_nodes_textlen*1.000/_all_text_len
        if not len(main_block.all_text_node_list)==0:
            self.link_tags_density = len(link_nodes)*1.000/(len(main_block.all_link_node_list))
        self.pos_distribution = (len(map_x.keys())**1.0)*len(map_y.keys())/(link_count*link_count)
        self.link_count = link_count
        most_key = sorted(map_x.items(), key=lambda item:len(item[1]), reverse=True)[0][0]
            
        logging.info("wwj debug get most_key:%d len:%d", most_key,len(map_x[most_key]))
        last_height = None
        height = None
        _compare = False
        #for key in sorted_map_y_keys:
        last_node = None
        self.first_top_ratio = abs((map_x[most_key][0].webkit_style.top-self.main_block.webkit_style.top)*1.00/self.main_block.webkit_style.height)
        logging.info("wwj debug tmp got first_link_node xpath:%s text:%s href:%s main_block_height:%d",
                     map_x[most_key][0].xpath, map_x[most_key][0].text,
                     map_x[most_key][0].href,
                     self.main_block.webkit_style.height)
        logging.info("wwj debug tmp got last_link_node xpath:%s text:%s href:%s main_block_height:%d",
                     map_x[most_key][-1].xpath, map_x[most_key][-1].text,
                     map_x[most_key][-1].href,
                     self.main_block.webkit_style.height)
        self.end_top_ratio =  abs(1-(map_x[most_key][-1].webkit_style.top-self.main_block.webkit_style.top)*1.00/self.main_block.webkit_style.height)
        
        self.link_area_cov = 1.00*(map_x[most_key][-1].webkit_style.top-map_x[most_key][0].webkit_style.top)/self.main_block.height
        _diff_count = 0
        _same_count = 0
        for node in map_x[most_key]:
            logging.info("wwj debug get height node:%s", node.text)

            if last_node:
                height = node.webkit_style.top -last_node.webkit_style.top
                if height<10:
                    continue
            if last_height:
                _compare = True
                _diff = last_height - height
                if _diff > 100:
                    logging.info("wwj debug the height diff %d height:%d last_height:%d key:%s last:%s %d", 
                            _diff,height, last_height,
                           node.text, last_node.text, node.webkit_style.top)
                    _diff_count += 1
                    #self.height_difference = 1
                else:
                    _same_count += 1
            last_node = node
            last_height = height
        if _same_count!= 0  or _diff_count!=0:
            self.height_difference = _diff_count*1.00/(_same_count+_diff_count)
        #if _compare and self.height_difference!=1:
        #    self.height_difference = 0
    
    def link_filtered(self, link_node):
     
        #filter javascript link 
        if link_node.visible == False:
            logging.info("The Link is Filtered by visible %s", link_node.text)
            return True
        if link_node.href=="" or link_node.href.startswith("javascript"):
            logging.info("The Link is Filtered by href %s href:%s", link_node.text, link_node.href)
            return True
        if link_node.text_len==0 and link_node.image_count == 0:
            logging.info("The Link is Filtered by text_len==0 and link_node.image_count %s", link_node.text)
            return True
        if link_node.father_block_type is not None and link_node.father_block_type is not BlockType.UNKNOWN and link_node.father_block_type is not BlockType.TITLE_H1:
            logging.info("The Link is Filtered by BlockType:%s reason:%s text:%s", 
                         link_node.father_block_type.name, link_node.filter_reason,link_node.text)
            return True

        if self.link_filter.filtered_by_pos(link_node):
            logging.info("The Link is Filtered by pos left:%d %s", link_node.webkit_style.left, link_node.text)
            return True
        if link_node.text_len <8 and (link_node.text.find(u"更多")!=-1\
                                       or link_node.text.find(u"详情")!=-1):
            logging.info("The Link is Filtered by keyword %s", link_node.text)
            return True
        #if self.link_filter.is_textin_link(link_node) and link_node.text_len <0.2*self.main_block.all_text_len():
        #    logging.info("wwj debug get_useful_link filtered %s %d %d", 
        #                     link_node.xpath, link_node.image_count, self.main_block.all_text_len())
        #    return True
        #todo filtered by text before
        #if link_node.text_len <=4 and link_node.image_count ==0:
        #    return True
        #if self.link_filter.filtered_by_width(link_node):
        #    return True

        return False
    
    def get_image_linkcount(self, main_block):
        if not main_block:
            return 0
        image_count = 0
        for block in main_block.blocks:
            logging.info("wwj debug got image_node_list %d %s", 
                         len(block.img_link_node_list), block.xpath)
            image_count += len(block.img_link_node_list)
        #todo need filter some image
        return image_count
      
    def get_page_charactor(self, url):
        _can_link_density = self.can_block.links_density()
        _can_link_tag_density = self.can_block.link_tags_density()
        _can_text_distance = self.can_block.text_tag_distance()
        _can_tag_density = self.can_block.tag_density()
        logging.info("IN GET_PAGE_PC wwj debug can_block pagecharactor %s text_distance:%d links_density:%f %d %d _link_tag_density:%f %d %d", 
                     url, _can_text_distance, self.can_block.links_density(),
                     self.can_block.chars_count_in_links, self.can_block.all_text_len(), _can_link_tag_density, self.can_block.webkit_style.width, 
                     self.can_block.webkit_style.height)
        
        logging.info("Get final main_block %s %d %d", 
                     self.main_block.text, self.main_block.chars_count_in_links, len(self.main_block.all_link_node_list))
        
        self.set_link_distribution(self.main_block)
        
        image_link_count = self.get_image_linkcount(self.main_block)
        _pc = PC(url=url, 
                 mainblock_link_tags_density = self.main_block.link_tags_density(),
                 mainblock_links_density = self.main_block.links_density(), 
                 mainblock_useful_link_tags_density = self.link_tags_density,
                 mainblock_useful_links_density = self.links_density,
                 mainblock_useful_links_count = self.link_count,
                 mainblock_image_links_count = image_link_count, 
                 mainblock_pos_distance = self.pos_distribution, 
                 mainblock_height_difference =self.height_difference,
                 mainblock_first_top_ratio = self.first_top_ratio,
                 mainblock_end_top_ratio = self.end_top_ratio,
                 mainblock_link_area_cov = self.link_area_cov)
        
        _pc.normalize()
        _pc_str = _pc.tostring()
        return _pc_str
    
    def predict_page_type(self, url):
        pc_str = self.get_page_charactor(url)
        logging.info("wwj debug get pagecharactor url:%s, pc:%s", url, pc_str)
        return self.page_predictor._predict(pc_str)





def predict(is_hub, f_result, url, body):
    is_hub.get_main_block(url, body)
    if is_hub.can_main_block is None:
        page_type = "-1.0"
        print url, page_type
        sys.exit(0)
        print "get page_charactor done"
    page_type = is_hub.predict_page_type(url)
    print url, page_type
    f_result.write(str(page_type)+"\t"+url)

if __name__ == "__main__":
    url = "http://www.baidu.com/"
    body = "<html webkit_style=\"top:0px;left:0px;width:1440;height:1529;\"><body webkit_style=\"top:0px;left:0px;width:1440;height:1529;\"><script type=\"text/javascript\" src=\"http://pix04.revsci.net/F09828/b3/0/3/120814/27018474.js?D=DM_LOC%3Dhttp%253A%252F%252Fwww.56.com%252Fw95%252Falbum-aid-13790189.html%253Fbpid%253D56%2526_rsiL%253D0%26DM_EOM%3D1&amp;C=F09828\" webkit_style=\"top:0px;left:0px;width:0;height:0;\"></script></body></html>"
    if not body:
        print "invalid body"
        sys.exit(-1)
    is_hub = IsHub("model.0512")
    f_result = open("page_type.lst", "w")
    predict(is_hub, f_result, url, body)
    f_result.close()
