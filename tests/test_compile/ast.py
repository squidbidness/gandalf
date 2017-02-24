from __future__ import print_function

import cStringIO
import re
import sys

class Node(object):

	def __init__( self, line_no, parent=None, children=None ):
		if children is None:
			children = []
		self._line_no = line_no
		self.parent = parent
		self.children = children

		for child in children:
			child.parent = self

	def __lt__( self, other ):
		return self._line_no < other._line_no

	@classmethod
	def make_parse_regex( cls, sub_regex ):
		return re.compile( '^\s*@\s*{}\s*$'.format(sub_regex) )

	@classmethod
	def parse( cls, parent, line_no, line ):
		if cls == Node:
			raise NotImplementedError
		result = cls.regex.match( line ) if line else None
		return cls( line_no, parent=parent ) if result else None

	def tree_string( self ):
		result = cStringIO.StringIO()
		self.print_tree( 0, result )
		return result.getvalue()

	def print_tree( self, level=0, result=sys.stdout ):
		print( "  " * level + self.__str__(), end="", file=result )
		if self.children:
			print( " [", file=result )
			for c in self.children:
				c.print_tree( level + 1, result )
			print( "  " * level + "]", file=result )
		else:
			print( file=result )

	def __eq__( self, other ):
		if self.__class__ != other.__class__:
			return False
		if self._line_no != other._line_no:
			return False
		if len( self.children ) != len( other.children ):
			return False
		succeeded = True
		for i in range( 0, len( self.children ) ):
			if self.children[i] != other.children[i]:
				return False
		return True

	def __ne__( self, other ):
		return not self.__eq__( other )

	def __str__( self, child_attrs=[] ):
		result = "{}:{}".format( self.__class__.__name__, self._line_no )
		for attr in child_attrs:
			value = getattr(self, attr)
			result = result + ", {}={}".format(
					attr,
					'"{}"'.format( value ) if isinstance(value, str) else value
					)
		return result


class RootNode(Node):

	def __init__( self, children=None ):
		Node.__init__( self, 0, children=children )


class CodeNode(Node):

	not_regex = re.compile( '\s*@.*' )

	def __init__( self, line_no, parent=None, end_line=None ):
		Node.__init__( self, line_no, parent=parent )
		if end_line == None:
			end_line = line_no + 1

		self.end_line = end_line

	def __eq__( self, other ):
		return self.end_line == other.end_line and Node.__eq__( self, other )

	def __str__( self ):
		return Node.__str__( self, ['end_line'] )

	@classmethod
	def parse( cls, parent, line_no, line ):
		if line != None and not cls.not_regex.match( line ):
			return CodeNode( line_no, parent=parent )
		else:
			return None


class EndNode(Node):

	regex = Node.make_parse_regex('}')

	def __init__( self, line_no, parent=None ):
		Node.__init__( self, line_no, parent=parent )


class TestNode(Node):
	regex = Node.make_parse_regex( 'TEST\s*(\w+)\s*{' )

	def __init__( self, line_no, test_name, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )
		self.name = test_name

	def __eq__( self, other ):
		return self.name == other.name and Node.__eq__( self, other )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line ) if line else None
		return TestNode( line_no, result.group(1), parent=parent, children=[] ) if result else None

	def __str__( self ):
		return Node.__str__( self, ['name'] )


class AssertionNode(Node):
	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		for sub in cls.__subclasses__():
			result = Node.parse.im_func( sub, parent, line_no, line )
			if result:
				return result
		
		return None


class ExpectNode(AssertionNode):
	regex = AssertionNode.make_parse_regex( 'EXPECT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		AssertionNode.__init__( self, line_no, parent=parent, children=children )


class ExpectNotNode(AssertionNode):
	regex = AssertionNode.make_parse_regex( 'EXPECT_NOT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		AssertionNode.__init__( self, line_no, parent=parent, children=children )


class AssertNode(AssertionNode):
	regex = AssertionNode.make_parse_regex( 'ASSERT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		AssertionNode.__init__( self, line_no, parent=parent, children=children )


class AssertNotNode(AssertionNode):
	regex = AssertionNode.make_parse_regex( 'ASSERT_NOT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		AssertionNode.__init__( self, line_no, parent=parent, children=children )


class EofNode(Node):

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		return EofNode( line_no, parent=parent ) if line is None else None


class ErrorNode(Node):

	def __init__( self, line_no, line, parent=None, message=None ):
		Node.__init__( self, line_no, parent=parent )

		if message is None:
			message = "unexpected line: \"{line}\"".format( line=line )
		self.line = line
		self.msg = (
				'line:{} error: While processing {}:\n' 
				'    {}'.format( line_no, parent, message )
				)

	def __eq__( self, other ):
		return self.line == other.line and Node.__eq__( self, other )

	def __str__( self ):
		return Node.__str__( self, ['line', 'msg'] )
