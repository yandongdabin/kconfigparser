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
from parse.CascadeConstrExtractor import CascadeConstrExtractor

class testCases(object):
    def __init__(self):
        self.ordinary = []
        self.keyIndex = {}
        self.value = []
        self.seq = -1
        self.cutVar = {}
        

class SUTModel(object):
    def __init__(self):
        self.keyValues = {}
    def __eq__(self,other):
        return self.keyValues == other.keyValues
        

class InferAll(object):


    def __init__(self, filePath):
        '''
        Constructor
        '''
        self.filePath = filePath
        self.typeChangeDict = {}
       
  
    #对变量类型的预处理  
    def changeType(self,old,var = ''):
        if old == ENUM_TYPE_TRISTATE:
            if var not in self.typeChangeDict:
                self.typeChangeDict[var] = old
            old = ENUM_TYPE_BOOL
        elif old == ENUM_TYPE_HEX:
            if var not in self.typeChangeDict:
                self.typeChangeDict[var] = old
            old = ENUM_TYPE_INT
        return old
    #对变量取值的预处理
    def getValueForType(self,node,t,cfp):
        dType = node.dataType
        value = dType.getValue()
        var = node.var
        old = node.var
        if '-' in node.var:
            var = old.replace('-','_')
            cfp.write(var + '\t' + old + '\n')  
          
        if value is None:
            value = node.getDefaultValue()
#         if str(dType) == 'INT' or str(dType)=='STRING':
#             value += node.getInvalidValueStr(str(dType))
        if t == ENUM_TYPE_BOOL:
            return 'bool %s;' %(var)
        else:
            return '%s %s: %s;' %(ENUM_REV_DTYPES[t],var,value)
    #得到变量的无效取值
    def getInvalidValue(self,node,t):
        if t == 'bool':
            return 'false'
        else:
            return node.getDefaultValue()
        
    
    def parseCSV(self,fileName):
        '''解析CSV文件'''
        csvfile = csv.reader(file(fileName,'rb'))
        cluster = {}
        threshold = 50
        line_cnt = -1
        for line in csvfile:
            line_cnt += 1
            if line_cnt == 0:
                continue
            
            if len(line) > 1:
                if line[0].strip() == '':
                    continue
                if line[1] not in  cluster:
                    cluster[line[1]] = [line[0]]
                else:
                    cluster[line[1]].append(line[0])
        
        cur_cnt = 0
        ct_groups = []
        cur_group = []
        for key in cluster:
            
            cur_cluster = cluster[key]
            #cnt += len(cur_cluster)
            if len(cur_cluster) > threshold:
                tmp = []
                tmp.append(cur_cluster) 
                ct_groups.append(tmp)
            else:
                if cur_cnt + len(cur_cluster) > threshold:
                    cur_group.append(cur_cluster)
                    ct_groups.append(cur_group) 
                    cur_cnt = 0
                    cur_group = []
                else:
                    cur_group.append(cur_cluster)
                    cur_cnt += len(cur_cluster)
        if len(cur_group) > 0:
            ct_groups.append(cur_group)
        return ct_groups
    
    def getDefaultValues(self,configPath):
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
                defaultValues[m1.group(1).strip()] = 'false'
            elif m2 is not None:
                value = m2.group(2).strip()
                if value == 'y':
                    value = 'true'
                elif value == 'n':
                    value = 'false'
                defaultValues[m2.group(1).strip()] = value
        fp.close()
        return defaultValues
                
    # 分解结果的csv文件，默认配置文件，以及变量约束图对应的根节点root
    def generateCascadeInputFiles(self,fileName,configPath,root):
        ct_groups = self.parseCSV(fileName)
        self.genVCModel(ct_groups,configPath,root)
        
    def genVCModel(self,ct_groups,configPath,root):        
        "generate Variable Constraint model"
        
        
        defaultValues = self.getDefaultValues(configPath)
        #记录各个SUTModel的统计信息
        sfp = open('model/count.txt','w')
        seq = 1
        for g in ct_groups:
            cur_group =g
            outputFileName = 'model/model' + str(seq) + '.txt'
            seq += 1
            fp = open(outputFileName,'a+')
            if len(g) == 1:
                self.subGenVCModel(root,cur_group,configPath,False,fp,seq,sfp,defaultValues)
            else:
                self.subGenVCModel(root,cur_group,configPath,True,fp,seq,sfp,defaultValues)
        sfp.close()
        cfp = open('model/changeType.txt','w')
        for var in self.typeChangeDict:
            cfp.write(var + ' ' + self.typeChangeDict[var] + '\n')
        cfp.close()

    def subGenVCModel(self,root,g,configPath,isChangeable,fp,seq,sfp,defaultValues=None):
        'generate variable constraint model with default strength'
        
        cutParameter = 0
        orderParamter = 0
        
        changeFp = open('tmp/change.txt','w')
        vfp= open('model/v'+str(seq-1)+'.txt','w')
            
        fp.write('[PARAMETERS]'+'\n')
        variables = []
        if not isChangeable:
            variables += g[0]
        else:
            for subg in g:
                variables += subg
        for v in variables:
            vfp.write(v + '\n')
        leftnodes = []    
        queue = Queue.Queue()
        queue.put(root)
        conditions = []
            
        excludeChoice = []
            
        type_dict = {}
        variables_str = []
        
        auxVar = []
        known = []
        
        
        rd_dict = Utils.getRdDict(queue)
            
        #正常的寻找变量以及约束关系 
        queue.put(root)   
        while not queue.empty():
            cur = queue.get()
            for child in cur.children:
                queue.put(child)
            cType = cur.getNodeType()
            if cur.var not in type_dict:
                type_dict[cur.var] = (cur,cur.dataType)
            
            #print cType
            if cType == ENUM_CHOICE:
                for child in cur.children:
                    extractor = CascadeConstrExtractor(child)
                    if child.var in variables and cur not in excludeChoice:
                        conditions.append(extractor.getChoiceCondition(auxVar,known))
                        excludeChoice.append(cur)
                        break
            extractor = CascadeConstrExtractor(cur)
            #得到所有有所选变量有关联的约束关系
            #print cType
            if cType != ENUM_HELP and cType!=ENUM_MENU and cType!=ENUM_CHOICE and cType!=ENUM_ROOT:
                    #print cur.var
                    condition = extractor.getConditionImp(known,rd_dict)
                    cs = condition.split('\n')
                    for c in cs:
                        flag = False
                        vs = self.getVarFromCondition(c)
                        for v in vs:
                            if v in variables:
                                flag = True
                                break
                        
                        if flag:    
                            conditions.append(c+'\n')
                                
            #得到所有的所选变量的取值
            if cur.var.strip() in variables:
                #普通变量计数器
                orderParamter += 1
                
                leftnodes.append(cur)
                    
                dType = cur.dataType
                    
                    #GET VARIABLES    
                if  cType != ENUM_MENU and cType != ENUM_CHOICE and cType != ENUM_HELP:       
                    t = self.changeType(dType,cur.var)
                    if cur.visible == True:
                        variables_str.append(self.getValueForType(cur, t,changeFp))
                    else:
                        variables_str.append('__aux__ ' + self.getValueForType(cur, t,changeFp))
                    #GET CONDITION
#                 if cType != 'HELP' and cType!='MENU' and cType!='CHOICE':
#                     condition = cur.getCondition(known,rd_dict)
#                     if condition != '':
#                         conditions.append(condition)

        #根据约束关系得到所有的在约束关系中出现的变量
        condition_var = []
        for c in conditions:
            for t in self.getVarFromCondition(c):
                if t not in condition_var:
                    condition_var.append(t)   
            
            #关心的变量
        for s in variables_str:
            fp.write(s+'\n')
        for v in auxVar:
            fp.write('__aux__ bool auxVar'+str(v)+';\n')
        
        #分割的变量 或者是choice条件引入的变量
        modelCutFp = open("model/cut"+str(seq-1)+".txt",'w')
        cutVariables = []
        for v in condition_var:
            if v!='UNDEFINED' and v!='1' and v !='0' and v!='int' and not v.startswith('auxVar') and v not in variables:
                if v in type_dict:
                    node,t = type_dict[v]
                    if v in defaultValues:
                        conditions.append(v + '==' + defaultValues[v] + ';\n')
                    else:
                        #bool不出现表示为false
                        if t == "bool":
                            conditions.append(v+'==false;\n')
                    t = self.changeType(t,cur.var)
                    modelCutFp.write(v+'\n');
                    cutVariables.append(v)
                    #print self.getValueForType(node, t,changeFp)
                    cutParameter += 1
                    fp.write(self.getValueForType(node, t,changeFp)+'\n')
                    
        modelCutFp.close()            
        sfp.write("model:"+str(seq-1)+"\n")    
        sfp.write("cut:"+str(cutParameter)+"\n")
        sfp.write("ordinary:"+str(orderParamter)+"\n") 
        sfp.write("total:"+str(cutParameter+orderParamter)+"\n")   
        sfp.write("--------------------------------------------"+"\n")       

        fp.write('[STRENGTHS]'+'\n')
        if not isChangeable:
            #print 'default: 3;'
            fp.write('default: 2;'+'\n')
        else:
            #print 'default: 1;'
            fp.write('default: 1;\n')
            for subg in g:
                cstrength = ''
                for ssg in subg:
                    if(cstrength == ''):
                        cstrength += ssg
                    else:
                        cstrength += ',' + ssg;
                if len(subg) >= 2:
                    cstrength += ' :2;'
                else:
                    cstrength += ' :1;'
                #print cstrength
                fp.write(cstrength+'\n')
            if len(cutVariables) >=2:
                fp.write(','.join(cutVariables)+': 2' + ';\n')
        #print '[CONSTRAINTS]'
        fp.write('[CONSTRAINTS]\n')
        for c in conditions:
            #print c,
            #处理表达式中 有=的情况,注意处理 !=时的情况
            c = c.replace('!=','\x00')
            c = c.replace('>=','\x01')
            c = c.replace('<=','\x02')
            c = c.replace('=','#')
            
            c = re.sub('#+','==',c)
            c = re.sub('\x00','!=',c)
            c = re.sub('\x01','>=',c)
            c = re.sub('\x02','<=',c)
            fp.write(c)             

        fp.write('[SEEDS]')
        changeFp.close()   
        
    def getConfigDefaultValues(self,configPath):
        ret = {}
        fp = open(configPath,'r')
        for line in fp:
            line = line.replace('\n','')
            if line == '' or line[0] == '#':
                continue
            ptn = 'CONFIG_([\w\W]+)=([\w\W]+)'
            m = re.match(ptn,line)
            if m.group(1).strip() not in ret:
                ret[m.group(1).strip()]=m.group(2).strip()   
        fp.close()
        return ret
    
    
    
    # 引号内出现空格的情况
    def splitter(self,s): 
        def replacer(m):
            return m.group(0).replace(" ", "\x00")
        parts = re.sub('".*?"', replacer, s).split() 
        parts = [p.replace("\x00", " ") for p in parts]
        return parts

    
    
    
    
    def getMultiConfigFile(self,cetDir,configPath,root,csvFileName):
        ct_groups = self.parseCSV(csvFileName)
        variables = []
        dirs = os.listdir(cetDir)
        curDirIdx = 0
        seq = 1
        for g in ct_groups:
            if len(g) == 1:
                variables = g
            else:
                for subg in g:
                    variables += subg
            self.getConfigFile(dirs[curDirIdx], configPath, root, variables, seq)
            curDirIdx += 1
            seq += 1
    
    
    """
    将不同的model生成的test case组合起来
    命名规则：
    model1.txt ---> 1.txt
    model2.txt ---> 2.txt
    每个model i都有一个 cut{i}.txt 来说明引入的割边 
    """
    def combineModels(self,cetFolder,root,configPath):
        sutModels = []
        #读取所有的测试用例集，每个model生成的测试用例集用一个TestCases的结构体表示
        totalTcs = self.readAllTestCases(cetFolder)
        #对所有的组合测试集进行组合，组合成完整的测试用例集    
        for tcs in totalTcs:
            seq = tcs.seq
            #找到该model对应的割边上的点
            fp = open('model/cut'+str(seq)+".txt",'r')
            cutKey = []
            for l in fp:
                l = l.replace('\n','')
                cutKey.append(l)
            
            cutEdges = {}    
            #找到当前簇与其他簇之间连接的cut-edge
            for inner in totalTcs:
                if seq == inner.seq:
                    continue
                found = []
                    #是否能够在一个块中找到对应的割边上的点
                for c in cutKey:
                    if c in inner.ordinary:
                        found.append((tcs.keyIndex[c],inner.keyIndex[c]))
                cutEdges[inner.seq] = found
            
            #核心算法：对于每一个测试用例都尝试找到一个可以组合的测试用例
            for testcase in tcs.value:
                sutModel = SUTModel()
                legal = True
                for k in tcs.keyIndex.keys():
                    sutModel.keyValues[k] = testcase[tcs.keyIndex[k]]
                for inner in totalTcs:
                    if seq == inner.seq:
                        continue
                    #print seq
                    found = cutEdges[inner.seq]
                    (flag,idx) = self.getOneLegal(testcase, found, inner)
                    if flag == True:
                        for k in inner.keyIndex:
                            if k in sutModel.keyValues:
                                continue
                            sutModel.keyValues[k] = inner.value[idx][inner.keyIndex[k]]
                    else:
                        legal = False
                if legal:        
                    sutModels.append(sutModel)
        newsutModels = []
        for sutModel in sutModels:
            if sutModel not in newsutModels:
                newsutModels.append(sutModel)
        print len(newsutModels[0].keyValues)         
        print len(newsutModels)        
        self.translateTestCaseToConfig(newsutModels, root,configPath)   
    
    
    def readAllTestCases(self,cetFolder):
        dirs = os.listdir(cetFolder)
        totalTcs = []
        tmpCnt = 0
        #读取所有的测试用例集，每个model生成的测试用例集用一个TestCases的结构体表示
        for d in dirs:
            fp = open(cetFolder+'/'+d)
            tmp_seq = os.path.splitext(d)[0]
            print tmp_seq
            vfp = open('model/'+'v'+str(tmp_seq)+'.txt','r')
            cutfp = open('model/'+'cut'+str(tmp_seq)+'.txt','r')
            tcs = testCases()
            for l in vfp:
                l = l.strip().replace('\n','')
                if l != '':
                    tcs.ordinary.append(l)
            vfp.close()
            cutVar = []
            for l in cutfp:
                cutVar.append(l.strip())
            cutfp.close()
            willDel = []
            lineCnt =  -1
            for l in fp:
                lineCnt += 1
                if lineCnt == 0:
                    ls = l.strip().split()
                    i = 0
                    j = 0
                    for lls in ls:
                        if lls.startswith('auxVar'):
                            willDel.append(i)
                        else:
                            tcs.keyIndex[lls] = j
                            j += 1
                        i = i + 1
                elif lineCnt == 1:
                    willDel.sort(reverse=True)
                    continue
                else:
                    ls = self.splitter(l)
                    for wd in willDel:
                        del ls[wd]
                    tcs.value.append(ls)
            for v in cutVar:
                tcs.cutVar[v] = tcs.keyIndex[v]
            tcs.seq = int(os.path.splitext(d)[0])
            totalTcs.append(tcs)
            tmpCnt += lineCnt - 1
            fp.close()
        return totalTcs
    def combineModelsDef(self,cetFolder,root,configPath):
        totalTcs = self.readAllTestCases(cetFolder)
        defaultValues = self.getDefaultValues(configPath)
        sutModels = []
        for tcs in totalTcs:
            for i in range(len(tcs.value)):
                curModel = SUTModel()
                for key in tcs.keyIndex:
                    curModel.keyValues[key] = tcs.value[i][tcs.keyIndex[key]]
                for d in defaultValues:
                    if d not in curModel.keyValues:
                        curModel.keyValues[d] = defaultValues[d]
                sutModels.append(curModel)
        self.translateTestCaseToConfig(sutModels, root, configPath)
    def translateTestCaseToConfig(self,sutModels,root,configPath):
        
        fp = open('model/changeType.txt','r')
        changeType = []
        for l in fp:
            ls = l.strip().split()
            changeType.append(ls[0])
        fp.close()
        seq = 1
        node_dict = {}
        queue = Queue.Queue()
        queue.put(root)
        while not queue.empty():
            cur = queue.get()
            node_dict[cur.var]=cur
            for child in cur.children:
                queue.put(child)
                
        
        haveConfig = True
        
        for sutmodel in sutModels:
            wfp = open('configs/'+str(seq)+'.txt','w')
            
            fp = open(configPath,'r')
            for line in fp:
                line = line.replace('\n','')
                line = line.strip()
                if line == '':
                    wfp.write('\n')
                    continue
                else:
                    if haveConfig:
                        ptn = '# CONFIG_([\w\W]+) is not set'
                        
                        ptn1 = 'CONFIG_([\w\W]+)=[\w\W]+'
                        m = re.match(ptn,line)
                        m1 = re.match(ptn1,line)
                    else:
                        ptn = '# ([\w\W]+) is not set'
                        ptn1 = '([\w\W]+)=[\w\W]+'
                        m = re.match(ptn,line)
                        m1 = re.match(ptn1,line)
                        
                    
                    
                    if m is not None or m1 is not None:
                        if m is not None:
                            word = m.group(1).strip()
                        elif m1 is not None:
                            word = m1.group(1).strip()
                        #如果不在关注变量里面
                        if word not in sutmodel.keyValues and 'CONFIG_'+word not in sutmodel.keyValues:
                            wfp.write(line + '\n')
                            
                        #如果在关注的变量里面 而且没有被处理过
                        elif word in sutmodel.keyValues:
                            #print word
                            output=self.translateValue(word, sutmodel.keyValues,node_dict,changeType)
                            if output!='':
                                output+='\n'
                            wfp.write(output)
                            del sutmodel.keyValues[word]
                        elif 'CONFIG_'+word in sutmodel.keyValues:
                            output=self.translateValue('CONFIG_'+word, sutmodel.keyValues,node_dict,changeType)
                            if output!='':
                                output+='\n'
                            wfp.write(output)
                            del sutmodel.keyValues['CONFIG_'+word]
                        
                    else:
                        wfp.write(line + '\n')
            #print len(sutmodel.keyValues)
            self.writeRemainWord(sutmodel.keyValues, wfp,sutmodel.keyValues.keys(),node_dict,changeType)
               
            fp.close()
            wfp.close() 
            seq += 1
    
    def translateValue(self,word,wordDict,node_dict,changeType,usePrefix=True):
        output = wordDict[word]
        if usePrefix:
            prefix='CONFIG_'
        else:
            prefix=''
        if(word.startswith('CONFIG_')):
            prefix=''
        if output == 'true':
            output = prefix + word + '=' + 'y'
        elif output == 'false':
            output = '# '+ prefix + word + ' is not set'
        else:
            if word in changeType and not wordDict[word].startswith('0x'):
                #print word
                value = hex(int(wordDict[word]))
                if value[-1] == 'L':
                    value = value[:-1]
            else:
                value = wordDict[word]
            output = prefix + word + '=' + value
        return output
    def writeRemainWord(self,wordDict,wfp,variables,node_dict,changeType):
        for word in wordDict:
            if word not in variables:
                continue
            output = self.translateValue(word, wordDict,node_dict,changeType)
            if output !='':
                output+='\n'
            wfp.write(output)   
        wordDict.clear()
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
    #得到部分组合测试用例的使用方法
    #pc = ParseCore('deleteafter.txt')        
    #root = pc.parse()
    #ia = InferAll('testsuite.txt')
    #ia.combineModels('../testcases')
    
#     s='!IFUPDOWN && UDHCPC || (IFUPDOWN_UDHCPC_CMD_OPTIONS=="-R -n");'
#     save = re.sub(r'(?P<x>[\.\w\d_-]+)==(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',s)
#     print save
    c = "a=1 || b == 1 && c!=2"
    c = c.replace('!=','\x00')
    c = c.replace('=','#')
    
    c = re.sub('#+','==',c)
    c = re.sub('\x00','!=',c)
    print c
    #ia.initValue(root)
    #ia.getConfigFile()
    #print ia.getVarFromCondition('PACKAGE_busybox|| !(BUSYBOX_DEFAULT_LAST_SUPPORTED_WCHAR==-1);') 
    #print ia.getConfigDefaultValues('../.config')
        