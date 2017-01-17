# -*- coding: utf-8 -*-
'''
Created on 2016��3��28��

@author: yandong
'''

import csv
import Queue

def test(fileName):
    csvfile = csv.reader(file(fileName,'rb'))
    cluster = {}
    threshold = 50
    for line in csvfile:
        if len(line) > 1:
            if line[1] not in  cluster:
                cluster[line[1]] = [line[0]]
            else:
                cluster[line[1]].append(line[0])
    
    cur_cnt = 0
    ct_groups = []
    cur_group = []
    for key in cluster:
        cur_cluster = cluster[key]
        if len(cur_cluster) > threshold:
            ct_groups.append(cur_cluster)
        else:
            if cur_cnt + len(cur_cluster) > threshold:
                cur_group.append(cur_cluster)
                ct_groups.append(cur_group) 
                cur_cnt = 0
                cur_group = []
            else:
                cur_group.append(cur_cluster)
                cur_cnt += len(cur_cluster)
    for g in ct_groups:
        print g    
        
def genVCModel(self,ct_groups,configPath,root):        
    "generate Variable Constraint model"
    for g in ct_groups:
        if len(g) == 1:
            self.subGenVCModel(root,g,configPath,False)
        else:
            self.subGenVCModel(root,g,configPath,True)

def subGenVCModel(self,root,g,configPath,isChangeable):
    'generate variable constraint model with default strength'
    changeFp = open('tmp/change.txt','w')
        
    print '[PARAMETERS]'
   
    if not isChangeable:
        variables = g
    else:
        for subg in g:
            variables += subg
    leftnodes = []    
    queue = Queue.Queue()
    queue.put(root)
    conditions = []
        
    excludeChoice = []
        
    type_dict = {}
    variables_str = []
    while not queue.empty():
        cur = queue.get()
        if cur.var not in type_dict:
            type_dict[cur.var] = (cur,str(cur.dataType).lower())
        cType = cur.getNodeType()
        if cType == 'CHOICE':
            for child in cur.children:
                if child.var in variables and cur not in excludeChoice:
                    conditions.append(cur.getChoiceCondition())
                    excludeChoice.append(cur)
                    break
        if cur.var.strip() in variables:
            leftnodes.append(cur)
                
            dType = cur.dataType
                
                #GET VARIABLES    
            if  cType != 'MENU' and cType != 'CHOICE' and cType != 'HELP':       
                t = str(dType).lower()
                t = self.changeType(t)
                variables_str.append(self.getValueForType(cur, t,changeFp))
                #GET CONDITION
            if cType != 'HELP' and cType!='MENU' and cType!='CHOICE':
                condition = cur.getCondition()
                if condition != '':
                    conditions.append(condition)
            elif cur.getNodeType()=='CHOICE':
                conditions.append(cur.getChoiceCondition())
        for child in cur.children:
            queue.put(child)
         
    condition_var = []
    for c in conditions:
        for t in self.getVarFromCondition(c):
            if t not in condition_var:
                condition_var.append(t)   
        
        #关心的变量
    for s in variables_str:
        print s
    
        #分割的变量 或者是choice条件引入的变量
    for v in condition_var:
        if v!='UNDEFINED' and v not in variables:
            node,t = type_dict[v]
            t = self.changeType(t)
            print self.getValueForType(node, t,changeFp)
                
         
             
    print '[STRENGTHS]'
    if not isChangeable:
        print 'default: 3;'
    else:
        print 'default: 1;'
        for subg in g:
            cstrength = ''
            for ssg in subg:
                if(cstrength == ''):
                    cstrength += ssg
                else:
                    cstrength += ',' + ssg;
            cstrength += ' :2;'
            print cstrength
    print '[CONSTRAINTS]'
    for c in conditions:
        c = c.replace('-','_')
        c = c.replace('_1','-1')
        print c,
    defaultValue = self.getConfigDefaultValues(configPath)
    for v in condition_var:
            #得到分割变量
        old = v
        if v!='UNDEFINED' and v not in variables:
            if '-' in v:
                v = v.replace('-','_')
                   
                changeFp.write(v + '\t' + old + '\n')
            node,t = type_dict[old]
            t = self.changeType(t)
                #如果分割变量在默认配置文件中未定义
            if old not in defaultValue:
                print v+"==" + self.getInvalidValue(node,t)+';'
                
            else:
                value = ''
                if t == 'bool':
                    if defaultValue[old] == 'y':
                        value = 'true'
                    else:
                        value = 'false'
                else:
                    value = defaultValue[old]
                print v+'==' +value+";"
                
    print '[SEEDS]'
    changeFp.close()   
            
if __name__ == '__main__':
    test('busybox_node.csv')