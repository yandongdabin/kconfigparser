# -*- coding: utf-8 -*-
'''
Created on 2016-12-26

@author: yandong
'''
from entity.Types import *
from ConditionParser import ConditionParser


'Cascade 约束的提取器'
class CasaConstrExtractor(ConstrExtractor):
    def __init__(self,node,varEncode):
        ConstrExtractor.__init__(self,node)
        self.varEncode = varEncode
    def transform(self,constrStr):
        cp = ConditionParser(constrStr)
        root = cp.parse()
        
        


if __name__ == '__main__':
    constrStr = '(CONFIG_CSHARP_BINDINGS || CONFIG_VBNET_BINDINGS) || (CONFIG_DOT_NET_FRAMEWORK_BASE=="")'
    cce = CasaConstrExtractor(None,None)
    cce.transform(constrStr)