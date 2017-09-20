# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals
from six.moves.urllib.parse import urljoin
import re
import logging
import json
from six.moves.urllib.parse import urlparse, urlunparse
from pip._vendor.distlib._backport.tarfile import TUREAD
from .utils import get_text_len
from .block_identify import BlockIdentifier 
BLACK_LIST={u'版权声明',u'免责声明'}   
punctuation_set={'|','>>','.',':'}
BLACK_LIST={u'邮箱',u'登陆',u'保险',u'注册',u'充值',u'登录',u'密码',u'隐私',u'退出'
            u'微信',u'微博',
            u'友情链接', u'投稿',u'建议', u'反馈',u'关注',u'联系',u'举报',u'帮助',u'客户服务',
            u'版权', u'公司', u'我们',u'广告服务',u'关于',
            u'新闻端',u'客户端',u'移动版',u'手机版',u'APP'
            u'搜索',u'网站地图'}

FONT_TAGS=['strong', 'b', 'u','font', 'i', 'em']
STYLE_TAGS=['span', 'br']  
class LinkFilter(object):
    def __init__(self):
        pass
    def is_textin_link(self, link_obj):
        block_indentifier = BlockIdentifier() 
        if not link_obj:
            return False
        #not in p <div>text1111<a>hi</a>
        if link_obj.before_is_text and link_obj.after_is_text and get_text_len(link_obj.before_text)>1:
            return True
    
    
        block = link_obj.block
        logging.info("wwj debug link_obj %s block:%s %s %d %d text:%s", 
                 link_obj.xpath, block.xpath, block.links_density(), len(block.all_link_node_list), len(block.all_text_node_list), link_obj.text)
        if not  block_indentifier.is_textblock(block):
            return False
        ## if a in <p> tag, return True
        #slow
        paragraph_pattern = re.compile('.*/p\[\d+\](.*)/a\[\d+\]')
        result = re.findall(paragraph_pattern, link_obj.xpath)
        #self
        #other_block = link_obj.other_block
        if result:
            match_str= result[-1]
            if match_str=="":
                return True
            else:
                tags = re.findall(r"[A-Za-z]+", result[-1])
                for tag in tags:
                    if tag not in FONT_TAGS and tag not in STYLE_TAGS:
                        return False
                    return True
                return False
                    

    def filtered_by_width(self, link_obj):
        if link_obj.webkit_style.width < 50:
            return True
        return False

    def filtered_by_pos(self, link_obj):
        if link_obj.webkit_style.left > 1440*2/3:
            return True
        return False

        
