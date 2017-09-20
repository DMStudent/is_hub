'''
Created on Apr 7, 2016

@author: wuwenjun
'''

class Page(object):
    def __init__(self, url, response_headers):
        self.url = url
        self.response_headers = response_headers
        