# -*- coding: utf-8 -*-

"""
定义一些数据结构 
包括节点类型、数据类型、节点类型、关系类型

"""
from __builtin__ import str



'节点变量'
ENUM_MENUCONFIG = 1
ENUM_CONFIG = 2
ENUM_CHOICE = 3
ENUM_MENU = 4
ENUM_IF = 5
ENUM_HELP = 6
ENUM_ROOT = 7

'类型变量'
ENUM_TYPE_BOOL = 1
ENUM_TYPE_TRISTATE = 2
ENUM_TYPE_HEX = 3
ENUM_TYPE_STRING = 4
ENUM_TYPE_INT = 5
ENUM_TYPE_UNDEFIEND = 6


'枚举节点各类取值'
ENUM_VALUES = {ENUM_TYPE_BOOL:["y","n"],ENUM_TYPE_TRISTATE:["y","n","m"]}    
# ENUM_DEFAULT_VALUES = {ENUM_TYPE_HEX:0,ENUM_TYPE_STRING:'""',ENUM_TYPE_INT:0}
ENUM_DEFAULT_VALUES = {}
ENUM_INVALID_TYPE = {ENUM_TYPE_INT:-123,ENUM_TYPE_STRING:'"werwqre"',ENUM_TYPE_HEX:-123,ENUM_TYPE_TRISTATE:"false",ENUM_TYPE_BOOL:"false"}


'辅助将字符串型的类型转化为整数表示'
ENUM_NODETYPES={"menuconfig":ENUM_MENUCONFIG,"config":ENUM_CONFIG,"choice":ENUM_CHOICE,"menu":ENUM_MENU,'if':ENUM_IF,'help':ENUM_HELP,'root':ENUM_ROOT}
ENUM_DTYPES = {'int':ENUM_TYPE_INT,'bool':ENUM_TYPE_BOOL,'tristate':ENUM_TYPE_TRISTATE,'hex':ENUM_TYPE_HEX,'string':ENUM_TYPE_STRING,'undefined':ENUM_TYPE_UNDEFIEND}
ENUM_REV_DTYPES = {ENUM_TYPE_INT:'int',ENUM_TYPE_BOOL:'bool',ENUM_TYPE_TRISTATE:'tristate',ENUM_TYPE_HEX:'hex',ENUM_TYPE_STRING:'string',ENUM_TYPE_UNDEFIEND:'undefined'}



"select以及default的depends关系"
class Relation(object):
    def __init__(self,_type,_name,_condition):
        self._type = _type
        self._name = _name
        self._condition = _condition
    def __str__(self):
        return 'type:%s name:%s condition:%s' %(self._type,self._name,self._condition)
    def __eq__(self,obj):
        return self._name == obj._name and self._condition == self._condition
    
"表示KConfig中一个节点"
class TreeNode(object):
    def __init__(self,parent,node_type,var):
        self.parent = parent
        self.children = []
        self.nodeType = ENUM_NODETYPES[node_type]
        self.level = 0
        self.dataType = ENUM_DTYPES['undefined']
        self.depends = []
        self.select = []
        self.default = []
        self.range = None
#         self.rangeCon = None
        self.var = var
        self.visible = False
    
    #-----------------------
    ####对节点属性的操作####
    #-----------------------
    def setType(self,dataType,value=None):
        self.dataType = ENUM_DTYPES[dataType]
    def getNodeType(self):
        return self.nodeType
    
    
    
    def addChild(self,child):
        self.children.append(child)
    def addSelect(self,select):
        self.select.append(select)
    def addDepend(self,depend):
        self.depends.append(depend)
    def addDefault(self,default):
        self.default.append(default)
        
        
    #-----------------------
    ####     辅助操作         ####
    #-----------------------
    "获取当前节点变量的无效值"
    def getInvalidValueStr(self,dType):
        if dType in ENUM_INVALID_TYPE:
            return str(ENUM_INVALID_TYPE[dType])
    "返回默认值的列表"
    def getDefaultValue(self):
        retList = []
        for default in self.default:  
            if default._name in retList:
                continue       
            if self.dataType == ENUM_TYPE_HEX:
                try:     
                    t = str(int(default._name.strip('"'),16))
                    if t in retList:
                        continue
                    retList.append(t)
                except:
                    pass
            else:
                retList.append(default._name)
#         dValue = str(ENUM_DEFAULT_VALUES[self.dataType])
#         if dValue not in retList:
#             retList.append(dValue)
        
        return retList
    
class ConstrExtractor(object):
    def __init__(self,node):
        self.node = node
        
        '添加一个小补丁'
        if self.node is not None and not self.node.visible:
            if len(self.node.default) <= 0 and self.node.dataType == ENUM_TYPE_BOOL:
                self.node.default.append(Relation('default','n',None))
            if len(self.node.default) == 1 and  self.node.dataType == ENUM_TYPE_BOOL:
                if self.node.default[0]._condition is not None:
                    if self.node.default[0]._name == 'y':
                        self.node.default.append(Relation('default','n',None))
                    else:
                        self.node.default.append(Relation('default','y',None)) 
    
    def parseNegateCondition(self,condition):
       
        tmp = self.parseCondition(condition)
        tmp = '!(' + tmp.strip() + ')'
        return tmp
    def parseCondition(self,condition):
        if condition == None:
            return ""
        return condition
    
    '获得当前节点所有的依赖关系'
    def getAllDepends(self):
        allDepends = []
        #添加父节点的依赖
        if self.node.parent.nodeType == ENUM_MENU or  self.node.parent.nodeType == ENUM_CHOICE:
            for d in self.node.parent.depends:
                allDepends.append(d)
        elif self.node.parent.nodeType == ENUM_MENUCONFIG:
            allDepends.append(self.node.parent.var) 
        for d in self.node.depends:
            allDepends.append(d)
        return allDepends
    '解析choice block块中的多选一的约束关系'
    def getChoiceCondition(self,auxVar,known):
        var = []
    
        #首先得到当前choice block块的所有约束
        allDepends = self.getAllDepends()
        
        for child in self.node.children:
            if child.nodeType!=ENUM_HELP:
                var.append(str(child.var))
        return self.getChoiceConditionImp(auxVar, known,allDepends,var)
    
    def getInvalidValue(self,nType):
        return ENUM_INVALID_TYPE[nType]
    #-----------------------
    ###以下函数在子类中实现  ####
    #-----------------------
    
    
    '得到choice约束'
    def getChoiceConditionImp(self,auxVar,known,allDepends,var):
        return ''
    '得到空条件的default表达式的约束'
    def getEmptyDefaultConditionImp(self,default):
        return ''       
    
    def getDependConditionImp(self,depend,known):
        return ''
        
    def getSelectConditionImp(self):
        return ''
    
    def getIntRangeConditionImp(self):
        return ''

    def getConditionImp(self,known,rd_dict,condition_dict=None):
        pass
        
    def __str__(self):
        s = 'var=%s\nnodeType:%s\ndatatype:%s\nlevel:%s' %(self.var,self.nodeType,self.dataType,self.level)
        for depend in self.depends:
            s += 'depends on: ' + depend + '\n'
        for select in self.select:
            s += str(select) + '\n'
        for default in self.default:
            s += str(default) + '\n'
        
            
        return s
    __repr__ = __str__
    
if __name__ == '__main__':
    s = '(arm || armeb || mips || mipsel || i386 || x86_64) && !TARGET_uml && @KERNEL_SECCOMP'
    ss = '!((TARGET_brcm2708||TARGET_at91||TARGET_brcm63xx||TARGET_mxs||TARGET_imx6))'
    sss = 'm || (PACKAGE_wpad != y)'
    node = TreeNode(None,'config','var')
    
    print ss.split('||')
    #print node.parseCondition(s)
    #print node.parseNegateCondition(ss)