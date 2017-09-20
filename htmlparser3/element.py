# -*- coding: utf8 -*-
from .utils import get_text_len
from .utils import normalize_whitespace 
import copy

punctuation_set={'|','>>','.',':'}
BLACK_LIST={u'邮箱',u'登陆',u'保险',u'注册',u'充值',u'登录',u'密码',u'隐私',u'退出'
            u'微信',u'微博',
            u'友情链接', u'投稿',u'建议', u'反馈',u'关注',u'联系',u'举报',u'帮助',u'客户服务',
            u'版权', u'公司', u'我们',u'广告服务',u'关于',
            u'新闻端',u'客户端',u'移动版',u'手机版',u'APP'
            u'搜索',u'网站地图'}

FONT_TAGS=['strong', 'b', 'u','font', 'i', 'em']
STYLE_TAGS=['span', 'br']


class ElementNode(object):
    def __init__(self, start_position, visible, path, block, other_block):
        self.start_position = start_position
        self.path = path
        self.xpath = path.xpath
        self.dom = path.dom
        self.block = block
        self.other_block = other_block
        
        self.visible = visible
        self.tag = None
        self.attributes = {}
        self.text = ""
        
        self.webkit_style = None
        self.block_type = BlockType.Unknown

        self.father_node = None
        self.pre_brother = None
        self.next_brother = None
    
    @property
    def text_len(self):
        return get_text_len(self.text)
        

class TextNode(ElementNode):
    def __init__(self, start_position, visible, path, block, other_block, text):
        super(TextNode, self).__init__(start_position,visible, path, block, other_block)
        self.text = text
        
        pass

class ImageNode(ElementNode):
    def __init__(self, start_position, visible, path, block, other_block):
        super(ImageNode, self).__init__(start_position, visible, path, block, other_block)
        self.src = None
        self.width = None
        self.height = None
        self.alt = None
        
class LinkNode(ElementNode):
    def __init__(self, start_position,visible, path, block, other_block, href):
        super(LinkNode, self).__init__(start_position,visible, path, block, other_block)
        self.href = href
        self.before_text=""
        self.after_text = ""
        self.before_is_text = False
        self.after_is_text = False
        self.image_count = 0
        self.has_onclick = False
        self.has_onload = False
        self.text=""
        self.father_block_type = BlockType.Unknown
        self.filter_reason = ""
        self.is_filtered = False
        

    def add_text(self, text):
        self.text += normalize_whitespace(text)
        
    
class InputNode(ElementNode):
    def  __init__(self, start_position, visible, path, block, other_block):
        super(InputNode, self).__init__(start_position, visible, path, block, other_block)
        self.type = None
    def set_type(self, _type):
        self.type = _type
    def set_value(self, value):
        self.value = value
class UserInteractNode(ElementNode):
    def  __init__(self, tag_name, start_position, visible, path, block, other_block):
        super(UserInteractNode, self).__init__(start_position,visible, path, block, other_block)
        self.tag_name = tag_name
        self.father = None
        self.nextsibling = None
        self.firstchild = None
        
