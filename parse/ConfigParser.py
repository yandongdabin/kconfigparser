# -*- coding: utf-8 -*-
"""
主控模块
主要完成kconfig的预处理(关键是source的处理方式)，调用其他模块完成cascade输入文件的生成

"""

import re
import os
from Queue import Queue
from parse.ParseCore import ParseCore
from ct.SimpleCondition import SimpleCondition
from entity.Stack import Stack          

from ModelExtractor import CascadeModelExtractor,ActsModelExtractor
     
class SourceNode(object):
    def __init__(self,value,level = -1):
        self.name = value
        self.children = []
        self.level = level
    def addChild(self,child):
        self.children.append(child)    
    def __str__(self):
        return self.name +'  ' +str(self.level)
    def setLevel(self,level):
        self.level = level
    def getLevel(self):
        return self.level
    def getChildren(self):
        return self.children


# 提供的API proprcess对目标KConfig文件进行预处理 
#          deleteHelpModule删除help模块，为处理做好准备
#          getCondition 解析预处理后的KConfig文件，生成组合测试模型，适用于small-scale software
class ConfigParser(object):
    def __init__(self):
        #self.filePath = filePath
        #self.basePath = '/home/yandong/Desktop/Experiment/busybox-1.24.1/'
        self.ptnSource = 'source ([\w\W]+)'
        self.ptn = '(\s*)([\w\W]*)' 
        self.sourceStack = Stack(False)
    """
         预处理Kconfig文件，处理source关键字
    """
    def preprocess(self,basePath,filePath):
        fp = open(basePath + '//' + filePath,'r')
        outputPath ='../total.txt'
        wfp = open(outputPath,'w')
        
        self.sourceStack.clear()
        self.basePath = basePath
        root = SourceNode(filePath,0)
        self.sourceStack.push(root)
        for line in fp:
            self.preprocessLine(wfp,line,'',basePath,basePath)
        self.sourceStack.pop()
        fp.close()
        wfp.close()
        self.deleteHelpModule(outputPath)
#         self.printSourceTree(root)
    def preprocessLine(self,wfp,line,indent,rePath,basePath):
        line = line.replace('\n','')
        m = re.match(self.ptn,line)
        if m is not None:
            mSource = re.match(self.ptnSource,m.group(2).strip())
            if mSource is not None:
                urls = self.disposeUrl(mSource.group(1))
                print urls
                self.disposeSource(wfp,urls,m.group(1) + indent,rePath,basePath)
            else:
                wfp.write(indent + line + '\n')
    def disposeSource(self,wfp,urls,indent,rePath,basePath):
             
        for url in urls:
            #print url
            
            tPath = basePath + '/' + url
            print tPath
            ttPath = rePath + '/' + url
            print ttPath
            if os.path.exists(tPath) or os.path.exists(ttPath):
                #print tPath
                fp=None
                if(os.path.exists(tPath)):
                    node = SourceNode(tPath)
                    node.setLevel(self.sourceStack.peek().getLevel()+1)
                    self.sourceStack.peek().addChild(node)
                    
                    fp = open(tPath,'r')
                    self.sourceStack.push(node)
                else:
                    node = SourceNode(ttPath)
                    node.setLevel(self.sourceStack.peek().getLevel()+1)
                    self.sourceStack.peek().addChild(node)
                    fp = open(ttPath,'r')
                    self.sourceStack.push(node)
                
                for line in fp:
                    #wfp.write(indent)
                    self.preprocessLine(wfp,line,indent,os.path.dirname(tPath),basePath)
                    #wfp.write(line)
                fp.close()
                self.sourceStack.pop()
            else:
                #print tPath
                pass
    #得到source所提文件的路径
    def disposeUrl(self,url):
        #print url
        #处理在引号中的情况
        if url[0] == '"':
            url = url[1:-1]
        queue = Queue()
        urls = []
        queue.put(url)  
        while queue.empty() == False:
            cur = queue.get()
            starPos = cur.find('*')
            if starPos != -1:
                prefix = cur[:starPos]
                tPath = self.basePath + os.sep + prefix
                dirs = os.listdir(tPath)
                for d in dirs:
                    if os.path.isdir(tPath + os.sep + d):
                        queue.put(cur[:starPos]+d+cur[starPos+1:])
                    
                        
            else:
                urls.append(cur)
        return urls   
    
    """
    #删除help模块
    """
    def deleteHelpModule(self,filePath):
        fp = open(filePath,'r')
        outputPath = '../pure.txt'
        wfp = open(outputPath,'w')
        whelp = open('help.txt','w')
        ptnHelp = '(\s*)help'
        ptnIndent = '(\s*)(config|menuconfig|menu|if)\s+[\w\W]+'
        ptnWithoutIndent = '(\s*)(choice|endmenu|endchoice|endif)\s*'
        inHelp = False
        indentHelp = 100
        for line in fp:
            
            line = line.replace("\n","")
            if line.strip() == '' or line.strip()[0] == '#':
                continue
            #print line
            mHelp = re.match(ptnHelp,line)
            
            if mHelp is not None:
#                 print mHelp.group()
                inHelp = True
                indentHelp = len(mHelp.group(1).replace('\t','    '))
            else:
                mIndent = re.match(ptnIndent,line)
                mWithtouIndent = re.match(ptnWithoutIndent,line)
                if mIndent is not None or mWithtouIndent is not None:
                    
                    if mIndent is not None:
                        curIndent = len(mIndent.group(1).replace("\t","    "))
                    if mWithtouIndent is not None:
                        curIndent = len(mWithtouIndent.group(1).replace("\t","    "))
                    if curIndent <= indentHelp:
                        inHelp = False
            if not inHelp:
                wfp.write(line+'\n')
                #print line   
            else:
                whelp.write(line + '\n')
        wfp.close()
        whelp.close()
        fp.close()        
    def readFile(self):
        wfp = open('result.txt','w')
                
        ptn1 = '(CONFIG_\w+)=([\w\W]+)'
        ptn2 = '# (CONFIG_\w+) is not set'
        ptns = [ptn1,ptn2]
        fp = open(self.filePath,'r')
        for line in fp:
            #print line
            for ptn in ptns:
                m = re.match(ptn,line)
                if m is not None:
                    print m.groups()[0]
                    wfp.write(m.groups()[0]+'\n')
                    break
        wfp.close()


    def getGraph(self,filePath):
        pc = ParseCore(filePath)
        root = pc.parse()
        sc = SimpleCondition()
        #得到邻接表存储的图结构
        sc.buildGraph(root)       
                
    def test(self):
        pc = ParseCore(self.filePath)
        root = pc.parse()
        self.printNodeWithQueue(root)
            

if __name__ == "__main__":
    #cp = ConfigParser('/home/yandong/openwrt/target/Config.in')
    #cp = ConfigParser('/home/yandong/桌面/openwrt-project/stage2-config/test.txt')
    #cp = ConfigParser('I:\\home\\yandong\\openwrt\\feeds\\packages\\utils\\lxc\\Config.in')
    #cp = ConfigParser('../total.txt')
    
    
    ################
    # busybox path
    ################
#     basePath = '/home/yandong/桌面/newTest/busybox-1.24.1'
#     filePath = 'Config.in'

    ################
    # axTls path
    ################        
#     basePath = '/home/yandong/桌面/newTest/axtls-code'
#     filePath = 'config/Config.in'

    ################
    # axTls path
    ################        
#     basePath = '/home/yandong/桌面/newTest/uClibc-0.9.33'
#     filePath = 'extra/Configs/Config.in'
#     basePath = '/home/yandong/桌面/newTest/coreboot-4.4'
#     filePath = 'src/Kconfig'
    basePath = '/home/rest/Desktop/Experiment-yd-newtest/libpayload'
    filePath = 'Kconfig'
    
#     cp = ConfigParser()
#     cp.getGraph('../testObj/libpayload/pure.txt')
#     
#     cp = ConfigParser()
#     cp.preprocess(basePath, filePath)
#     cp.deleteHelpModule('../total.txt')
    modelEx = ActsModelExtractor('../testObj/libpayload/pure.txt')
#     modelEx.getModel()
#     modelEx.getVModel(2, '../testObj/libpayload/cluster.csv')
#     modelEx.getModel()
    modelEx.getConfigFiles('../testObj/libpayload/libpayload_vs2.txt', '../testObj/libpayload/defconfig')
#     modelEx.getConfigFiles('../busybox/busybox_str2_tc47.txt', '../busybox/defconfig')

#     modelEx.clusterInfo('../testObj/axtls/cluster.csv')
#     modelEx.getSimpleConfig('../testObj/coreboot/random-test','../testObj/coreboot/defconfig')
#     modelEx.getConfigFiles('../testObj/axtls/axtls_vs2_ce.txt', '../testObj/axtls/defconfig')
#     modelEx.getConfigFiles('../testObj/busybox/busybox_str2_ce.txt', '../testObj/busybox/defconfig')
#     modelEx.getConfigFiles('../testObj/exam/exam_vs2.txt', '../testObj/exam/defconfig')
#     testCases = modelEx.getTestCases('tmp/busybox_acts.txt')
#     print len(testCases)
#     for testCase in testCases:
#         for v in testCase:
#             print v,testCase[v]
#         print '-----------------'
#     cp = ConfigParser()
#     cp.preprocess(basePath, filePath)
#     cp.deleteHelpModule('../total.txt')
#     cp.getCondition('../deleteafter.txt')
#     cp.getGraph('../deleteafter.txt')
    #cp.preprocess()
    #cp.deleteHelpModule('../total.txt')
    #cp.getCondition()
#     ptnDefault = '^default (".*?"|[\w|\d|_|-|"|"|:|/|%|\.]+)(\s+if ([\w\W]+))?'
#     s='default "c:\\Program Files\\Microsoft Visual Studio .NET 2003"'
#     m = re.match(ptnDefault,s)
#     if m is not None:
#         print m.group(1)
    #cp.preprocess()
    #cp.deleteHelpModule('../total.txt')
    #cp.getCondition()
    #cp.preprocess()
    #cp.generateCB()
    #cp.getGraph()
    #cp.preprocess()
    #res= cp.generateCB()
    #print res
    #cp.getCondition()
    #cp = ConfigParser('')
    #cp.deleteHelpModule('../total.txt')
    #cp.deleteHelpModule('config-package.in')
    #print cp.getIndent('')
    #cp.preprocess()
    #cp.getCondition()
    #cp.getCondition()
    #cp.test()
   
    #s = 'if PACKAGE_dnsmasq-full'
    
    #ptn = 'source ([\w\W]+)'
    #s = 'source "package/utils/busybox/config/archival/Config.in"'
    #print re.match(ptn,s).group(1)
    #cp.preprocess()
    #source = 'package/*/image-config.in'
    #print cp.disposeUrl(source)
    #m = re.findall(ptn,s)
    #print re.sub(ptn,'\g<var>==true',s)
            
    #print s
    #cp.test(s)
    #cp.parse()
            
    
    
    
    

    