from __future__ import print_function

import cStringIO
import json
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

	@classmethod
	def make_parse_regex( cls, sub_regex ):
		return re.compile( '^\s*@\s*{}\s*$'.format(sub_regex) )

	@classmethod
	def parse( cls, parent, line_no, line ):
		raise NotImplementedError

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
		for i in range( 0, len(self.children) ):
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

	def __init__( self, line_no, parent=None ):
		Node.__init__( self, line_no, parent=parent )

	@classmethod
	def parse( cls, parent, line_no, line ):
		if line != None and line != "" and not cls.not_regex.match( line ):
			return CodeNode( line_no, parent=parent )
		else:
			return None


class EndNode(Node):

	regex = Node.make_parse_regex('}')

	def __init__( self, line_no, parent=None ):
		Node.__init__( self, line_no, parent=parent )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return EndNode( line_no, parent=parent ) if result else None


class TestNode(Node):
	regex = Node.make_parse_regex( 'TEST\s*(\w+)\s*{' )

	def __init__( self, line_no, test_name, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )
		self.name = test_name

	def __eq__( self, other ):
		return self.name == other.name and Node.__eq__( self, other )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return TestNode( line_no, result.group(1), parent=parent, children=[] ) if result else None

	def __str__( self ):
		return Node.__str__( self, ['name'] )


class ExpectNode(Node):
	regex = Node.make_parse_regex( 'EXPECT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return ExpectNode( line_no, parent=parent ) if result else None


class ExpectNotNode(Node):
	regex = Node.make_parse_regex( 'EXPECT_NOT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return ExpectNotNode( line_no, parent=parent ) if result else None


class AssertNode(Node):
	regex = Node.make_parse_regex( 'ASSERT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return AssertNode( line_no, parent=parent ) if result else None


class AssertNotNode(Node):
	regex = Node.make_parse_regex( 'ASSERT_NOT\s*{' )

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		result = cls.regex.match( line )
		return AssertNotNode( line_no, parent=parent ) if result else None


class EofNode(Node):

	def __init__( self, line_no, parent=None, children=None ):
		Node.__init__( self, line_no, parent=parent, children=children )

	@classmethod
	def parse( cls, parent, line_no, line ):
		return EofNode( line_no, parent=parent ) if not line else None


class ErrorNode(Node):

	def __init__( self, line_no, line, parent=None, message=None ):
		Node.__init__( self, line_no, parent=parent )

		line = self.trim_newline( line )
		if message is None:
			message = "unexpected line: \"{line}\"".format( line=line )
		self.line = line
		self.msg = (
				'line:{} error: While processing {}:\n' 
				'    {}'.format( line_no, parent, message )
				)

	def __eq__( self, other ):
		return self.line == other.line and Node.__eq__( self, other )

	def trim_newline( self, line ):
		return line[:-1] if line[-1] == "\n" else (
				"EOF" if line == "" else line )

	@classmethod
	def parse( cls, parent, line_no, line ):
		return ErrorNode( line_no, line, parent=parent )

	def __str__( self ):
		return Node.__str__( self, ['line', 'msg'] )


class _State:
	Start = 0
	Reject = 1
	Accept = 2

	Test = 10
	Assertion = 11


class _AstOp:
	Push = 0
	Pop = 1
	Append = 2


class Parser(object):
	
	_state_trans = {
			_State.Start : [
				(EofNode, _State.Accept, _AstOp.Append),
				(TestNode, _State.Test, _AstOp.Push),
				(CodeNode, _State.Start, _AstOp.Append)
				],

			_State.Test : [
				(EndNode, _State.Start, _AstOp.Pop),
				(ExpectNode, _State.Assertion, _AstOp.Push),
				(ExpectNotNode, _State.Assertion, _AstOp.Push),
				(AssertNode, _State.Assertion, _AstOp.Push),
				(AssertNotNode, _State.Assertion, _AstOp.Push),
				(CodeNode, _State.Test, _AstOp.Append)
				],
			_State.Assertion : [
				(EndNode, _State.Test, _AstOp.Pop),
				(CodeNode, _State.Assertion, _AstOp.Append)
				]
			}

	def __init__( self, infile ):
		self._infile_init_pos = infile.tell()
		self._infile = infile
		self._reset()

	def _reset( self ):
		self._state = _State.Start
		self._ast_root = RootNode()
		self._node = self._ast_root
		self._line_no = 0
		self._infile.seek( self._infile_init_pos )

	def __str__( self ):
		return (
"""
_infile_init_pos = {}
_infile.getvalue() = (
{}
)
_state = {}
_ast_root.tree_string() = (
{}
)
_node.tree_string() = (
{}
)
_line_no = {}

""".format(
		self._infile_init_pos,
		self._infile.getvalue(),
		self._state,
		self._ast_root.tree_string(),
		self._node.tree_string(),
		self._line_no
		) )

	def _step( self ):

		if self._state in [_State.Accept, _State.Reject]:
			return

		self._line_no = self._line_no + 1
		line = self._infile.readline()
		transitions = self._state_trans[self._state]

		for node_class, next_state, action in transitions:
			result = node_class.parse( self._node, self._line_no, line )

			if result is not None:
				self._node.children.append( result )
				if action == _AstOp.Push:
					self._node = result
				elif action == _AstOp.Pop:
					self._node = self._node.parent
				elif action == _AstOp.Append:
					pass
				else:
					raise NotImplementedError

				self._state = next_state
				return

		err = ErrorNode( self._line_no, line, parent=self._node )
		self._node.children.append( err )
		self._node = err
		self._state = _State.Reject

	def run( self ):
		while self._state not in [_State.Accept, _State.Reject]:
			self._step()

		if self._state == _State.Accept:
			succeeded = True
		elif self._state == _State.Reject:
			if self._node is ErrorNode:
				print( self._node.msg, file=sys.stderr )
			succeeded = False
		else:
			raise NotImplementedError

		result = (succeeded, self._ast_root)
		self._reset()
		return result

