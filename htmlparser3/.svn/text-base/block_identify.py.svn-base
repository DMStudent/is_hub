#            -*- coding: utf8 -*-
from .block import Block, MainBlock, BlockType
import logging
import operator
from .utils import get_text_len

recommend_words = {u"排行榜", u"热评",u"相关", u"其他相关", u"类似",u"相似", u"猜你喜欢", u"热门", u"最新", u"附近的", u'推荐', u'向你推荐',u'您可能',u'你可能'}

issue_words={u'版权声明',u'免责声明'}
CRUMB_MARK = {">",u"›", ">>", u"»","->", "->>", "-->>", "-- >>", "?"}
CLASS_FOOTER = {"footer", "foot", "bottom"}
CLASS_HEADER ={"head", "nav", "banner", "hd"}
CLASS_BANNER ={"head", "nav", "banner", "hd"}

class BlockIdentifier(object):
    
    def __init__(self):
        self.first_crumb_webkit_style = None
        self.title_h1_webkit_style = None

    def is_invisible(self, block):
        if block.webkit_style is not None and (block.webkit_style.width==0 or block.webkit_style.height==0):
            return True
        return False
    
    def is_invalid_style(self, block, body_style):
        if  block.webkit_style is None:
            return True
        # render wrong
        if body_style is not None and block.webkit_style.top < body_style.height and block.webkit_style.top >body_style.height*0.95 and block.webkit_style.height<200:
            logging.info("block filtered by bottom %s %s top:%d body_height:%d",
                         block.xpath, block.text, block.webkit_style.top, body_style.height)
            return True
        return False
    
    def is_topblock(self, block, body_style):
        if body_style and block.webkit_style.top!=0 and block.webkit_style.top < body_style.height*0.01 and block.webkit_style.height <200:
            logging.info("block filtered by top %s %s top:%d body_height:%d",
                         block.xpath, block.text, block.webkit_style.top, body_style.height)
            return True
        return False
    
    def is_headerblock(self, block):
        for _head in CLASS_HEADER:
            class_attr = block.attributes.get("class")
            id_attr = block.attributes.get("id")
            if (class_attr and class_attr.find(_head)!=-1) or (id_attr and id_attr.find(_head)!=-1):
                if block.start_position <10 :
                    return True
            return False

    def is_bannerblock(self, block):
        for _banner in CLASS_BANNER:
            class_attr = block.attributes.get("class")
            if class_attr and class_attr.find(_banner)!=-1:
                if block.webkit_style.width > 600 and block.all_text_len()<20:
                    logging.info("The Block's BlockType is BANNER %s %s", block.xpath, block.text)
                    return True
        return False

    def is_textblock(self, block):
        if not block:
            return False
        if len(block.all_link_node_list)>3 and block.links_density()>0.35:
            return False
        if len(block.all_link_node_list)>2 and block.link_tags_density()>0.35 :
            return False
        return True

    def is_sideblock(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if block.webkit_style.left <1440/2 and \
            block.webkit_style.left+block.webkit_style.width>1440/2:
            return False
        if block.webkit_style.width >400:
            return False
        
        for word in recommend_words:
            if block.text.find(word) != -1:
                logging.info("The Block's BlockType is Right-Side %s %s", block.xpath, block.text)
                return True
            #TODO 右边栏框只有链接，没有含有关键字的文本，这个判断条件要加上
        return False

    
    def is_footerblock(self, block, all_text_len):
        #by class
        for _foot in CLASS_FOOTER:
            class_attr = block.attributes.get("class")
            id_attr = block.attributes.get("id")
            if (class_attr and class_attr.find(_foot)!=-1) or (id_attr and id_attr.find(_foot)!=-1):
                if block.start_position + block.all_text_len()+10 > all_text_len:
                    logging.info("The Block's BlockType is FOOTER %s %s", block.xpath, block.text)
                    return True
        return False
    
    def is_bottomblock(self, block, body_style):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if not body_style:
            return False
        if body_style.height >=900 and block.webkit_style.top > body_style.height*3/4:
            logging.info("The Block's BlockType is Bottom %s %s %d", block.xpath, block.text, block.text.find(u"排行版"))
            return True
        return False
        

    def is_shareblock(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if block.webkit_style.width <100 and block.all_text_len() <30 and  block.text.startswith(u"分享") or block.text.startswith(u"微信") or block.text.startswith(u"新浪微博") or block.text.startswith(u"微博") or block.text.startswith(u"QQ空间"):
            return True
        return False

    def is_crumb(self, block):
        if not block.webkit_style: 
            return False
        if block.webkit_style.width == 0:
            return False
        if len(block.all_link_node_list)==0:
            return False
        if block.all_text_len() >50:
            return False
        
        #1. 根据链接前的文本来判断 
        crumb_count = 0
        link_count = 0
        for link_node in block.all_link_node_list:
            logging.info("wwj debug maybe crumb:%s before:%s",link_node.text, link_node.before_text)
            if link_node.text!="" and link_node.before_text!="" :
                if link_node.before_text in CRUMB_MARK:
                    link_count +=1
                    crumb_count += 1
        if crumb_count >=1 and (crumb_count == link_count -1 or crumb_count == link_count ):
            logging.info("The Block's BlockType is CRUMB %s %s %d %d top:%d left:%d",
                          block.xpath, block.text, block.all_text_len(), len(block.all_link_node_list),
                          block.webkit_style.width, block.webkit_style.height)

            if self.first_crumb_webkit_style is None or self.first_crumb_webkit_style.top > block.webkit_style.top:
                self.first_crumb_webkit_style = block.webkit_style
            return True
        
        #2. 根据class 属性和链接长度、密度来判断
        _class_attr = block.attributes.get("crumb")
        if _class_attr and _class_attr.find("crumb")!=-1:
            if block.links_density>0.40 and  len(block.all_link_node_list)>=1 \
            and block.all_text_len()/len(block.all_link_node_list)<8:
                logging.info("The Block's BlockType is CRUMB by class_attr %s %s %d %d class_attri:%s",
                          block.xpath, block.text, block.all_text_len(), len(block.all_link_node_list),\
                          block.class_attr)
            return True
            
        return False
    
    def is_nav(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if len(block.all_link_node_list)==0:
            return False
        if len(block.image_node_list)>2 or (len(block.all_link_node_list)-len(block.image_node_list) -len(block.image_node_list))<3:
            return False
        if block.all_text_len() -block.chars_count_in_links >20:
            return False
        _class_attr = block.attributes.get('class')
        if _class_attr and _class_attr.find("nav")!=-1:
            if block.links_density()>0.40 and block.chars_count_in_links/len(block.all_link_node_list)<8 and len(block.all_link_node_list)>2:
                logging.info("The Block's BlockType is NAV (tag nav) %s %s", block.xpath, block.text)
                return True
        
        # 最大文本节点长度
        if block.long_text_node is not None and block.long_text_node.text_len < 8:
            if block.links_density()>0.40 and block.chars_count_in_links/len(block.all_link_node_list)<8 and len(block.all_link_node_list)>2:
                logging.info("The Block's BlockType is NAV %s %s", block.xpath, block.text)
                return True
        
        return False
    
    #todo 
    def is_recommend_block(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if len(block.all_link_node_list)<2:
            return False
        if block.links_density()<0.1:
            return False
        top = 525
        bottom = 825
        left = 520
        right = 620
        
        # block not cover middle
        if block.webkit_style.top < top and block.webkit_style.left<left \
         and (block.webkit_style.top+block.webkit_style.height) >bottom and \
         (block.webkit_style.left +block.webkit_style.width)>right:
            return False
        
        for word in recommend_words:       
            if block.text.startswith(word) or block.text.endswith(word):
                logging.info("The Block's BlockType is RECOMMEND %s %s word:%s no_linktext %s",
                              block.xpath, block.text, word, block.nolink_text)
                return True
        return False
    
    def is_login_block(self, block):
        LOGIN_WORDS={u"会员",   u"密码", u"账号", u"账户",u"注册", u"大名",  u"邮箱",  u"匿名",  u"昵称",  u"姓名", u"登录",u"登陆", u"登入",  u"用户",u"验证码"}
        if not block.webkit_style:
            return False
        if not block.contains_text():
            return False
        if block.all_text_len()>100:
            return False
        
        login_key_word = False
        login_tag_hit = False
        
        #关键字判断
        for login_word in LOGIN_WORDS:
            if block.text.find(login_word)!= -1:
                login_key_word = True
                break
        
        if not login_key_word:
            return False

        # tag 判断
        # tag 判断1：input 标签
        for input_node in block.input_node_list:
            _value = input_node.attributes.get("value")
            if _value and (_value.find(u"注册")!=-1 or _value.find(u"登陆")!=-1 or _value.find(u"登录")!=-1 or \
                    _value.find(u"登入")!=-1):
                login_tag_hit = True
                logging.info("The Block's BlockType is LOGIN %s %s", block.xpath, block.text)
                return True
            _type = input_node.attributes.get("type")
            if _type and (_type == "password"):
                login_tag_hit = True
                logging.info("The Block's BlockType is LOGIN %s %s", block.xpath, block.text)
                return True
            
            _class = input_node.attributes.get("class")
            _id = input_node.attributes.get("id")
            if (_class and (_class.find("login")!=-1 or _class.find("register")!= -1)) or \
             (_id and (_id.find("login")!= -1 or _id.find("register")!= -1)):
                login_tag_hit = True
                logging.info("The Block's BlockType is LOGIN %s %s", block.xpath, block.text)
                return True
            
        # tag 判断2：image 标签
        for image_node in block.image_node_list:
            _alt = image_node.attributes.get("alt")
            if _alt and (_alt.find(u"注册")!=-1 or _alt.find(u"登陆")!= -1 or _alt.find(u"登录")!=-1 or _alt.find(u"登入")!=-1):
                return True
            
            
        #tag 判断3：a 标签
        
        for link_node in block.all_link_node_list:
            _id = link_node.attributes.get("id")
            _class = link_node.attributes.get("class")
            if (_class and (_class.find("login")!=-1 or _class.find("register")!= -1 )) or \
                 (_id and (_id.find("login")!= -1 or _id.find("register")!= -1)):
                login_tag_hit = True
                logging.info("The Block's BlockType is LOGIN %s %s", block.xpath, block.text)
                return True
        
        return False
         
    def is_search_block(self, block):
        if not block.webkit_style:
            return False
        if not block.contains_text():
            return False
        if block.all_text_len()>100:
            return False
        search_keyword = False
        input_node_hit = False
        search_words={u"搜索", u"搜寻", u"查询", u"查找", u"类型", u"检索", u"搜", u"找",u"关键字", u"关键词", u"search"}
        for search_word in search_words:
            if block.text.find(search_word)!=-1:
                search_keyword = True
                break
        if not search_keyword:
            return False
        #1. 根据input_node 判断。分为submit/button/text/image 四种类型判断。根据class id属性值判断
        for input_node in block.input_node_list:
            if not input_node.visible:
                continue

            _value = input_node.attributes.get('value')
            if input_node.type and (input_node.type == 'submit' or input_node.type=='button'):

                if _value:
                    words={u"搜索", u"搜寻", u"查询", u"查找", u"类型", u"检索", "go", "search"}
                    for word in words:
                        if _value.find(word)!=-1:
                            input_node_hit = True
                            logging.info("wwj debug tmp find button hit words %s %s", input_node.xpath, input_node.attributes['value'])
                            break
            if input_node.type and input_node.type == "text":
                name = input_node.attributes.get('name')
                if name:
                    #key word
                    if name.find('keyword')!=-1 or name.find('key')!=-1:
                        input_node_hit = True
                        logging.info("wwj debug tmp find input name hit keyword %s %s", input_node.xpath, input_node.attributes['name'])
                        break
                if _value:
                    if _value.find(u"输入")!=-1 or _value.find(u"关键")!=-1:
                        logging.info("wwj debug tmp find input value hit keyword %s %s", input_node.xpath, input_node.attributes['value'])
                        input_node_hit = True
                        break
            if input_node.type and input_node.type =='image':
                src = input_node.attributes.get('src')
                if src and src.find('search')!=-1:
                    logging.info("wwj debug tmp find input image src keyword %s %s", input_node.xpath, input_node.attributes['value'])
                    input_node_hit = True
                    break
                
                alt = input_node.attributes.get('alt')
                if alt and ( alt.find("search")!=-1 or alt.find(u"搜索")!=-1 or alt.find(u"提交")!=-1):
                        input_node_hit = True
                        break

            id = input_node.attributes.get("id")
            if id and id.find("search")!=-1:
                input_node_hit = True
                break
            class_name = input_node.attributes.get("class")
            if class_name and class_name.find("search")!=-1:
                input_node_hit = True
                break
            
        if not input_node_hit:
            for user_node in block.user_interact_list:
                if not user_node.visible:
                    continue
                if user_node.tag_name == "form":
                    _id = user_node.attributes.get(id)
                    if _id and _id.find("search")!=-1:
                        logging.info("wwj debug tmp find form id %s %s", user_node.xpath, user_node.attributes['id'])
                        input_node_hit = True
                        break
                    _action = user_node.attributes.get("action")
                    if _action and _action.find("search")!=-1:
                        logging.info("wwj debug tmp find form action %s %s", user_node.xpath, user_node.attributes['action'])
                        input_node_hit = True
                        break
                
                if user_node.tag_name == "button":
                    if user_node.text.find("search")!=-1 or user_node.text.find(u"搜")!=-1:
                        logging.info("wwj debug tmp find button text %s %s", user_node.xpath, user_node.text)
                        input_node_hit = True
                        break
                    
        if input_node_hit and search_keyword:
            logging.info("The Block's BlockType is SEARCH %s %s", block.xpath, block.text)
            return True
        return False

    def is_user_input_block(self,block):
        COMMENT_WORDS={u"评论" , u"留言" , u"发言" , u"点评" , u"提交" , u"回复" , u"内容" , u"好评" , u"差评" , u"发表" ,u"字数" , u"标题" , u"表情" , u"积分" , u"选填" , u"必填" , u"评价" , u"中立" , u"发布" , u"字符" ,u"本站立场", u"严禁发布", u"遵守互联网",u"记住我", u"必须", u"必需", u"来说两句",u"不能为空" };
        if not block.webkit_style:
            return False        
        if block.all_text_len()>300:
            return False
        #
        #if len(block.all_link_node_list)-len(block.image_node_list) >6:
        #    logging.info("wwj debug is_user_input_block len(block.all_link_node_list)-len(block.image_node_list) >6%s %d %d", 
        #                 block.text, len(block.all_link_node_list),len(block.image_node_list))
        #    return False
        
        if len(block.input_node_list)==0 and len(block.user_interact_list) ==0:
            return False
        action_words={u"发表",u"发帖",u"发送", u"提交",u"确定",u"确认",u"递交",u"留言",u"回复",u"点评",u"评论"}
        input_keyword = False
        input_hit_key = False
        for word in COMMENT_WORDS:
            if block.text.find(word)!=-1:
                input_keyword = True
                logging.info("wwj debug tmp find user_input text %s",block.text)
        if not input_keyword:
            return False
        for user_node in block.user_interact_list:
            if not user_node.visible:
                continue
            if user_node.tag_name == "button":
                logging.info("wwj debug got button %s", block.text)
                for word in action_words:
                    if user_node.text.find(word)!=-1:
                        input_hit_key = True
                        break
                if input_hit_key:
                    break
            if user_node.tag_name == "form":
                _id = user_node.attributes.get("id")
                _class = user_node.attributes.get("class")
                _action = user_node.attributes.get("action")
                if (_id and _id.find("comment")!=-1 or (_class  and _class.find("comment")!=-1) or\
                    _action and _action.find("comment")!=-1):
                    input_hit_key = True
                    break
                    
        if not input_hit_key:
            for input_node in block.input_node_list:
                if not input_node.visible:
                    continue
                _value = input_node.attributes.get("value")
                _id = input_node.attributes.get("id")
                _class = input_node.attributes.get("class")
                if (_id and _id.find("comment")!=-1) or (_class and _class.find("comment")!=-1):
                    input_hit_key = True
                    break
                for word in action_words:
                    if _value and _value.find(word)!=-1:
                        input_hit_key = True
                        break
                if  input_hit_key:
                    break
        
        if input_keyword and input_hit_key:
            logging.info("The Block's BlockType is USER_INPUT %s %s", block.xpath, block.text)
            return True
        return False
        
            
    def is_next_block(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width ==0 and block.father is not None:
            if block.father.webkit_style and  block.father.webkit_style.width>0 and block.webkit_style.width<373:
                return False
        #include main content
        if block.webkit_style.height >300:
            return False
        if block.webkit_style.width > 0 and block.webkit_style.width < 266:
            return False
        if block.all_text_len()> 100:
            return False
        if len(block.all_link_node_list) < 2:
            return False 
        block_text = block.text.encode("utf8")
        if block_text.startswith("上一") or block_text.startswith("下一") or \
            block_text.startswith("前一") or block_text.startswith("后一")  or \
            block_text.startswith("上页") or  block_text.startswith("下页") or \
            block_text.startswith("上篇") or  block_text.startswith("下篇") or \
            block_text.startswith("前篇") or  block_text.startswith("后篇"):
            logging.info("The Block's BlockType is NEXT_PAGE %s %s", block.xpath, block.text)
            return True
        
        if (block_text.find("上一")!=-1 and block_text.find("下一")!=-1) or \
            (block_text.find("前一") !=-1 and block_text.find("后一")!=-1)  or \
            (block_text.find("上页")!= -1 and  block_text.find("下页") != -1) or \
            (block_text.find("上篇") != -1 and  block_text.find("下篇") !=-1 )or \
            (block_text.find("前篇")!=-1 and  block_text.find("后篇")!= -1):
            logging.info("The Block's BlockType is NEXT_PAGE %s %s", block.xpath, block.text)
            return True
        
        if (block.all_link_node_list[0].text.isdigit() or\
             block_text.startswith("首页") or \
             block_text.startswith("第") or\
              block_text.startswith("上一") \
              or block_text.startswith("前一"))and \
                ( block.all_link_node_list[-1].text.isdigit() \
                  or block_text.endswith("下一", -3) or \
                   block_text.endswith("后一", -3) or  \
                   block_text.endswith("下页") or  \
                   block_text.endswith("下篇") or \
                block_text.endswith("后篇") or \
                block_text.endswith("后页") or \
                block_text.endswith("末页") or \
                block_text.endswith("尾页")):
            logging.info("The Block's BlockType is NEXT_PAGE %s %s", block.xpath, block.text)
            return True
        return False
    
        
    def is_issued_block(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        for word in issue_words:       
            if block.text.startswith(word):
                logging.info("wwj debug block was filtered by issued %s %s", block.xpath, block.text)
                return True
        return False
        
    def is_ads_block(self, block):
        pass
    
    def is_bbs_userinfo_block(self, block):
        if not block.webkit_style:
            return False
        if block.webkit_style.width == 0:
            return False
        if block.all_text_len()<10 or block.all_text_len()>400:
            return False
        words_4 = {u"在线时间", u"在线状态", u"在线等级", u"当前在线", u"当前离线", u"注册时间", u"注册日期", \
                   u"注册天数", u"阅读权限", u"新手上路", u"作者资料", u"阅读权限", u"论坛元老", u"论坛等级", \
                   u"论坛游民", u"论坛游侠", u"论坛积分", u"社区公民", u"超级版主", u"组别版主", u"注册会员", \
                   u"注册用户", u"普通用户", u"普通主题", u"正式会员", u"中级会员", u"普通会员", u"初级会员", \
                   u"荣誉会员", u"高级会员", u"金牌会员", u"会员级别", u"版主帖子", u"总发帖数", u"帖子数量", \
                   u"发贴总数", u"社区金币", u"魅力指数", u"最后登陆", u"最后登录", u"登录次数", u"发表时间", \
                   u"加入时间", u"今日心情", u"今日贴子", u"使用道具", u"升级进度", u"用户积分", u"个人空间", \
                   u"个人资料", u"个性首页", u"活跃指数"}
        
        words_2 = {u"精华", u"积分", u"帖子", u"贴子", u"威望", u"等级", u"级别", u"贴数", u"帖数", \
                   u"人气", u"财富", u"财产", u"经验", u"头衔", u"金钱", u"银币", u"银元", u"金币", \
                   u"现金", u"铜币", u"相册", u"文章", u"注册", u"来自", u"性别", u"贡献", u"网币", \
                   u"微博", u"粉丝", u"奴数", u"主题", u"状态", u"魅力",u"声望", u"体力", u"离线", \
                   u"版主", u"会员", u"组别", u"门派", u"顶端", u"生日", u"鲜花", u"昵称", u"角色", \
                   u"游客", u"文采", u"权限", u"勋章"}
        
        words_3 = {u"贡献值", u"帖子数" ,u"总贴数", u"管理员", u"美誉度", u"好评度" , u"交易", \
                   u"经验值",  u"用户组", u"发帖数", u"总结分", u"论坛币", u"地产币", u"影响力", \
                   u"游戏币", u"威望值", u"新会员", u"发帖人"}
        
        user_operation_words = {u"发短消息", u"发送消息", u"发站内信", u"发送短信", u"加为好友", 
                                u"加好友", u"加关注", u"发短信", u"发私信", u"关注"}
        key_weight = 0       
        for word in words_4:
            pos = block.text.find(word)
            if pos !=-1 and pos+4 < block.all_text_len():
                pos += 4
                while block.text[pos].isspace():
                    logging.info("wwj debug maybe user_info_block word:%s %s next:%s", 
                            word, block.text, block.text[pos])
                    pos += 1
                if block.text[pos] == ':' or block.text[pos] == u'；' or block.text[pos].isdigit():
                    key_weight += 1
                    logging.info("wwj debug maybe user_info_block add key_weight word:%s %s %s", 
                            word, block.text, block.text[pos+1])

        for word in words_3:
            pos = block.text.find(word)
            if pos !=-1 and pos+3 < block.all_text_len():
                pos += 3
                logging.info("wwj debug maybe user_info_block word:%s %s next:%s", word, block.text, block.text[pos+1])
                while block.text[pos].isspace():
                    pos += 1
                if block.text[pos] == ':' or block.text[pos] == u'；' or block.text[pos].isdigit():
                    logging.info("wwj debug maybe user_info_block add key_weight word:%s %s %s", 
                            word, block.text, block.text[pos+1])
                    key_weight += 1
        
        for word in words_2:
            pos = block.text.find(word)
            if pos !=-1 and pos+3 < block.all_text_len():
                logging.info("wwj debug maybe user_info_block word:%s %s  cur:%s next:%s type:%s", 
                        word, block.text, block.text[pos], block.text[pos+2], type(block.text[pos+2]))
                pos += 2
                while block.text[pos].isspace():
                    pos += 1
                if block.text[pos] == ':' or block.text[pos] == u'：' or block.text[pos].isdigit():
                    logging.info("wwj debug maybe user_info_block add key_weight word:%s %s %s", 
                            word, block.text, block.text[pos+1])
                    key_weight += 1
        for word in user_operation_words:
            pos = block.text.find(word)
            if pos!=-1:
                logging.info("wwj debug maybe user_info_block word:%s %s", word, block.text)
                key_weight +=1 
                
        if key_weight >=3:
            logging.info("The Block's BlockType is BBS_USER_INFO %s %s %d", 
                    block.xpath, block.text, key_weight)
            return True





    
    def is_h1title_block(self, block):
        if 'h1'  in block.gap_tags:
            if not block.webkit_style:
                return False
            if not self.title_h1_webkit_style or self.title_h1_webkit_style.top >block.webkit_style.top:
                self.title_h1_webkit_style = block.webkit_style
            # 仅含有h1标签的不是h1 title block. 根据title后的文本长度做筛选
            if not block.path.dom.endswith(".h1"):
                logging.info("The Block's BlockType is TITLE_H1 %s %s", block.xpath, block.text)
                return True
        return False
    
    
    def is_block_filtered(self, block):
        if self.is_invisible(block) or self.is_crumb(block) or self.is_ads_block(block) or self.is_nav(block) or self.is_recommend_block(block)\
        or self.is_issued_block(block):
            return True
        return False
    
    def get_block_type(self, block, all_text_len, body_style):
        if not block.webkit_style :
            block.block_type = BlockType.FILTERED
            block.filter_reason="No webkit_style"
        elif not block.visible:
            block.block_type = BlockType.FILTERED
            block.filter_reason="invisible"
        elif block.all_text_len ==0  and  len(block.image_node_list)==0:
            block.filter_reason="no text and image"
            block.block_type = BlockType.FILTERED
        elif self.is_crumb(block):
            block.block_type = BlockType.CRUMB
        elif self.is_footerblock(block, all_text_len):
            block.block_type = BlockType.COPYRIGHT
        elif self.is_headerblock(block):
            block.block_type = BlockType.HEADER
        elif self.is_login_block(block):
            block.block_type = BlockType.LOGIN
        elif self.is_recommend_block(block):
            block.block_type = BlockType.HOT_RECOMMEND
        elif self.is_sideblock(block):
            block.block_type = BlockType.RIGHT_OR_LEFT_SIDE
        elif self.is_bannerblock(block):
            block.block_type = BlockType.BANNER
        elif self.is_next_block(block):
            block.block_type = BlockType.NEXTPAGE
        elif self.is_bottomblock(block, body_style):
            block.block_type = BlockType.BOTTOM
        elif self.is_h1title_block(block):
            block.block_type = BlockType.TITLE_H1
        elif self.is_search_block(block):
            block.block_type = BlockType.SEARCH
        elif self.is_user_input_block(block):
            block.block_type = BlockType.USER_INPUT
        elif self.is_nav(block):
            block.block_type = BlockType.NAV
        elif self.is_bbs_userinfo_block(block):
            block.block_type = BlockType.BBS_USER_INFO
        else:
            block.block_type = BlockType.UNKNOWN
        

        
    def get_mainblock_from_list(self, merged_blocks, all_text_len, body_style, h1_tag_count):
        main_block = MainBlock()
        if not merged_blocks:
            return None
        if len(merged_blocks) == 1:
            for block in merged_blocks[0]:
                main_block.blocks.append(block)
                logging.info("wwj debug get_mainblock_from_list return %s", block.all_link_node_list)
            logging.info("wwj debug get_mainblock_from_list return %d", len(main_block.blocks))
            return main_block
        can_main_blocks= []
        for _block_list in merged_blocks:
            can_main_block = MainBlock()
            for _block in _block_list:
                can_main_block.blocks.append(_block)
            can_main_blocks.append(can_main_block)
        
        _dict = {}
        for _main_block in can_main_blocks:
            score = 0
            #对can_main_block 做一些过滤, same to get_main_block_from_first_level
            if _main_block.height < 100:
                continue
            if _main_block.left >1440/2:
                continue
            if _main_block.top >900:
                continue
            
            self.get_block_type(_main_block, all_text_len, body_style)
            if _main_block.block_type == BlockType.TITLE_H1 and h1_tag_count==1:
                _main_block.main_block_score = 5
                _dict[_main_block] = _main_block.main_block_score
            elif _main_block.block_type != BlockType.UNKNOWN:
                _main_block.main_block_score = -2
                _dict[_main_block] = _main_block.main_block_score
            elif _main_block.block_type == BlockType.UNKNOWN:
                _main_block.main_block_score += 0
                for block in _main_block.blocks:
                    _main_block.main_block_score += block.main_block_score
                    logging.info("wwj debug get_mainblock_from_list block score:%f %s %s", block.main_block_score, block.xpath, block.text)
                _dict[_main_block] = _main_block.main_block_score
           
        #如果有多个score相同的候选块，返回宽度最大的那个
        #ugly code 
        keylist = sorted(_dict, key=lambda k: k.width, reverse=True)
        sorted_dict = {}
        for key in keylist:
                logging.info("wwj debug width:%d score:%f height:%d %s", 
                             key.width, _dict[key], key.height, key.text)
                sorted_dict[key] =_dict[key]
        if not sorted_dict:
            return
        can_main_block = max(sorted_dict.iteritems(), key=operator.itemgetter(1))[0]
        logging.info("finally wwj debug get_mainblock_from_list %s %d %f %d %d %d %d", 
                     can_main_block.text, len(can_main_block.all_link_node_list), 
                     can_main_block.links_density(), len(can_main_blocks),
                     can_main_block.height, len(can_main_block.blocks), score)
        return can_main_block
                
            
