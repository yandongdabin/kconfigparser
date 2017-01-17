# -*- coding: utf-8 -*-
'''
Created on 2016-12-26

@author: otcaix
'''

class Utils(object):
    "得到反向select关系"
    @staticmethod
    def getRdDict(queue):
        select_dict = {}
        while not queue.empty():
            cur = queue.get()
            for child in cur.children:
                queue.put(child)
            for s in cur.select:
                if cur.var not in select_dict:
                    select_dict[cur.var] = {}
                select_dict[cur.var][s._name] = 0
        rd_dict = {}    
        for s in select_dict:
            for ss in select_dict[s]:
                if ss not in rd_dict:
                    rd_dict[ss] = {}
                rd_dict[ss][s] = 0     
        return rd_dict

if __name__ == '__main__':
    pass