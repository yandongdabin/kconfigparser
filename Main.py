# -*- coding: utf-8 -*-

'''
Created on 2015年11月24日

@author: yandong
'''
import os
from ct.InferAll import InferAll
from parse.ParseCore import ParseCore
from parse.ConfigParser import ConfigParser

import getopt
import sys

class Main():
    def __init__(self,configInPath):
        self.configInPath = configInPath
        tmpdir = 'tmp'
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
    #通过图算法分析得到少量的配置变量
    def generateTestSuite(self,outputName='tmp/testsuite.txt'):
        cp = ConfigParser(self.configInPath)
        res= cp.generateCB()
        maxsize = -1
        suite = []
        for r in res:
            if maxsize < len(r):
                maxsize = len(r)
                suite = r
        print 'we adopt the strongly connect component with size :%d' %(maxsize)
        fp = open(outputName,'w')
        for s in suite:
            fp.write(s+'\n')
        return outputName
    #通过少量的配置变量得到cascade输入
    def getCascadeInputFile(self,inputName='coreboot-part10.csv',configPath='.config'):
        pc = ParseCore(self.configInPath)        
        root = pc.parse()
        ia = InferAll(inputName)
        ia.generateCascadeInputFiles(inputName, configPath, root)

    #根据配置变量，cascade输入，原始config文件生成新的config文件
    def generateConfig(self,cetFileFolder='tmp/cetModel',csvFileName="testsuit.csv",configPath='.config'):
        ia = InferAll()
        pc = ParseCore(self.configInPath)        
        root = pc.parse()
        #ia.getConfigFile(cetFile,configPath,root)
        ia.getMultiConfigFile(cetFileFolder, configPath, root, csvFileName)
    
    #根据配置变量，cascade输入，得到 config.h 文件
    def generateConfigH(self,cetFile='tmp/cetct.txt'):
        ia = InferAll('')
        pc = ParseCore(self.configInPath)        
        root = pc.parse()
        ia.getConfighFile(cetFile,root)
        
    #通过cascade得到测试用例输出
    def generateCetRes(self,outputName='tmp/cetct.txt',modelName='tmp/model.txt'):
        cmd = 'cascade.exe ' + modelName + ' -o ' + outputName
        print cmd
        os.system(cmd)
    def combineModel(self,cetFolder='coreboot-10-11',configPath='.config'):
        ia = InferAll('')
        pc = ParseCore(self.configInPath)        
        root = pc.parse()
        ia.combineModelsDef(cetFolder,root,configPath)


def cmp(f1,f2):
    fp1 = open(f1,'r')
    f1_dict = []
    for l in fp1:
        f1_dict.append(l.strip())
    fp1.close()
    fp1 = open(f2,'r')
    f2_dict = []
    for l in fp1:
        f2_dict.append(l.strip());
    fp1.close()
    for f1 in f1_dict:
        if f1 in f2_dict:
            print f1
    print '----------------'
    for f2 in f2_dict:
        if f2 in f1_dict:
            print f2
def test():
    cmp('model/v14.txt','model/v11.txt')
helpstr = '''
-h print this message
--openwrt specify the openwrt directory
--gci getCascadeInputFile
--gc generateConfig
--gts generateTestSuite
--gcr run cascade to get the combinational testing suite result
--gch generate config.h file
--cm  combine the test cases of models 
'''
if __name__ == '__main__':
    main = Main('deleteafter.txt')
    try:
        opts,args = getopt.getopt(sys.argv[1:], "h", ["openwrt=","gci","gc","gts","gcr","gch","cm","test"])
    except Exception,e:
        sys.stderr.write('Unrecognized option\n')
        print helpstr
        sys.exit(0)
        
    openwrtdir = ""
    for op,value in opts:
        if op == '-h':
            print helpstr,
            sys.exit()
        elif op == '--openwrt':
            openwrtdir = value
        elif op == '--gci':
            main.getCascadeInputFile()
            sys.exit(0)
        elif op =='--gc':
            main.generateConfig()
            sys.exit(0)
        elif op =='--gts':
            main.generateTestSuite()
            sys.exit(0)
        elif op == '--gcr':
            main.generateCetRes()
            sys.exit(0)
        elif op == "--gch":
            main.generateConfigH()
            sys.exit(0)
        elif op == "--cm":
            main.combineModel()
            sys.exit(0)
        elif op =="--test":
            test()
            sys.exit(0)
        else:
            print helpstr
            sys.exit(0)
    #main.generateTestSuite()
    #main.getCascadeInputFile()
    #main.generateCetRes()
    #main.generateConfig()
    print helpstr