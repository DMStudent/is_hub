
class PC(object):

    def __init__(self,url, \
                 mainblock_link_tags_density  = 0, \
                 mainblock_links_density = 0, \
                 mainblock_useful_link_tags_density = 0, \
                 mainblock_useful_links_density = 0, 
                 mainblock_useful_links_count = 0, 
                 mainblock_image_links_count = 0 ,
                 mainblock_pos_distance = 0,
                 mainblock_height_difference = 0, 
                 mainblock_first_top_ratio = 0,
                 mainblock_end_top_ratio = 0,
                 mainblock_link_area_cov = 0):
        self.url = url
        '''hub page +1 && detail page -1'''
        self.default_label = "+1"  
        self.mainblock_link_tags_density = mainblock_link_tags_density
        self.mainblock_links_density = mainblock_links_density
        self.mainblock_height_difference = mainblock_height_difference
        self.mainblock_useful_link_tags_density = mainblock_useful_link_tags_density
        self.mainblock_useful_links_count = mainblock_useful_links_count
        self.mainblock_useful_links_density = mainblock_useful_links_density 
        self.mainblock_first_top_ratio = mainblock_first_top_ratio
        self.mainblock_end_top_ratio = mainblock_end_top_ratio
        self.mainblock_pos_distance = mainblock_pos_distance
        self.mainblock_link_area_cov = mainblock_link_area_cov

        
        
    def normalize(self):
        self.mainblock_link_tags_density = self.mainblock_link_tags_density
        self.mainblock_links_density = self.mainblock_links_density
        self.mainblock_useful_links_density = self.mainblock_useful_links_density 
        self.mainblock_useful_links_count = self.mainblock_useful_links_count*1.000/100
        
    def tostring(self):                
        _pc_str= self.default_label + \
                " 1:" + str(self.mainblock_useful_links_density) +\
                " 2:" + str(self.mainblock_pos_distance) + \
                " 3:" + str(self.mainblock_height_difference) +\
                " 4:" + str(self.mainblock_first_top_ratio) +\
                " 5:" + str(self.mainblock_end_top_ratio) +\
                " 6:" + str(self.mainblock_link_area_cov)
        return _pc_str
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
                