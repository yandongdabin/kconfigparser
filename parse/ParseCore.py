# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 08:57:44 2015

@author: yandong
Kconfig文件解析引擎 主要完成的功能就是把Kconfig文件解析为一颗树，树的节点包含这Kconfig的有用信息
"""
import re
from entity.Stack import Stack
from entity.Types import TreeNode,Relation

class ParseCore(object):
    def __init__(self,filePath):
        self.filePath = filePath
        self.hash = {}
    def getIndent(self,s):
        #将TAB换算为四个空格
        s = s.replace('\t','    ')
        l = len(s)
        return l
    def parse(self):
        fp = open(self.filePath,'r')
        #主要用来获得缩进的数目
        ptn = '(\s*)([\w\W]*)'
        #获得有用命令项
        ptnNode = '^(menuconfig|menu|config|choice|endif|help|endmenu|endchoice)([\w\W]*)'
        #获得if项
        ptnIf = '^if ([\w\W]+)'
        #获得数据类型
        ptnType = '^(tristate|bool|int|string|hex|prompt)([\w\W]*)'
        
        #def_XX value if XX
        ptnDefType = '^def_(bool)\s*([n|y])?\s*(if\s+([\w\W]+))?'
        #获得反向选择项
        ptnSelect = '^select ([\w|\d|_|-]+)(\s+if ([\w\W]+))?'
        #获得default项
        #ptnDefault = '^default ([\w|\d|_|-|"|"|:|/|%|\.]+)(\s+if ([\w\W]+))?'
        ptnDefault = '^default (".*?"|[\w|\d|_|-|"|"|:|/|%|\.|!]+)(\s+if ([\w\W]+))?'
        #获得依赖项
        ptnDepends = '^depends on ([\w\W]+)'
        #获得range
        ptnRng = '^range ([\w\W]+)'
        
        #当前正在处理的节点序列        
        nodeStack = Stack(False)
        #存储上面栈中节点对应的缩进
        indentStack = Stack(False)
        
        #存储当前if块对应的变量，每个if都有一个endif与它对应
        ifStack = Stack(False)
        #存储当前的menu和choice，每个menu都有一个endmenu与它对应，每一个choice都有一个endchoice对应
        menuStack = Stack(False)
        
        
        #利用栈来实现处理的先后次序，栈顶的表示当前正在处理的节点，每遇到一次缩进的变化，都去检查是否应该变换节点        
        root = TreeNode(None,'root','')
        root.visible = True
        nodeStack.push(root)
        indentStack.push(-1)
        parentSpace = -1
        
    

        for line in fp:
            line = line.replace('\n','')
            if line == '':
                continue
            m = re.match(ptn,line)
            indent = self.getIndent(m.group(1))
            stripStr = m.group(2).strip()
            mNode = re.match(ptnNode,stripStr)  
            mIf = re.match(ptnIf,stripStr)
            mType = re.match(ptnType,stripStr)
            mSelect = re.match(ptnSelect,stripStr)
            mDefault = re.match(ptnDefault,stripStr)
            mDepends = re.match(ptnDepends,stripStr)
            mRng = re.match(ptnRng,stripStr)
            mDefType = re.match(ptnDefType,stripStr)
            
            
            #只可能是‘子’    
            if indent >= parentSpace:
                if nodeStack.peek().getNodeType() == 'HELP':
                    continue
                #表示父节点的数据类型
                if mType is not None:
                        #print mType.groups()
                    curType = mType.group(1).strip()
                    node = nodeStack.peek()
                    if curType == 'prompt':
                        if mType.group(2).strip()!="":
                            node.visible = True;
                    else:
                        node.setType(mType.group(1).strip())
                        if mType.group(2) is not None and mType.group(2).strip() != '':
                            node.visible = True
                elif mDefType is not None:
                    curType = mDefType.group(1).strip()
                    #print curType
                    node = nodeStack.peek()
                    #print node.var
                    node.setType(curType)
                    if mDefType.group(2) is None:
                        dv = 'n'
                    else:
                        dv = mDefType.group(2).strip()
                    condition = mDefType.group(4)
                    if condition is not None:
                        idx = condition.find('#')
                        if idx != -1:
                            condition = condition[:idx]
                    default = Relation('default',dv,condition)
                    node.addDefault(default)
#                     node.visible = False
                    #表示select关系
                elif mSelect is not None:
                    select = Relation('select',mSelect.group(1).strip(),mSelect.group(3))
                    node = nodeStack.peek()
                    node.addSelect(select)
                    #表示父节点default取值
                elif mDefault is not None:
                    condition = mDefault.group(3)
                    if condition is not None:
                        idx = condition.find('#')
                        if idx != -1:
                            condition = condition[:idx]
                    default = Relation('default',mDefault.group(1),condition)
                    
                        
                        #print default
                    node = nodeStack.peek()
#                     if condition is not None:
#                         node.addDepend(condition)
                        #print node.var
                    node.addDefault(default)
                    #表示父节点depends on关系
                elif mDepends is not None:
                    node = nodeStack.peek()
                    dependStr = mDepends.group(1).strip()
                    idx = dependStr.find('#')
                    if idx != -1:
                        dependStr = dependStr[:idx]
                    node.addDepend(dependStr)
                elif mRng is not None:
                    node = nodeStack.peek()
                    rangeStr = mRng.group(1).strip().split()
                    tmp = []
                    try:
                        tmp.append(int(rangeStr[0]))
                    except:
                        tmp.append(rangeStr[0])
                    try:
                        tmp.append(int(rangeStr[1]))
                    except:
                        tmp.append(rangeStr[1])
                    node.range = tmp
               
            #‘可能是祖先 或者是兄弟节点’    
            else:
                top = indentStack.peek()
                #出栈，一起到当前块与上一块平行或者处于??‘子’??的位置
                while(indent <= top):
                    #print 'indent:%d:top:%d' %(indent,top)
                    indentStack.pop()
                    top = indentStack.peek()
                    nodeStack.pop()
                    parentSpace = top   
                
            #处理if/endif块
            if mIf is not None:
                #为了防止help块与if块平行 或者 if位于help块中的情形
                if not (indent < indentStack.peek() and nodeStack.peek().getNodeType() == 'HELP'):
                    ifStack.push(mIf.group(1).strip())    
            
            #添加新的节点
            if mNode is not None: 
                #print mNode.groups()
                pnode = nodeStack.peek()
                nType = mNode.group(1)
                #print nType
                    
                if(nType == 'endif'):
                    ifStack.pop()
                    continue
                if(nType == 'endmenu' or nType == 'endchoice'):
                    menuStack.pop()
                    continue
                if menuStack.isEmpty() == False:
                    pnode = menuStack.peek()
                
                node_var = mNode.group(2).strip()
                sharp_idx =  node_var.find('#')
                if sharp_idx != -1:
#                     print node_var
                    node_var = node_var[:sharp_idx].strip()
                    
                #处理config定义使用的特殊情况
                if nType == 'config' and node_var in self.hash:
                    node = self.hash[node_var]
                    tmp_parent = node.parent
                    #print node.var
                    #先使用再定义
                    if str(node.dataType) == 'UNDEFINED':
                        
                        curnode = TreeNode(tmp_parent,nType,node_var)
                        #print 'parent:' + node.parent.var
                        tmp_parent.children.remove(node)
                        
                        tmp_parent.addChild(curnode)
                        self.hash[node_var] = curnode
                        
                        nodeStack.push(curnode)
                        
                    #先定义再使用
                    else:
                        
                        tmp_parent.children.remove(node)
                        node.parent = pnode
                        pnode.addChild(node)
                        nodeStack.push(node)
                    
                else:
                    node = TreeNode(pnode,nType,node_var)
                        
                    if(nType == 'menu' or nType == 'choice'):
                        menuStack.push(node)
                    if(ifStack.isEmpty() == False):
                        node.addDepend(ifStack.peek())
                    node.level = pnode.level + 1
                   
                    pnode.addChild(node)
                    nodeStack.push(node)
                    if nType == 'config':
                        self.hash[node.var] = node
                indentStack.push(indent)
                parentSpace = indent
        return root  
        
if __name__ == "__main__":
    s = 'def_bool n if !B'
    ptn = '^def_(bool)\s*([n|y])?\s*(if\s+([\w\W]+))?'
    m = re.match(ptn,s)
    print m.groups()
    condition = m.group(4)
    print condition
    idx = condition.find('#')
    if idx != -1:
        condition = condition[:idx]
    print condition
    if m is not None:
        print m.groups()