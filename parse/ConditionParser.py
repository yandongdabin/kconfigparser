# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 10:19:31 2015

@author: yandong

条件解析模块，主要完成的是将条件语句转化为一颗AST树，然后在节点上面进行处理，进而得到cascade所需输入条件
"""
import re
from entity.Stack import Stack


#height > 3
height = 3
width = 6
class Node(object):
    def __init__(self,name,value):
        self.__name = name
        self.__value = value
        self.__level = -1
        self.__parent = None
        self.__children = []
    def setLevel(self,level):
        self.__level = level
    def getLevel(self):
        return self.__level
    def addChild(self,child):
        self.__children.append(child)
    def printNode(self):
        print 'name:%s  value:%s  level:%d' %(self.__name,self.__value,self.__level)
    def getValue(self):
        return self.__value
    def setValue(self,value):
        self.__value = value
    def getChildren(self):
        return self.__children
    def getName(self):
        return self.__name
    def setParent(self,parent):
        self.__parent = parent
    def getParent(self):
        return self.__parent
    def setChildren(self,children):
        self.__children = children
class ConditionParser(object):
    def __init__(self,condition):
        self.condition = condition
    def parse(self):
        
        ptn1 = '\s*([\.\w\d_@-]+)\s*'
        ptn2 = '\s*([\.\w\d_@-]+)\s*(!=|==)\s*([""\\\\\.\w\d_@-]+)\s*'
        
        nodeStack = Stack()
        root = Node('root','')
        root.setLevel(0)
        nodeStack.push(root)
        i = 0
        #统计！后面的括号的匹配数，如果为 0 且 isFirst = False 那么说明 ！的作用域结束 ！（（）（））
        notBrackEffect = 0
        #后面是否跟有 (
        followBrack = False
        #是否处在 !的作用域内
        isNot = False
        #是否是紧跟在！后面   还可以表示！后面没有括号而是紧跟着一个变量 ！X
        isFirst = True
        while i < len(self.condition):
            ch = self.condition[i]
            #print i
            #print ch
            #print ch
            m2 = re.match(ptn2,self.condition[i:])
            m1 = re.match(ptn1,self.condition[i:])
            
            #!的作用域结束
            if (isNot and followBrack == False and isFirst == False) or (isNot and followBrack and notBrackEffect==0 and isFirst == False):
                isNot = False
                nodeStack.pop()
            if ch == ' ' or ch == '\t':
                i += 1
                continue
            if ch == '(':
                node = Node('LBRACKET','(')
                nodeStack.peek().addChild(node)
                node.setParent(nodeStack.peek())
                node.setLevel(nodeStack.peek().getLevel() + 1)
                nodeStack.push(node)
                i += 1
                if isNot:
                    notBrackEffect += 1
                    isFirst = False
            elif ch == ')':
                node = Node('RBRACKET',')')
                nodeStack.pop()
                nodeStack.peek().addChild(node)
                node.setParent(nodeStack.peek())
                node.setLevel(nodeStack.peek().getLevel() + 1)
                i += 1
                if isNot:
                    notBrackEffect -= 1
            elif ch == '!':
                node = Node('NOT','!')
                nodeStack.peek().addChild(node)
                node.setLevel(nodeStack.peek().getLevel() + 1)
                node.setParent(nodeStack.peek())
                nodeStack.push(node)
                notBrackEffect = 0
                if self.condition[i+1] == '(':
                    followBrack = True
                isNot = True
                isFirst = True
                i += 1
            elif self.condition[i:i+2] == '&&' or self.condition[i:i+2] =='||':
                expr = 'CONJ' if self.condition[i:i+2] == '&&' else 'DISJ'
                node = Node(expr,self.condition[i:i+2])
                #node.printNode()
                node.setLevel(nodeStack.peek().getLevel() + 1)
                nodeStack.peek().addChild(node)
                node.setParent(nodeStack.peek())
                i += 2
            elif m2 is not None:
                value = m2.group().strip()
                if m2.group(2) == "!=":
                    value = "!(" + value.replace("!=","==") +")"
                    
                node = Node('EXPRESSION',value)
                node.setLevel(nodeStack.peek().getLevel() + 1)
                nodeStack.peek().addChild(node)
                node.setParent(nodeStack.peek())
                i+=len(m2.group())
                if isNot:
                    isFirst = False
                
            elif m1 is not None:
                node = Node('VARIABLE',m1.group().strip())
                node.setLevel(nodeStack.peek().getLevel() + 1)
                nodeStack.peek().addChild(node)
                node.setParent(nodeStack.peek())
                #node.printNode()
                i+=len(m1.group())
                if isNot:
                    isFirst = False
            else:
                i += 1
        return root
    #先序遍历AST生成树
    def restoreCondition(self,root,s):
        #tmp = s        
        s += root.getValue()
        for child in root.getChildren():
            s = self.restoreCondition(child,s)
        return s
        
    def printTree(self,root):
        root.printNode()
        for child in root.getChildren():
            self.printTree(child)
    def reduceCondition(self,root):
        
        pass
    def convertTree(self,root):
        if root.getName() == 'VARIABLE':
            if root.getParent().getName()!='NOT':
                root.setValue(root.getValue() + '=="y"')
            else:
                root.setValue(root.getValue() + '=="n"')
        for child in root.getChildren():
            self.convertTree(child)
    def delBracketEngine(self,node):
        self.printTree(node)
        print '--------------'
        change = self.delBracket(node)
        self.printTree(node)
        print self.restoreCondition(node,'')
        print '--------------'
        while change:
            change = self.delBracket(node)
            self.printTree(node)
            print self.restoreCondition(node,'')
            print '--------------'
                    
    def delBracket(self,node):
        change = False
        for child in node.getChildren():
            if self.delBracket(child):
                return True
        if node.getName() == 'NOT' and node.getChildren()[0].getName() == 'LBRACKET':
            children = []
            for child in node.getChildren()[0].getChildren():
                if child.getName() == "LBRACKET":
                    newnode = Node('NOT',"!")
                    newnode.setLevel(node.getLevel())
                    newLbracket = Node("LBRACKET","(")
                    newLbracket.setParent(newnode)
                    newLbracket.setLevel(newnode.getLevel() + 1)
                    newnode.addChild(newLbracket)
                    for c in child.getChildren():
                        c.setLevel(newLbracket.getLevel() + 1)
                        newLbracket.addChild(c)
                        c.setParent(newLbracket)
                    newRbracket = Node("RBRACKET",")")
                    newRbracket.setParent(newnode)
                    newRbracket.setLevel(newnode.getLevel() + 1)
                    newnode.addChild(newRbracket)
                    newnode.setParent(node.getParent())
                    children.append(newnode)
                    change = True
                if child.getName() == "VARIABLE" or child.getName() == "EXPRESSION":
                    if child.getValue()[0] == "!":
                        children.append(Node("VARIABLE",child.getValue()[1:]))
                    else:
                        children.append(Node("VARIABLE","!" + child.getValue()))
                elif child.getName() == "CONJ":
                    children.append(Node("DISJ",'||'))
                elif child.getName() == "DISJ":
                    children.append(Node("CONJ","&&"))
                
            newchildren = children + node.getChildren()[2:]
            for child in newchildren:
                child.setParent(node.getParent())
                child.setLevel(node.getLevel())
            idx = 0
            for c in node.getParent().getChildren():
                if c == node:
                    break
                idx += 1
            node.getParent().setChildren(newchildren + node.getParent().getChildren()[:idx] +node.getParent().getChildren()[idx+1:])       
           
        elif node.getName() == 'NOT' and node.getChildren()[0].getName() == 'VARIABLE':
            value = node.getChildren()[0].getValue()
            
            if value[0] == '!':
                node.getParent().setChildren([Node('VARIABLE',value[1:])])
            else:
                node.getParent().setChildren([Node('VARIABLE','!' + value)])
        return change            
#     def delBracket_Util(self,node):
#         for child in node.getChildren():
#             self.delBracket_Util(node)
#         if node.getName() == 'NOT' and node.getChildren()[0].getName() == 'LBRACKET':
#             children = []
#             for child in node.getChildren()[0].getChildren():
#                 if child.getName() == "LBRACKET":
#                     newnode = Node('NOT',"!")
#                     for c in child.getChildren():
#                         newnode.addChild(c)
#                         c.parent = newnode
#                     children.append(newnode)
#                 elif child.getName() == "VARIABLE" or child.getName() == "EXPRESSION":
#                     if child.getValue()[0] == "!":
#                         children.append(Node("VARIABLE",child.getValue()[1:]))
#                     else:
#                         children.append(Node("VARIABLE","!" + child.getValue()))
#                 elif child.getName() == "CONJ":
#                         children.append(Node("DISJ",'||'))
#                 elif child.getName() == "DISJ":
#                         children.append(Node("CONJ","&&"))
#                 else:
#                     children.append(child) 
                
        
    def start(self):
        root = self.parse()
        self.delBracketEngine(root)
        #self.convertTree(root)
        return self.restoreCondition(root,'')
#         return self.condition        
if __name__ == '__main__':
#    s = ' PACKAGE_wpad !=y1231321'
#    ptn = '\s*([\w\d_@]+)\s*'
#    m = re.match(ptn,s)
#    if m is not None:
#        print len(m.group())
    
    ss = '!((TARGET_brcm2708||TARGET_at91||TARGET_brcm63xx == 1||TARGET_mxs||TARGET_imx6))'
    s = 'm || (PACKAGE_wpad != y)'
    sss = '!(!(a!=1 && b))'
    ssss = '(!((V1 || V2)&&(V3&&V3))) || V4=="V5"'
    cp = ConditionParser(ssss)
    root = cp.parse()
#     cp.printTree(root)
    print cp.start()
    #cp.test()
    
                