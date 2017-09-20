import logging
class TreeNode(object):
    def __init__(self):
        self.father = None
        self.firstchild = None
        self.nextsibling = None

def done_nothing(self):
    pass
 
class Tree(object):
    def __init__(self, name):
        # list of TreeNode
        self._elements = []
        self.root = None
        self.level_elements=[]
        self.levels = 0
        self.name = name

    def append(self, node):
        self.node = node
        father = self._get_father()
        node.father = father
        if father is None:
            self.root = node
            self._elements.append(node)
            return
        if father.firstchild is None:
            father.firstchild = node
        else:
            #logging.info("begin add to brother %s %s", node.xpath, father.firstchild.xpath)
            self._add_to_younger_brother(node)
        self._elements.append(node)
        #if self.name == "BLOCK":
        #    logging.info("APPEND NODE %s %d", node.xpath, self.getLevels(self.root))
        return self
    
    def _get_father(self):
        if not self._elements:
            return None
        #logging.info("wwj debug in get_father %s father:%s", self.node.xpath, self._elements[-1].xpath)
        return self._elements[-1]
    
    def _add_to_younger_brother(self, block):
        if not self._elements:
            return None
        big_brother = self._elements[-1].firstchild
        if big_brother is None:
            return
        young_brother = big_brother.nextsibling
        if young_brother is None:
            #logging.info("add to brother big %s %s", big_brother.xpath, block.xpath)
            big_brother.nextsibling = block
            return
        tmp = None
        while not (young_brother is None):
        #while young_brother:
            tmp = young_brother
            young_brother = young_brother.nextsibling
        #logging.info("add to brother young %s %s", tmp.xpath ,block.xpath)
        tmp.nextsibling = block
    
    def pop(self):
        _node = self._elements.pop()
        #logging.info("POP BLOCK %s", _node.xpath)
        return _node
    
    def top(self):
        if not self._elements:
            return None
        _node = self._elements[-1]
        return _node
    
    def inorder(self, root, handler = done_nothing):
        if root==None:
            return False
        self.inorder(root.firstchild, handler)
        handler(root)
        self.inorder(root.nextsibling, handler)
    
    def getLevels(self,root):
        if root==None:
            return 0
        first_child_level = self.getLevels(root.firstchild)
        child_brother = None
        other_child_level = 0
        if root.firstchild is not None:
            child_brother = root.firstchild.nextsibling
        while child_brother is not None:
            level = self.getLevels(child_brother)
            if level>other_child_level:
                other_child_level = level
            child_brother = child_brother.nextsibling
        return 1+max(first_child_level, other_child_level)
    
    def add_next_level(self, level):
        for ele in self.level_elements[level]:
            if ele.firstchild is None:
                continue
            else:
                self.level_elements[level+1].append(ele.firstchild)
                brother =ele.firstchild.nextsibling
                while brother is not None:
                    self.level_elements[level+1].append(brother)
                    brother = brother.nextsibling
                
            
    def build_level_nodes(self):
        if self.root is None:
            return
        self.levels=self.getLevels(self.root)
        logging.info("In build_level_nodes get levels %d",self.levels)
        self.level_elements=[[] for i in xrange(self.levels)]
        self.level_elements[0].append(self.root)
        for level in xrange(self.levels-1):
            self.add_next_level(level)
            

            
            
            
            
        
            
            
