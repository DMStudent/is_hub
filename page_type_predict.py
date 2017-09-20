import logging
from libsvm.svmutil import svm_load_model, svm_predict
class PageTypePredictor(object):
    def __init__(self, model_file):
        self.model = None
        self.svm_model_file = model_file
        self.load_model()
        
    def load_model(self):
        self.model = svm_load_model(self.svm_model_file)  
          
    def _predict(self, line):
        if not self.model:
            logging.info("model is None")
            return None 
        prob_y = []
        prob_x = []
        line = line.split(None, 1)
        # In case an instance with all zero features
        if len(line) == 1: line += ['']
        label, features = line
        xi = {}
        for e in features.split():
            #logging.info("e %s",e)
            ind, val = e.split(":")
            xi[int(ind)] = float(val)
        prob_y += [float(label)]
        prob_x += [xi]
        pred_labels, (ACC, MSE, SCC), pred_values = svm_predict(prob_y,prob_x,self.model)
        return pred_labels[0]
    
