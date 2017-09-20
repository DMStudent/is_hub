import logging
class TreeNode(object):
    def __init__(self):
        self.father = None
        self.firstchild = None
        self.nextsibling = None

def done_nothing(self):
    pass
 
class Tree(object):
    def __init__(self):
        # list of TreeNode
        self._elements = []
        self.root = None

    def append(self, node):
        self.node = node
        father = self._get_father()
        node.father = father
        if father is None:
            self.root = node
            self._elements.append(node)
            return
        if not father.firstchild:
            logging.info("father first child %s",node.xpath)
            father.firstchild = node
        else:
            logging.info("begin add to brother %s", node.xpath)
            self._add_to_younger_brother(node)
        self._elements.append(node)
        return self
    
    def _get_father(self):
        if not self._elements:
            return None
        logging.info("wwj debug in get_father %s %s", self.node.xpath, self._elements[-1].xpath)
        return self._elements[-1]
    
    def _add_to_younger_brother(self, block):
        if not self._elements:
            return None
        big_brother = self._elements[-1].firstchild
        logging.info("##############%s", big_brother)
        if big_brother is None:
            return
        young_brother = big_brother.nextsibling
        if not young_brother:
            logging.info("add to brother %s", big_brother.xpath)
            big_brother.nextsibling = block
            return
        young_brother = big_brother.nextsibling
        tmp = None
        while young_brother:
            tmp = young_brother
            young_brother = young_brother.nextsibling
        logging.info("add to brother %s", tmp)
        tmp.nextsibling = block
    
    def pop(self):
        _node = self._elements.pop()
        logging.info("POP BLOCK %s", _node.xpath)
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