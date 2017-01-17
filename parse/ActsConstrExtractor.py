# -*- coding: utf-8 -*-
'''
Created on 2016-12-28

@author: yandong
'''
from entity.Types import *


'ACTS 约束的提取器'
class ActsConstrExtractor(ConstrExtractor):
    def __init__(self,node):
        ConstrExtractor.__init__(self,node)
    
    def getChoiceConditionImp(self,auxVar,known,allDepends,var):
        s = ''
        if len(allDepends) > 0:
            if len(auxVar)==0:
                auxVar.append(0)
            else:
                auxVar.append(auxVar[-1]+1)
            auxStr = 'auxVar'+str(auxVar[-1])
            var.append(auxStr)
            tmps = '&&'.join(allDepends)
            s += '(!(' + tmps + '))' + '|| !' + auxStr+'\n'
            s += '(' + tmps + ')' + '||' + auxStr+'\n' 
        
       
       
        if len(var) > 0:
            s += '||'.join(var) + '\n'
            for v in var:
                for vv in var:
                    if v != vv:
                        tmp = '!' + v + '|| !'+vv+'\n'
                        s += tmp
        if s == '':
            s='\n'
        return s
           
    "默认值约束为空的时候"
    def getEmptyDefaultConditionImp(self,default):
        defaultCondition = '&&'.join(['!(' + d._condition+')' for d in self.node.default if d != default and d._condition is not None])
        if defaultCondition != "":
            defaultCondition = '(' + defaultCondition + ')'
        return defaultCondition
    
    "depends on 依赖"
    def getDependConditionImp(self,depend,known):
        if depend == '':
            return ''
        nType = self.node.dataType
        #BOOL和TRISTATE我们认为是一样的
        if nType == ENUM_TYPE_BOOL  or nType== ENUM_TYPE_TRISTATE:
            if depend in known:
                return ""
            return '(' + depend + ') || !'+self.node.var+"\n"
        elif nType ==ENUM_TYPE_STRING:
            if depend in known:
                return ""
            return '(' + depend + ') || (' + self.node.var + '==' +str(self.getInvalidValue(nType)) + ')\n'
        elif nType ==ENUM_TYPE_INT or nType == ENUM_TYPE_HEX:
            if depend in known:
                s = ''
            else:
                s = '(' + depend + ') || (' + self.node.var + '==' +str(self.getInvalidValue(nType)) + ')\n'
            if self.node.range is not None:
                iv = self.getInvalidValue(nType)
                #print self.range
                if iv >= self.node.range[0] and iv <=self.node.range[1]:
                    return s
                else:
                    s += '(!(' + depend + '))|| ' + '!(' +self.node.var+'==' + str(iv)+')\n'  
            return s
                
        else:
            return ""
    
    "select约束"    
    def getSelectConditionImp(self):
        #添加select约束
        s = ''
        for select in self.node.select:
            if select._condition == None:
                s += '!' + self.node.var + '||'+ select._name+'\n'
            else:
                s += '!' + self.node.var +'|| !(' + self.parseCondition(select._condition)+') ||'+select._name+'\n'
        return s

    "int类型的range约束"
    def getIntRangeConditionImp(self):
        s = ''
        s +=self.node.var + '>=' + str(self.node.range[0]) + '\n'
        s += self.node.var + '<=' + str(self.node.range[1]) + '\n'
        return s
    
    '默认值约束'
    def getDefaultCondition(self,depend_str,ns):
        dType = self.node.dataType
        ret = ''
        for d in self.node.default:
            if d._name == 'y':
                dv = 'true'
            elif d._name == 'n':
                dv = 'false'
            else:
                dv = d._name
                if dType == ENUM_TYPE_HEX:
                    dv = str(int(d._name.strip('"'),16))
            defaultCondition = self.parseCondition(d._condition)
            if defaultCondition != "":
                defaultCondition = '(' + defaultCondition + ')'
            else:
                defaultCondition = self.getEmptyDefaultConditionImp(d)
                
            conditions = []
            if defaultCondition != "":
                conditions.append(defaultCondition)
            if ns != "":
                conditions.append(ns)
            if depend_str != "":
                conditions.append(depend_str)
            
            allDepends = "&&".join(conditions)
            
            if allDepends == "":
                if self.node.dataType == ENUM_TYPE_BOOL:
                    if dv == 'true':
                        ret += self.node.var + '\n'
                    else:
                        ret += '!' + self.node.var + '\n'
                else:
                    ret += self.node.var + '==' + dv + '\n'
            else:
                ret += '(!(' + allDepends + ")) || "
                if self.node.dataType == ENUM_TYPE_BOOL:
                    if dv == 'true':
                        ret += self.node.var + '\n'
                    else:
                        ret += '!' + self.node.var + '\n'
                else:
                    ret += self.node.var + '==' + dv  +'\n'
#             if ns != '':
#                 c1 = '(' + ns +  ('&&' if defaultCondition!='' else '')+ defaultCondition+('&&' if depend_str!='' else '')+ depend_str +') ->' + self.node.var + '==' + dv  +';\n' 
#             else:
#                 c1 = '(' + defaultCondition+('&&' if depend_str!='' else '')+ depend_str +') ->' + self.node.var + '==' + dv  +';\n' 
#             ret += c1
        return ret
    "总控接口，得到当前节点所有的约束"
    def getConditionImp(self,known,rd_dict,condition_dict=None):

        s = ''
       
        
        #对 int 型 range 关键字添加约束
        if self.node.dataType == ENUM_TYPE_INT and self.node.range is not None:
            s += self.getIntRangeConditionImp()
        
        
        #添加select约束
        s += self.getSelectConditionImp()
        
        #添加depends约束
        depend_s = ''
        allDepends = self.getAllDepends()
        for depend in allDepends:
            depend_s += self.getDependConditionImp(depend,known)
            
        
        depend_str = '&&'.join(allDepends)
        if depend_str != "":
            depend_str = '(' + depend_str + ')'
        #不可见变量需要特殊处理
        if self.node.visible == False:
            
            ns = ''

            #如果当前的值可以被select
            if self.node.var in rd_dict:
                for v in rd_dict[self.node.var]:
                    if ns == '':
                        ns += '!' + v
                    else:
                        ns += '&& !' + v
                if ns != '':
                    ns = '(' + ns + ')'
                dType = self.node.dataType
                #只有当select变量无效时，depend约束才成立
                for d in allDepends:
                    if ns == '' and d == '':
                        continue
                    #s += self.getDependConditionImp('(' + ns + ('' if d=='' else '&& ') + d + ')', known)
                    s += self.getDependConditionImp('!' + '(' + ns + ('' if d=='' else '&& !') + d + ')', known)
                #此时要控制其所有的取值
                
                
                if self.node.default is not None:
                    s += self.getDefaultCondition(depend_str, ns)

            #不可以被select的话
            else:

                dType =  self.node.dataType
                #depend生效是无条件的
                for d in allDepends:
                    s += self.getDependConditionImp(d, known)
                #控制其所有的取值
                if len(self.node.default) <= 0:
                    s += self.node.var + '==' + str(self.getInvalidValue(dType))+'\n'
                else:   
                    s += self.getDefaultCondition(depend_str, '')
            return s     
        
       
        s += depend_s        
        
        if self.node.dataType == ENUM_TYPE_INT or self.node.dataType == ENUM_TYPE_STRING or self.node.dataType == ENUM_TYPE_HEX:
            if depend_str == "":
                s+= self.node.var + "!=" + str(self.getInvalidValue(self.node.dataType)) + '\n'
            else:
                s += depend_str + '=>' + self.node.var + "!=" + str(self.getInvalidValue(self.node.dataType)) + '\n'
                
                            
        
        #如果一个int类型变量约束为空，那么它将取一个合法的默认值，那么就不能取无效值
        #但是如果默认值等于无效值的情况下
#         if len(tmpdepends) == 0:
#             if self.node.dataType == ENUM_TYPE_INT:
#                 iv = self.getInvalidValue(ENUM_TYPE_INT)
#                 if self.node.range is not None and type(self.node.range[0]) == type(1) and type(self.node.range[1]) == type(1) and iv >= self.node.range[0] and iv <= self.node.range[1]:
#                     pass
#                 else:
#                     if len(self.node.default) < 1:
#                         pass
#                     elif len(self.node.default) == 1 and self.node.default[0]._name == str(iv):
#                         pass
#                     else:
#                         s += self.node.var + '!=' + str(iv) + '\n'
#                     
#         
#         #只有当string或者int类型才关心default约束
#         if self.node.dataType == ENUM_TYPE_STRING:
#             #如果当前string没有依赖约束，而且又有默认值，那么当前值就不能取无效值
#             if len(tmpdepends) == 0 and len(self.node.default) > 0:
#                 found = False
#                 iv = self.getInvalidValue(self.node.dataType)
#                 for default in self.node.default:
#                     if iv == default._name:
#                         found = True
#                         break
#                 if found == False:
#                     s += self.node.var + '!=' + str(iv) + '\n'
# 
#             for default in self.node.default:
#                 s += self.getDefaultCondition(depend_str, '')
                    
        return s

if __name__ == '__main__':
    pass