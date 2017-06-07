# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 09:30:47 2015

@author: yandong

用于条件的简化 包括图的构建与聚类
"""
from Queue import Queue
import re, os
import sys

from entity.Stack import Stack
from entity.Types import *

class Node(object):
    def __init__(self,value,firstArc):
        self.value = value
        self.firstArc = firstArc
    def __eq__(self,obj):
        return self.value == obj.value
    def __ne__(self,obj):
        return self.value != obj.value
class Edge(object):
    def __init__(self,nodeIndex,nextArc):
        self.nodeIndex = nodeIndex
        self.nextArc = nextArc
class SimpleCondition(object):
    def __init__(self):
        #self.filePath = filePath
        self.times = 0
        self.low = {}
        self.dfn = {}
        self.stack = Stack()
        self.dfsStack = Stack()
        self.visited = []
        
    def addNode(self,nodevar,nodeList,nodeId,currentId,debug1):
        if nodevar == '':
            return
        if nodevar not in nodeId:
            nodeId[nodevar] = currentId[0] + 1
            currentId[0] += 1
            debug1[nodevar] = 1
        if nodevar not in nodeList:
            nodeList[nodevar] = Node(nodevar,None)
#             nodeList[nodevar] = Node(nodevar,None)
    def addEdge(self,nodeList,edgevar,nodevar,currentId,nodeId,edgeId,debug1):
        if nodevar not in nodeId:
            self.addNode(nodevar,nodeList,nodeId,currentId,debug1)
        if edgevar not in nodeId:
            self.addNode(edgevar,nodeList,nodeId,currentId,debug1)
        tmp = str(nodeId[nodevar]) + ' ' + str(nodeId[edgevar])
        if tmp not in edgeId:
            edgeId[tmp] = 0 
        newArc = Edge(edgevar,None)
        if nodeList[nodevar].firstArc is None:
            nodeList[nodevar].firstArc = newArc
        else:
            newArc.nextArc = nodeList[nodevar].firstArc
            nodeList[nodevar].firstArc = newArc
    def addCnt(self, ret_graph, key1, key2):
        if key1 not in ret_graph:
            ret_graph[key1] = {}
        if key2 not in ret_graph:
            ret_graph[key2] = {}    
        if key2 not in ret_graph[key1]:
            ret_graph[key1][key2] = 0
        if key1 not in ret_graph[key2]:
            ret_graph[key2][key1] = 0
        ret_graph[key1][key2] += 1
        ret_graph[key2][key1] += 1
        
    def getSimilarity(self, root):
        queue = Queue()
        for child in root.children:
            queue.put(child)
        ret_graph = {}
        while not queue.empty():
            node = queue.get()
            for child in node.children:
                queue.put(child)
                
            if node.nodeType == ENUM_MENU:
                continue
            if node.nodeType == ENUM_CHOICE:
                nodevar = []
                for child in node.children:
                    nodevar.append(child.var)
                        
                for var in nodevar:
                    for var1 in nodevar:
                        if var != var1:
                            self.addCnt(ret_graph, var, var1)
                
                            
            if node.nodeType == ENUM_CONFIG or node.nodeType == ENUM_MENUCONFIG:
                pType =  node.parent.nodeType
                if pType == ENUM_MENU or pType == ENUM_CHOICE:
                    for depend in node.parent.depends:
                        variables = self.getVarFromCondition(depend)
                         
                        for var in variables:
                            self.addCnt(ret_graph, var, node.var)
                elif pType == ENUM_MENUCONFIG:
#                     print node.parent.var
#                     print node.var
                    self.addCnt(ret_graph, node.parent.var)
                 
            if node.nodeType == ENUM_CONFIG or node.nodeType == ENUM_MENUCONFIG:
                for depend in node.depends:
                    variables = self.getVarFromCondition(depend)
                    for var in variables:
                        self.addCnt(ret_graph, var, node.var)
                for default in node.default:
                    if default._condition is not None:
                        variables = self.getVarFromCondition(default._condition)
                        for var in variables:
                            self.addCnt(ret_graph, var, node.var)
            #处理select依赖 select->node && condition
            for s in node.select:
                variables = self.getVarFromCondition(s._condition)
                variables.append(node.var)
                for var in variables:
                    self.addCnt(ret_graph, var, node.var)
        keys = ret_graph.keys()
        ret = []
        for key in keys:
            cur = []
            for in_key in keys:
                if in_key == key:
                    cur.append(1)
                else:
                    cur.append(ret_graph[key][in_key])
            ret.append(cur)
        return (keys, ret)    
    
    #用邻接表数据结构构建依赖图
    def buildGraph(self,root):
        currentId = [0,]
        nodeId = {}
        nodeList = {}
        edgeId = {}
        queue = Queue()
        
        debug1 = {}
        debug2 = {}
        for child in root.children:
            queue.put(child)
        cnt = 0
        while not queue.empty():
            node = queue.get()
            for child in node.children:
                queue.put(child)

                
            if node.nodeType == ENUM_MENU:
                continue
            if node.nodeType == ENUM_CHOICE:
                nodevar = []
                for child in node.children:
                    nodevar.append(child.var)
                        
                for var in nodevar:
                    for var1 in nodevar:
                        if var != var1:
                            self.addEdge(nodeList, var1, var,currentId,nodeId,edgeId,debug1)   
                
                            
            if node.nodeType == ENUM_CONFIG or node.nodeType == ENUM_MENUCONFIG:
                pType =  node.parent.nodeType
                if pType == ENUM_MENU or pType == ENUM_CHOICE:
                    for depend in node.parent.depends:
                        variables = self.getVarFromCondition(depend)
                         
                        for var in variables:
                            self.addEdge(nodeList, var, node.var,currentId,nodeId,edgeId,debug1)
                            self.addEdge(nodeList, node.var,var,currentId,nodeId,edgeId,debug1)
                elif pType == ENUM_MENUCONFIG:
#                     print node.parent.var
#                     print node.var
                    self.addEdge(nodeList, node.parent.var, node.var,currentId,nodeId,edgeId,debug1)
                    self.addEdge(nodeList, node.var, node.parent.var,currentId,nodeId,edgeId,debug1)
                 
            if node.nodeType == ENUM_CONFIG or node.nodeType == ENUM_MENUCONFIG:
                self.addNode(node.var,nodeList,nodeId, currentId,debug1)
                debug2[node.var] = 1
                cnt+=1
            if node.nodeType == ENUM_CONFIG or node.nodeType == ENUM_MENUCONFIG:
                for depend in node.depends:
                    variables = self.getVarFromCondition(depend)
                    for var in variables:
                        self.addEdge(nodeList, var, node.var,currentId,nodeId,edgeId,debug1)
                        self.addEdge(nodeList, node.var,var,currentId,nodeId,edgeId,debug1)
                for default in node.default:
                    if default._condition is not None:
                        variables = self.getVarFromCondition(default._condition)
                        for var in variables:
                            self.addEdge(nodeList, var, node.var,currentId,nodeId,edgeId,debug1)
                            self.addEdge(nodeList, node.var,var,currentId,nodeId,edgeId,debug1)
            #处理select依赖 select->node && condition
            for s in node.select:
                variables = self.getVarFromCondition(s._condition)
                variables.append(node.var)
                for var in variables:
                    self.addEdge(nodeList, var, s._name,currentId,nodeId,edgeId,debug1)
                    self.addEdge(nodeList, s._name, var,currentId,nodeId,edgeId,debug1)

        for d in debug1:
            if d not in debug2:
                print d
        print 'node count:%d' %len(nodeList)
        print 'edge count:%d' %len(edgeId)
        print cnt
        self.printGraphXml(nodeId, currentId, edgeId)
        return nodeList
    def printGraphXml(self,nodeId,currentId,edgeId):
        fd = os.open('test.gexf',os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        stdout = os.dup(1)
        os.dup2(fd,1)
        print '''<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns:viz="http:///www.gexf.net/1.1draft/viz" version="1.1" xmlns="http://www.gexf.net/1.1draft">
<meta lastmodifieddate="2010-03-03+23:44">
<creator>Gephi 0.7</creator>
</meta>
<graph defaultedgetype="undirected" idtype="string" type="static">'''
        print '<nodes count="%d">' %(currentId[0])
        for n in nodeId:
            print '<node id="%d" label="%s"/>' %(nodeId[n],n)
        print '</nodes>'
        print '<edges count="%d">' %len(edgeId)
        tmpId = 1
        for i in edgeId:
            ss = i.split()
            print '<edge id="%d" source="%d" target="%d"/>' %(tmpId,int(ss[0]),int(ss[1]))
            tmpId += 1
        print '''</edges>
</graph>
</gexf>'''
        sys.stdout.flush()
        os.dup2(stdout,1)
            
            
    def getVarFromCondition(self,condition):
        if condition is None:
            return []
        res = []
        ptn = '([\.\w\d_-]+)'
        ptnEqual = '(([\w\d\s\.-_]+)=([\s\w\d\.-_]+))'
        ptnNotEqual = '(([\w\d\s\.-_]+)!=([\s\w\d\.-_]+))'
        resEq = re.findall(ptnEqual,condition)
        resNEq = re.findall(ptnNotEqual,condition)
        for r in resEq:
            res.append(r[1].strip())
        for r in resNEq:
            res.append(r[1].strip())
        condition = re.subn(ptnEqual,'',condition)[0]
        condition = re.subn(ptnNotEqual,'',condition)[0]
        res += re.findall(ptn,condition)
        return res


if __name__ == "__main__":
    ptn = '(([\w\d\s\.-_]+)=([\s\w\d\.-_]+))'
    s = 'a = 1 ||D|| b = 1 && C'
    sc = SimpleCondition()
    print sc.getVarFromCondition(s)
    print re.findall(ptn,s)
    res= re.subn(ptn,'',s)
    print res
    print sc.getVarFromCondition(res[0])
    
    
                