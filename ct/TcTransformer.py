# -*- coding: utf-8 -*-
'''
Created on 2016-12-29

@author: otcaix
'''
# -*- coding: utf-8 -*-
'''
Created on 2015.11.23
@author: yandong
通过图的分解结果来的到对应的cascade输入
并且通过cascade的输出得到.config文件（CONFIG_XXX）
'''
import Queue
import os
import re
import csv
from entity.Types import *
from parse.Utils import Utils


        


class TcTransformer(object):

    def __init__(self):
        pass
    
    def getDefaultConfigValues(self,configPath):
        fp = open(configPath,'r')
        defaultValues = {}
        ptn = '# CONFIG_([\w\W]+) is not set'
        ptn1 = 'CONFIG_([\w\W]+)\s*=\s*([\w\W]+)'
        for l in fp:
            l = l.strip()
            if l == '': continue
            m1 = re.match(ptn,l)
            m2 = re.match(ptn1,l)
            if m1 is not None:
                defaultValues[m1.group(1).strip()] = 'FALSE'
            elif m2 is not None:
                value = m2.group(2).strip()
                if value == 'y':
                    value = 'TRUE'
                elif value == 'n':
                    value = 'FALSE'
                defaultValues[m2.group(1).strip()] = value
        fp.close()
        return defaultValues

    def readTestCaseFromConfig(self,folder,configPath):
        testCases = []
        for f in os.listdir(folder):
            curf = folder + os.sep + f
            testCase = self.getDefaultConfigValues(curf)
            testCases.append(testCase)
        self.translateTestCaseToConfig(testCases, [], configPath)
            
    def translateValue(self,word,wordDict,changeType,usePrefix=True):
        output = wordDict[word]
        configPrefix = 'CONFIG_LP_'
        if usePrefix:
            prefix=configPrefix
        else:
            prefix=''
        if(word.startswith(configPrefix)):
            prefix=''
        if output == 'true' or output == "TRUE":
            output = prefix + word + '=' + 'y'
        elif output == 'false' or output == 'FALSE':
            output = '# '+ prefix + word + ' is not set'
        else:
            value = wordDict[word]
            iv_int = str(ENUM_INVALID_TYPE[ENUM_TYPE_INT])
            iv_str = str(ENUM_INVALID_TYPE[ENUM_TYPE_STRING])
            if value == iv_int or value == iv_str: return ''
            if word in changeType and not wordDict[word].startswith('0x'):
                #print word
                value = hex(int(wordDict[word]))
                if value[-1] == 'L':
                    value = value[:-1]
            else:
                value = wordDict[word]
            output = prefix + word + '=' + value
        return output
    def writeRemainWord(self,wordDict,wfp,variables,changeType):
        for word in wordDict:
            if word not in variables:
                continue
            output = wordDict[word]
#             if output == 'FALSE' or output == 'false':
#                 continue
            output = self.translateValue(word, wordDict,changeType)
            if output !='':
                output+='\n'
            wfp.write(output)   
        wordDict.clear()
    
    # 引号内出现空格的情况
    def splitter(self,s): 
        def replacer(m):
            return m.group(0).replace(" ", "\x00")
        parts = re.sub('".*?"', replacer, s).split() 
        parts = [p.replace("\x00", " ") for p in parts]
        return parts
    
    
    
    '''API'''
    def translateTestCaseToConfig(self,testCases,changeType,configPath):     
        seq = 1
        haveConfig = True
        configPrefix = 'CONFIG_LP_'
        for testCase in testCases:
            wfp = open('../configs/'+str(seq)+'.txt','w')
            
            fp = open(configPath,'r')
            for line in fp:
                line = line.replace('\n','')
                line = line.strip()
                if line == '':
                    wfp.write('\n')
                    continue
                else:
                    if haveConfig:
                        ptn = '# '+configPrefix+'([\w\W]+) is not set'
                        
                        ptn1 = configPrefix+'([\w\W]+)=([\w\W]+)'
                        m = re.match(ptn,line)
                        m1 = re.match(ptn1,line)
                    else:
                        ptn = '# ([\w\W]+) is not set'
                        ptn1 = '([\w\W]+)=([\w\W]+)'
                        m = re.match(ptn,line)
                        m1 = re.match(ptn1,line)
                        
                    
                    
                    if m is not None or m1 is not None:
                        if m is not None:
                            word = m.group(1).strip()
                        elif m1 is not None:
                            word = m1.group(1).strip()
                        #如果不在关注变量里面
                        if word not in testCase and configPrefix+word not in testCase:
#                             wfp.write(line + '\n')
                            if m is not None:
                                wfp.write(line + '\n')
                            else:           
                                if m1.group(2).strip() == 'y':
                                    if haveConfig:
                                        wfp.write('# ' + configPrefix  + word + ' is not set\n') 
                                    else:
                                        wfp.write('# ' + word + ' is not set\n') 
                            
                            
                        #如果在关注的变量里面 而且没有被处理过
                        elif word in testCase:
                            #print word
                            output=self.translateValue(word, testCase,changeType)
                            if output!='':
                                output+='\n'
                            wfp.write(output)
                            del testCase[word]
                        elif configPrefix+'_'+word in testCase:
                            output=self.translateValue(configPrefix+word, testCase,changeType)
                            if output!='':
                                output+='\n'
                            wfp.write(output)
                            del testCase[configPrefix+word]
                        
                    else:
                        wfp.write(line + '\n')
                        pass
            self.writeRemainWord(testCase, wfp,testCase.keys(),changeType)
               
            fp.close()
            wfp.close() 
            seq += 1
    
    
    def getVarFromCondition(self,condition):
        #print condition
        saves = condition.split('\n')
        tmp = []
        for save in saves:
            if save.strip() == '':
                continue
            save = re.sub(r'(?P<x>[\.\w\d_-]+)==(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            ptn = '([\.\w\d_-]+)'
            tmp += re.findall(ptn,save)
        return tmp
       
if __name__ == '__main__':
    pass