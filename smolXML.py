from __future__ import annotations
from typing import List

# @TODO: Currently, any whitespace strings that are children of xml elements just get ignored. This is not desired, but not a huge issue atm

class Cursor():
	file: str = ""
	row:  int = 0
	col:  int = 1
	def __init__(self, file: str, col: int, row: int):
		self.file = file
		self.col  = col
		self.row  = row

	def getPos(self) -> str:
		return str(self.col) + ":" + str(self.row)

	def err(self, msg: str):
		if self.file != "":
			print(f"Error at {self.file}:{self.getPos()} - {msg}")
		else:
			print(f"Error at {self.getPos()} - {msg}")
		exit(1)


class StrBuf():
	idx:  int = 0
	bol:  int = 0
	col:  int = 1
	text: str = ""
	file: str = ""
	def __init__(self, text: str):
		self.text = text

	@staticmethod
	def fromFile(fname: str) -> StrBuf:
		with open(fname, "rb") as f:
			s = f.read().decode("utf8")
			sb = StrBuf(s)
			sb.file = fname
			return sb

	def getCursor(self) -> Cursor:
		return Cursor(self.file, self.col, self.idx - self.bol)

	def err(self, msg: str):
		self.getCursor().err(msg)

	def isDone(self) -> bool:
		return self.idx >= len(self.text)

	def expectDone(self, expected: bool = True) -> StrBuf:
		if self.isDone() != expected:
			self.err("Expected file to be finished, but it continues")
		return self

	def expectReadable(self, n: int = 1) -> StrBuf:
		if self.idx + n > len(self.text):
			self.err("File ended unexpectedly")
		return self

	def peek(self, n: int = 1) -> str:
		self.expectReadable(n)
		return self.text[self.idx:self.idx+n]

	def skipOne(self) -> StrBuf:
		self.expectReadable()
		if self.text[self.idx] == '\n':
			self.col += 1
			self.bol = self.idx + 1
		self.idx += 1
		return self

	def skip(self, n: int = 1) -> StrBuf:
		while n > 0:
			self.skipOne()
			n -= 1
		return self

	def read(self, n: int = 1) -> str:
		res = self.peek(n)
		self.skip(n)
		return res

	def readExpected(self, expected: str) -> StrBuf:
		s = self.read(len(expected))
		if s != expected:
			self.err("Expected '" + expected + "', but found '" + s + "'")
		return self

	def skipWhitespace(self) -> StrBuf:
		while self.idx < len(self.text) and self.text[self.idx].isspace():
			self.skipOne()
		return self

	# @TODO: Make sure this logs an error if "end" wasn't found
	def skipUntil(self, end: str) -> StrBuf:
		l = len(end)
		while self.idx < len(self.text) and self.text[self.idx:self.idx+l] != end:
			self.skipOne()
		if self.idx < len(self.text):
			self.skip(l)
		return self

	def skipComments(self, start: str, end: str) -> StrBuf:
		l = len(start)
		cont = True
		while self.idx < len(self.text) and self.text[self.idx:self.idx+l] == start:
			self.skip(l)
			self.skipUntil(end)
		return self

	def skipCommentsWhitespace(self, start: str, end: str) -> StrBuf:
		i = -1
		while self.idx < len(self.text) and i != self.idx:
			i = self.idx
			self.skipWhitespace()
			self.skipComments(start, end)
		return self

	def alphaNumericEx(self, allowedChars: str) -> str:
		start = self.idx
		while self.idx < len(self.text) and self.text[self.idx].isalpha() or self.text[self.idx].isdigit() or self.text[self.idx] in allowedChars:
			self.skipOne()
		res = self.text[start:self.idx]
		if res == "":
			msg = "Expected an alphanumeric string, but "
			if self.idx >= len(self.text):
				msg += "found end of file instead"
			else:
				msg += "found '" + self.text[self.idx] + "' instead"
			self.err(msg)
		return res

	def alphaNumeric(self) -> str:
		return self.alphaNumericEx("")

	def quotedStr(self) -> str:
		self.expectReadable()
		startCursor = self.getCursor()
		if self.text[self.idx] not in ('"', "'"):
			startCursor.err("Expected to read a string starting with \" or '")
		quote = self.text[self.idx]
		res = ""
		escaped = False
		self.idx += 1 # @Note: Don't need to use "skipOne", because we know the current character is a quote
		while self.text[self.idx] != quote or escaped:
			c = self.text[self.idx]
			if escaped:
				escaped = False
				res += c
			else:
				if c == '\\':
					escaped = True
				else:
					res += c
			self.skipOne()
		if self.text[self.idx] != quote:
			if quote == "'":
				self.err("Expected \"'\" to end the quoted string started at " + startCursor.getPos())
		self.idx += 1 # see note above
		return res

	def strUntil(self, end: str) -> str:
		self.expectReadable()
		start = self.idx
		l = len(end)
		while self.text[self.idx:self.idx+l] != end:
			self.skipOne()
		return self.text[start:self.idx]


class Element():
	type: str = ""
	attrs: dict[str, str] = {}
	children: list[Element|str] = []
	empty: bool = False
	def __init__(self, type: str):
		self.type     = type
		self.attrs    = {}
		self.children = []
		self.empty    = False

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
		for i in range(len(self.children)):
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
			o = o.getFirstChildByName(name) # type: ignore
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

	def getFirstElementOfType(self, typ: str) -> Element|None:
		if self.type == typ:
			return self
		for child in self.children:
			if isinstance(child, Element):
				res = child.getFirstElementOfType(typ)
				if res is not None:
					return res
		return None

	def getAllElementsOfType(self, typ: str) -> List[Element]:
		res = []
		if self.type == typ:
			res.append(self)
		for child in self.children:
			if isinstance(child, Element):
				res += child.getAllElementsOfType(typ)
		return res

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


XML_NAME_ALLOWED_CHARS = ":-_"

def xmlSkip(sb: StrBuf) -> StrBuf:
	return sb.skipCommentsWhitespace("<!--", "-->")

def parseElOrStr(sb: StrBuf) -> tuple[Element|str, StrBuf]:
	s = xmlSkip(sb).strUntil('<')
	if len(s):
		return (s, sb)
	else:
		return parseElement(sb)

def parseElement(sb: StrBuf) -> tuple[Element, StrBuf]:
	sb.readExpected('<')
	xmlSkip(sb)
	el = Element(sb.alphaNumericEx(XML_NAME_ALLOWED_CHARS))
	while xmlSkip(sb).peek() not in '/>':
		key = sb.alphaNumericEx(XML_NAME_ALLOWED_CHARS)
		xmlSkip(sb).readExpected('=')
		val = xmlSkip(sb).quotedStr()
		if key in el.attrs:
			sb.err("The same key is not allowed to be specified twice in an XML-Element. Read duplicate key: '" + key + "'")
		el.attrs[key] = val
	if sb.read() == '/':
		xmlSkip(sb).readExpected('>')
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
		endType = sb.alphaNumericEx(XML_NAME_ALLOWED_CHARS)
		if el.type != endType:
			sb.err(f"Unexpected end-element. Expected </{el.type}>, but received: </{endType}>")
		sb = xmlSkip(sb)
		sb.readExpected('>')
	return (el, sb)

def parseStrBuf(sb: StrBuf) -> Element:
	sb = xmlSkip(sb)
	el, sb = parseElOrStr(sb)
	sb = xmlSkip(sb)
	sb.expectDone()
	if isinstance(el, str):
		sb.err("Expected XML, but found only a string '" + el + "'")
	return el # type: ignore

def parseStr(s: str) -> Element:
	return parseStrBuf(StrBuf(s))

def parseFile(fname: str) -> Element:
	return parseStrBuf(StrBuf.fromFile(fname))
