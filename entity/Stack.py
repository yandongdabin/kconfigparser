# -*- coding: utf-8 -*-

"""

自定义栈

"""

class Stack(object):
	def __init__(self,debug=False):
		self.items = []
		self.debug = debug
		self.times = 0
	def printStack(self):
		for i in self.items:
			print i
	def push(self,item):
		self.times += 1
		self.items.append(item)
		if self.debug:
			print 'push'
			print item
			print self.times
			print '---------'
	def pop(self):
		self.times -= 1
		if self.debug:         
			print 'pop'
			print self.times
			print '---------'
		if(self.isEmpty() == False):
			return self.items.pop()
		else:
			return None
	def peek(self):
		if(self.isEmpty() == False):
			return self.items[len(self.items) - 1]
		else:
			return None
	def clear(self):
		self.items = []
	def isEmpty(self):
		return len(self.items) == 0
	def __getattr__(self,attr):
		return getattr(self.items,attr) 
	def contains(self,key):
		return key in self.items   
if __name__ == "__main__":
	stack = Stack()
	stack.push(1)
	stack.push(2)
	print stack.pop()
	
	