# -*- coding: utf-8 -*-
'''
Created on 2016-12-28

@author: yandong
'''
from Queue import Queue
from parse.ParseCore import ParseCore         
from parse.CascadeConstrExtractor import CascadeConstrExtractor
from parse.ActsConstrExtractor import ActsConstrExtractor
from entity.Types import *
from Utils import Utils
import re,json,csv
from ct.TcTransformer import TcTransformer
# import numpy as np

class ModelExtractor(object):
    def __init__(self,filePath):
        self.filePath = filePath
        self.changeType = []
    def getSimpleConfig(self,folder,configPath):
        tc = TcTransformer()
        tc.readTestCaseFromConfig(folder, configPath)
    def getVariable(self,root):
        retVariables = []
        queue = Queue()
        queue.put(root)
        static_dict = {}
        visible_num = 0
        invisible_num = 0
        
#         allIntValue = []
#         allStringValue = []
        
        while queue.empty() == False:
            current = queue.get()
            
            for child in current.children:
                queue.put(child)
                cType = child.getNodeType()
                if  cType == ENUM_MENU or cType == ENUM_CHOICE or cType == ENUM_HELP: 
                    continue
                if len(child.default) <= 0 and child.dataType == ENUM_TYPE_STRING:
                    child.default.append(Relation('default','""',None))
                #statistic number
                if child.visible:
                    visible_num += 1
                else:
                    invisible_num += 1
                
                
                dType = child.dataType
                if dType in ENUM_VALUES: #boolean and tristate
                    value = ENUM_VALUES[dType] 
                else:                    #others
                    value = child.getDefaultValue()
#                     if dType == ENUM_TYPE_INT or dType == ENUM_TYPE_HEX:
#                         for v in value:
#                             if v not in allIntValue:
#                                 allIntValue.append(v)
#                     else:
#                         for v in value:
#                             if v not in allStringValue:
#                                 allStringValue.append(v)
                

                iv = child.getInvalidValueStr(dType)
                if iv not in value:
                    value.append(iv)
                value = ','.join(value)
                if  cType != ENUM_MENU and cType != ENUM_CHOICE and cType != ENUM_HELP: 
                    if dType not in static_dict:
                        static_dict[dType] = 0
                    static_dict[dType] += 1
                    if dType == ENUM_TYPE_TRISTATE:
                        dType = ENUM_TYPE_BOOL
                    elif dType == ENUM_TYPE_HEX:
                        dType = ENUM_TYPE_INT
                        if child.var not in self.changeType:
                            self.changeType.append(child.var)
 
                    retVariables.append(self.getSingleVariable(dType,child,value))
                    
                    
        for dType in static_dict:
            print ENUM_REV_DTYPES[dType],static_dict[dType]
        print 'invisible',invisible_num
        print 'visible',visible_num
        json.dump(self.changeType,open('tmp/changeType.txt','w'))
        return retVariables
    def getSingleVariable(self,dType,node,value):
        pass
    
    def genConditionByRoot(self,root):
        retConditions = []
        condition_dict = {}
        condition_dict['depend'] = 0
        condition_dict['select'] = 0
        condition_dict['default'] = 0
        condition_dict['choice'] = 0
        queue = Queue()
        for child in root.children:
            queue.put(child)
            
        rd_dict = Utils.getRdDict(queue)
        
        for child in root.children:
            queue.put(child)
        auxVar = []        
    
        while queue.empty() == False:
            node = queue.get()
            extrator = self.getConstrExtractor(node)
            if node.getNodeType() != ENUM_HELP and node.getNodeType()!=ENUM_MENU and node.getNodeType() != ENUM_CHOICE:
                condition = extrator.getConditionImp([],rd_dict,condition_dict)
                if condition != '':
                    retConditions.append(condition)
            elif node.getNodeType()==ENUM_CHOICE:
                retConditions.append(extrator.getChoiceCondition(auxVar,[]))
                condition_dict['choice']+=1

            for child in node.children:
                queue.put(child)    
        for c in condition_dict:
            print c,condition_dict[c]
    
        return (retConditions,auxVar)     
    def getConstrExtractor(self,node):
        return CascadeConstrExtractor(node) 
    'parse the cluster information from a csv format file'
    def parseCSV(self,fileName):
        csvfile = csv.reader(file(fileName,'rb'))
        cluster = {}
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
        
        
   
        return cluster
    
    
    def getModel(self,useVariableStrength = False,clusterFile='',defaultStrength=2):
        pass
    'Extract the test cases in the file'
    def getTestCases(self,fileName):
        pass
    
    def getConfigFiles(self,fileName,configPath):
        changeType = json.load(open('tmp/changeType.txt','r'))
        tcs = TcTransformer()
        tcs.translateTestCaseToConfig(self.getTestCases(fileName), changeType, configPath)
    def getVariableStrength(self):
        pass   
    def getVarFromCondition(self,condition):
        #print condition
        saves = condition.split('\n')
        tmp = []
        for save in saves:
            if save.strip() == '':
                continue
            save = re.sub(r'(?P<x>[\.\w\d_-]+)\s*==\s*(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            save = re.sub(r'(?P<x>[\.\w\d_-]+)\s*=\s*(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            save = re.sub(r'(?P<x>[\.\w\d_-]+)\s*!=\s*(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            save = re.sub(r'(?P<x>[\.\w\d_-]+)\s*>=\s*(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            save = re.sub(r'(?P<x>[\.\w\d_-]+)\s*<=\s*(?P<y>[""\/\.\w\d_\s-]+)','\g<x>',save)
            ptn = '([\.\w\d_-]+)'
            tmp.append(re.findall(ptn,save))
        return tmp
    def clusterInfo(self,clusterFile):
        clusters = self.parseCSV(clusterFile)
        res = []
        for c in clusters:
            res.append(len(clusters[c]))
        print 'min-variable:',min(res)
        print 'max-variable:',max(res)
        print 'average-variable:',sum(res)*1.0/len(res)
        print 'cluster number:',len(res)
        print 'variable-variance:',np.std(res)
        
        inedge = {}
        ids = {}
        for c in clusters:
            inedge[c] = 0
            for cc in clusters[c]:
                ids[cc] = c
        
        pc = ParseCore(self.filePath)
        root = pc.parse()
        
        (retConditions,dummy) = self.genConditionByRoot(root)
        
        
        constrs = []
        
        for c in retConditions:
            for val in self.valueDict:
                if val in c:
                    c = c.replace(val,'"' + self.valueDict[val] + '"')
            for val in self.intChange:
                if val in c:
                    for v in self.intChange[val]:
                        c = c.replace(v,self.intChange[val][v])
            constrs.append(c)
        cutedge = 0
        
        for c in constrs:
            vs_list = self.getVarFromCondition(c)
            for vs in vs_list:
                l = len(vs)
                for i in range(l):
                    for j in range(i+1,l):
                        if 'auxVar' in vs[i] or 'auxVar' in vs[j]: continue
                        if ids[vs[i]] != ids[vs[j]]:
                            cutedge += 1
                        else:
                            inedge[ids[vs[i]]] += 1
        edges = inedge.values()
        print 'cutedge:',cutedge
        print 'max-edge',max(edges)
        print 'min-edge',min(edges)
        print 'std-edge',np.std(edges)
        print 'mean-edge',np.mean(edges)
        
        

class CascadeModelExtractor(ModelExtractor):
    def __init__(self,filePath):
        ModelExtractor.__init__(self,filePath)
    def getModel(self,useVariableStrength = False,clusterFile='',defaultStrength=2):
        pc = ParseCore(self.filePath)
        root = pc.parse()
        print '[PARAMETERS]'
        retVariables = self.getVariable(root)
        (retConditions,auxVar) = self.genConditionByRoot(root)
        for v in retVariables:
            print v
        for v in auxVar:
            print '__aux__ bool auxVar'+str(v) + ';'    
        print '[STRENGTHS]'
        print 'default: 2;'
        print '[CONSTRAINTS]'
        for c in retConditions:
            print c,
        print '[SEEDS]'
    def getSingleVariable(self, dType, node,value):
        ModelExtractor.getSingleVariable(self, dType, node,value)
        if dType == ENUM_TYPE_BOOL:
            return 'bool %s;' %(node.var)
        else:
            return '%s %s: %s;' %(ENUM_REV_DTYPES[dType],node.var,value)
        
    def getConstrExtractor(self,node):
        return CascadeConstrExtractor(node) 
    
    def getTestCases(self,fileName):
        pass
    def getVariableStrength(self):
        pass  


class ActsModelExtractor(ModelExtractor):
    def __init__(self,filePath):
        ModelExtractor.__init__(self,filePath)
        self.valueDict = {}
        self.count = 1
        self.intChange = {}
    def getVModel(self,defaultStrength,clusterFile):
        self.getModel(True,clusterFile,defaultStrength)    
    
    def getModel(self,useVariableStrength = False,clusterFile='',defaultStrength=2):
        pc = ParseCore(self.filePath)
        root = pc.parse()
        
        fp = open('model.txt','w')
        fp.write("[System]\n")
        fp.write("Name:Dong\n")
        fp.write('[Parameter]\n')
        print "[System]"
        print "Name:Dong"
        print '[Parameter]'
        retVariables = self.getVariable(root)
        (retConditions,auxVar) = self.genConditionByRoot(root)
        for v in retVariables:
            fp.write(v + '\n')
            print v
        for v in auxVar:
            fp.write('auxVar'+str(v) + '(boolean):TRUE,FALSE\n')
            print 'auxVar'+str(v) + '(boolean):TRUE,FALSE'  
        
        
        constrs = []
        
        for c in retConditions:
            for val in self.valueDict:
                if val in c:
                    c = c.replace(val,'"' + self.valueDict[val] + '"')
            for val in self.intChange:
                if val in c:
                    for v in self.intChange[val]:
                        c = c.replace(v,self.intChange[val][v])
            constrs.append(c)
        
        'use cluster information'  
        if useVariableStrength:
#             self.getVariableStrength(defaultStrength,clusterFile,fp)
#             self.getVariableStrengthOnCutedge(defaultStrength,clusterFile,constrs,fp)
            self.getBothVariableStrength(defaultStrength, clusterFile, constrs, fp)

        print '[Constraint]'
        fp.write('[Constraint]\n')
        for c in constrs:
            print c,
            fp.write(c)
        
#         self.knownConstraint(fp)
        fp.close()
        json.dump(self.valueDict,open('tmp/valueDict.txt','w'))
        json.dump(self.intChange,open('tmp/intChange.txt','w'))
    def knownConstraint(self,fp=None):
        fp.write('VENDOR_EMULATION\n')
        fp.write('PAYLOAD_NONE\n')
        fp.write('BOARD_EMULATION_QEMU_X86_Q35\n')
        fp.write('!BOOTSPLASH_IMAGE\n')
        fp.write('!VGA_BIOS\n')
        fp.write('!UPDATE_IMAGE\n')
        print 'VENDOR_EMULATION'
        print 'BOARD_EMULATION_QEMU_X86_Q35'
        print 'PAYLOAD_NONE'
        print '!BOOTSPLASH_IMAGE'
        print '!VGA_BIOS'
        print '!UPDATE_IMAGE'
#         print 'BOARD_EMULATION_QEMU_ARMV7'
#         print 'CONFIG_PLATFORM_LINUX'
#         print 'TARGET_x86_64'
        pass
        
    
    
    def getBothVariableStrength(self,defaultStrength,clusterFile,constrs,fp):
        print '[Relation]'
        fp.write('[Relation]\n')
        cluster = self.parseCSV(clusterFile)
        Rx = 1
        for c in cluster:
            if len(cluster[c]) < defaultStrength:
                continue
            curR = 'R' + str(Rx) + ':(' + ','.join(cluster[c]) + ',' + str(defaultStrength) + ')'
            Rx += 1
            print curR
            fp.write(curR + '\n')
        ids = {}
        for c in cluster:
            for cc in cluster[c]:
                ids[cc] = c
        result = {}
        for c in constrs:
            vs_list = self.getVarFromCondition(c)
            for vs in vs_list:
                l = len(vs)
                for i in range(l):
                    for j in range(i+1,l):
                        if 'auxVar' in vs[i] or 'auxVar' in vs[j]: continue
                        if ids[vs[i]] != ids[vs[j]]:
                            
                            tmp = [ids[vs[i]],ids[vs[j]]]
                            tmp.sort()
                            tmp = str(tmp[0]) + '_' + str(tmp[1])
                            if tmp not in result:
                                result[tmp] = []
                            if vs[i] not in result[tmp]:
                                result[tmp].append(vs[i])
                            if vs[j] not in result[tmp]:
                                result[tmp].append(vs[j])
        for r in result:
            if len(result[r]) < defaultStrength:
                continue
            curR = 'R' + str(Rx) + ':(' + ','.join(result[r]) + ',' + str(defaultStrength) + ')'
            Rx += 1
            print curR
            fp.write(curR + '\n')
             
    def getVariableStrength(self,defaultStrength,clusterFile,fp):
        print '[Relation]'
        fp.write('[Relation]\n')
        cluster = self.parseCSV(clusterFile)
        Rx = 1
        for c in cluster:
            if len(cluster[c]) < defaultStrength:
                continue
            curR = 'R' + str(Rx) + ':(' + ','.join(cluster[c]) + ',' + str(defaultStrength) + ')'
            Rx += 1
            print curR
            fp.write(curR + '\n')
        
          
    def getVariableStrengthOnCutedge(self,defaultStrength,clusterFile,constrs,fp):
        cluster = self.parseCSV(clusterFile)
        ids = {}
        for c in cluster:
            for cc in cluster[c]:
                ids[cc] = c
        result = {}
        for c in constrs:
            vs_list = self.getVarFromCondition(c)
            for vs in vs_list:
                l = len(vs)
                for i in range(l):
                    for j in range(i+1,l):
                        if 'auxVar' in vs[i] or 'auxVar' in vs[j]: continue
                        if ids[vs[i]] != ids[vs[j]]:
                            
                            tmp = [ids[vs[i]],ids[vs[j]]]
                            tmp.sort()
                            tmp = str(tmp[0]) + '_' + str(tmp[1])
                            if tmp not in result:
                                result[tmp] = []
                            if vs[i] not in result[tmp]:
                                result[tmp].append(vs[i])
                            if vs[j] not in result[tmp]:
                                result[tmp].append(vs[j])
        print '[Relation]'
        fp.write('[Relation]\n')
        Rx = 1
        for r in result:
            if len(result[r]) < defaultStrength:
                continue
            curR = 'R' + str(Rx) + ':(' + ','.join(result[r]) + ',' + str(defaultStrength) + ')'
            Rx += 1
            print curR
            fp.write(curR + '\n')
        
                    
            
        
        
    def splitter(self,s):
        def replacer(m):
            return m.group(0).replace(",", "\x00")
    
        parts = re.sub('".*?"', replacer, s).split(',') 
        parts = [p.replace("\x00", ",") for p in parts]
        return parts    
    
    """get the value output format in the final model
        Especially, there is no string type, instead the enum type is provided, so we should transform the value of 
        a string type to enum type, which will need to be reversed back latter
    """
    
    def getSingleVariable(self, dType, node,value):
        ModelExtractor.getSingleVariable(self, dType, node,value)
        if dType == ENUM_TYPE_BOOL:
            return '%s(boolean):TRUE,FALSE' %(node.var)
        elif dType == ENUM_TYPE_INT:
            valueList = value.split(',')
            newValueList = []
            
            used = []
            for val in valueList:
                realValue = int(val)
                if realValue > 21474836:
                    if node.var not in self.intChange:
                        self.intChange[node.var] = {}
                    if val not in self.intChange[node.var]:
                        cur = 1
                        for i in range(1024):
                            if str(i+1) not in valueList and str(i + 1) not in used:
                                cur = i + 1
                                break
                            used.append(cur)
                        self.intChange[node.var][val] = str(cur)
                    newValueList.append(self.intChange[node.var][val])
                else:
                    newValueList.append(val)
            return '%s(int):%s' %(node.var,','.join(newValueList))
        else:
            valueList = self.splitter(value)
            newValueList = []
            for val in valueList:
                realValue = val
                if val not in self.valueDict:
                    self.valueDict[val] = "ENUM" + str(self.count)
                    self.count += 1
                    realValue = self.valueDict[val]
                else:
                    realValue = self.valueDict[val]
                newValueList.append(realValue)
            value = ",".join(newValueList)
            return '%s(enum):%s' %(node.var,value)
    def getConstrExtractor(self,node):
        return ActsConstrExtractor(node)  
    
    def getTestCases(self,fileName):
        head = False
        headList = []
        testCases = []
        valueDict = json.load(open('tmp/valueDict.txt','r'))
        revValueDict = {}
        for v in valueDict.keys():
            revValueDict[valueDict[v]] = v
        intChange = json.load(open('tmp/intChange.txt','r'))
        revIntChange = {}
        for v in intChange:
            revIntChange[v] = {}
            for value in intChange[v].keys():
                revIntChange[v][intChange[v][value]] = value
        with open(fileName,'r') as fp:
            for l in fp:
                l = l.strip()
                if len(l) > 0 and l[0] == '#':
                    continue
                else:
                    if not head:
                        headList = l.split(',')
                        tmpList = []
                        for h in headList:
                            if not h.startswith('auxVar'):
                                tmpList.append(h)
                        headList = tmpList
                        head = True
                    else:
                        testCase = {}
                        values = l.split(',')
                        for i in range(len(headList)):
                            if values[i].startswith('ENUM'):
                                values[i] = revValueDict[values[i]]
                            if headList[i] in revIntChange and values[i] in revIntChange[headList[i]]:
                                values[i] = revIntChange[headList[i]][values[i]]
                            testCase[headList[i]] = values[i] 
                        testCases.append(testCase)
        return testCases    
                    
        
if __name__ == '__main__':
    pass