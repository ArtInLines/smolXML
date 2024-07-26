from __future__ import annotations

# @TODO: Currently, any whitespace strings that are children of xml elements just get ignored. This is not desired, but not a huge issue atm

class StrBuf():
	idx: int = 0
	str: str = ""
	def __init__(self, str: str):
		self.str = str
		self.idx = 0

	def isDone(self) -> bool:
		return self.idx >= len(self.str)

	def peek(self, n: int = 1) -> str:
		assert(self.idx + n <= len(self.str))
		return self.str[self.idx:self.idx+n]

	def read(self, n: int = 1) -> str:
		res = self.peek(n)
		self.idx += n
		return res

	def skipWhitespace(self) -> StrBuf:
		while self.idx < len(self.str) and self.str[self.idx].isspace():
			self.idx += 1
		return self

	def skipUntil(self, end: str) -> StrBuf:
		l = len(end)
		while self.idx < len(self.str) and self.str[self.idx:self.idx+l] != end:
			self.idx += 1
		if self.idx < len(self.str):
			self.idx += l
		return self

	def skipComments(self, start: str, end: str) -> StrBuf:
		l = len(start)
		cont = True
		while self.str[self.idx:self.idx+l] == start:
			self.idx += l
			self.skipUntil(end)
		return self

	def skipCommentsWhitespace(self, start: str, end: str) -> StrBuf:
		i = -1
		while i != self.idx:
			i = self.idx
			self.skipWhitespace()
			self.skipComments(start, end)
		return self

	def alphaStrNumEx(self, allowedChars: str) -> str:
		start = self.idx
		while self.idx < len(self.str) and (self.str[self.idx].isalpha() or self.str[self.idx].isdigit() or self.str[self.idx] in allowedChars):
			self.idx += 1
		return self.str[start:self.idx]

	def alphaNumStr(self) -> str:
		return self.alphaStrNumEx("")

	def quotedStr(self) -> str:
		assert(self.idx < len(self.str))
		assert(self.str[self.idx] in ('"', "'"))
		quote = self.str[self.idx]
		res = ""
		escaped = False
		self.idx += 1
		while self.idx < len(self.str) and (self.str[self.idx] != quote or escaped):
			c = self.str[self.idx]
			if escaped:
				escaped = False
				res += c
			else:
				if c == '\\':
					escaped = true
				else:
					res += c
			self.idx += 1
		assert(self.str[self.idx] == quote)
		self.idx += 1
		return res

	def strUntil(self, end: str) -> str:
		start = self.idx
		l = len(end)
		while self.idx < len(self.str) and self.str[self.idx:self.idx+l] != end:
			self.idx += 1
		return self.str[start:self.idx]


class Element():
	type: str = ""
	attrs: dict[str, str] = {}
	children: list[Element|str] = []
	empty: bool = False
	def __init__(self, type: str):
		self.type = type
		self.attrs = {}
		self.children = []
		self.empty = False

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		s = "Element {\n"
		s += "  type: " + self.type + ",\n"
		keys = self.attrs.keys()
		if len(keys) == 0:
			s += "  attrs: {},\n"
		else:
			s += "  attrs: {\n"
			for k in keys:
				s += "    " + k + ": '" + self.attrs[k] + "',\n"
			s += "  },\n"
		if len(self.children) == 0:
			s += "  children: [],\n"
		else:
			s += "  children: [,\n"
			for child in self.children:
				cs = child.__str__()
				if isinstance(child, str):
					cs = "'" + cs + "'"
				s += "    " + "\n    ".join(cs.splitlines()) + ",\n"
			s += "  ],\n"
		s += "}"
		return s

	def __getitem__(self, key: str|int) -> Element|str|None:
		if isinstance(key, str):
			return self.getFirstChildByName(key)
		elif isinstance(key, int):
			return self.getChildByIndex(key)
		else:
			return None

	def __setitem__(self, key: str|int, val: Element|str):
		idx: int = -1
		if isinstance(key, str):
			idx = self.getFirstChildIndexByName(key)
		elif isinstance(key, int):
			idx = key
		if idx < 0:
			return
		self.children[idx] = val

	def attrsToXML(self) -> str:
		s = ""
		for k, v in self.attrs.items():
			s += ' ' + k + '="' + v + '"'
		return s

	def toXML(self, indentLevel: int = 0) -> str:
		indent = "  " * indentLevel
		if self.empty:
			return indent + "<" + self.type + self.attrsToXML() + " />"
		else:
			s = indent + "<" + self.type + self.attrsToXML() + ">"
			feedLine = True
			if len(self.children) > 1:
				for child in self.children:
					if isinstance(child, str):
						feedLine = False
						break
			for child in self.children:
				if feedLine:
					s += "\n"
				if isinstance(child, str):
					s += child
				else:
					s += child.toXML(feedLine*(indentLevel+1))
			s += feedLine*('\n'+indent) + "</" + self.type + ">"
			return s

	def getFirstChildIndexByName(self, name: str) -> int:
		for i in len(self.children):
			child = self.children[i]
			if isinstance(child, Element) and child.type == name:
				return i
		return -1

	def getChildByIndex(self, index: int) -> Element|str:
		return self.children[index]

	def getFirstChildByName(self, name: str) -> Element|None:
		for child in self.children:
			if isinstance(child, Element) and child.type == name:
				return child
		return None

	def getAllChildrenByName(self, name: str) -> List[Element]:
		res = []
		for child in self.children:
			if isinstance(child, Element) and child.type == name:
				res.append(child)
		return res

	def getFirstChildByPath(self, path: str|List[str]) -> Element|None:
		if isinstance(path, str):
			return self.getFirstChildByName(path)
		o = self
		for name in path:
			o = getFirstChildByName(name)
			if o == None:
				return None
		return o

	def getAllChildrenByPath(self, path: str|List[str]) -> List[Element]:
		if isinstance(path, str):
			return self.getAllChildrenByName(path)
		l1 = [self]
		for name in path:
			l2 = []
			for o in l1:
				l2.extend(o.getAllChildrenByName(name))
			l1 = l2
		return l1

	def getStrVal(self, joinStr: str = "", recursive: bool = True) -> str:
		res = ""
		for i in range(len(self.children)):
			js: str = (i > 0) * joinStr
			child = self.children[i]
			if isinstance(child, str):
				res += js + child
			elif recursive:
				res += js + child.getStrVal(joinStr, recursive)
		return res


def xmlSkip(sb: StrBuf) -> StrBuf:
	return sb.skipCommentsWhitespace("<!--", "-->")

def parseElOrStr(sb: StrBuf) -> tuple[Element|str, StrBuf]:
	s = sb.skipComments("<!--", "-->").strUntil('<')
	if len(s):
		return (s, sb)
	else:
		return parseElement(sb)

def parseElement(sb: StrBuf) -> tuple[Element, StrBuf]:
	assert(sb.read() == '<')
	xmlSkip(sb)
	el = Element(sb.alphaStrNumEx(':'))
	while xmlSkip(sb).peek() not in '/>':
		key = sb.alphaStrNumEx(":")
		assert(xmlSkip(sb).read() == '=')
		val = xmlSkip(sb).quotedStr()
		assert(key not in el.attrs)
		el.attrs[key] = val
	if sb.read() == '/':
		assert(xmlSkip(sb).read() == '>')
		el.empty = True
		return (el, sb)
	else:
		# @Note: If '/' wasn't read, '>' must have been read
		sb = xmlSkip(sb)
		while sb.peek(2) != "</":
			x, sb = parseElOrStr(sb)
			if not isinstance(x, str) or len(x) > 0:
				el.children.append(x)
			sb = xmlSkip(sb)
		sb.read(2)
		sb = xmlSkip(sb)
		assert(el.type == sb.alphaStrNumEx(":"))
		sb = xmlSkip(sb)
		assert(sb.read() == ">")
	return (el, sb)

def parseStrBuf(sb: StrBuf) -> Element:
	sb = xmlSkip(sb)
	el, sb = parseElOrStr(sb)
	sb = xmlSkip(sb)
	assert(sb.isDone())
	return el

def parseStr(s: str) -> Element:
	return parseStrBuf(StrBuf(s))

def parseFile(fname: str) -> Element:
	with open(fname, "r", encoding="utf8") as f:
		return parseStrBuf(StrBuf(f.read()))
