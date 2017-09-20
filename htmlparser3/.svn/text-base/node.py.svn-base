import logging
import json

class Node(object):
    def __init__(self, paragraph):
        self.paragraph = paragraph
        self.my_style = None
    
    def set_style(self, style_str):
        if style_str:
            try:
                '''{'y':50,'x:'0,'cssText':''}'''
                #json_str = json.loads(style_str) # need double quote
                json_str = style_str.replace("'","\"")
                self.my_style = json.loads(json_str)
            except Exception, e:
                logging.info("wuwenjun debug set style error %s %s %s", type(style_str), style_str, str(e))
    
    def get_style(self):
        return self.my_style