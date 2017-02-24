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


class _State:
	Start = 0
	Reject = 1
	Accept = 2

	TestBeforeAssertion = 10
	TestAfterAssertion = 11
	Assertion = 12

class _StateTrans:
	m = {
		_State.Start : [
			(EofNode, _State.Accept, "append"),
			(TestNode, _State.TestBeforeAssertion, "push"),
			(CodeNode, _State.Start, "append")
			],

		_State.TestBeforeAssertion : [
			(AssertionNode, _State.Assertion, "push"),
			(CodeNode, _State.TestBeforeAssertion, "append")
			],
		_State.Assertion : [
			(EndNode, _State.TestAfterAssertion, "pop"),
			(CodeNode, _State.Assertion, "append")
			],
		_State.TestAfterAssertion : [
			(EndNode, _State.Start, "pop"),
			(AssertionNode, _State.Assertion, "push"),
			(CodeNode, _State.TestAfterAssertion, "append")
			]
		}

class _InvalidTrans:
	m = {
			s : [ n for n in [ CodeNode, EndNode, TestNode, AssertionNode, EofNode ]
					if n not in _StateTrans.m[s] ]
				for s in _StateTrans.m
			}

class _InvalidTransErrors:
	m = {
		_State.Start : {
			EndNode : "Unmatched @}",
			AssertionNode : "Assertion block outside of a @TEST block",
			},
		_State.TestBeforeAssertion : {
			EndNode : "@TEST block contains no assertion blocks",
			TestNode : "@TEST block nested inside another @TEST",
			EofNode : "@TEST not closed before EOF"
			},
		_State.Assertion : {
			TestNode : "@TEST block inside an assertion block",
			AssertionNode : "Assertion block nested inside another assertion block",
			EofNode : "Assertion block not closed before EOF"
			},
		_State.TestAfterAssertion : {
			TestNode : "@TEST block nested inside another @TEST",
			EofNode : "@TEST block not closed before EOF"
			}
		}


class Parser(object):

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

	@classmethod
	def _trim_newline_or_check_eof( cls, line ):
		"Convert EOF line to None and trim newline from end of line if present"
		return None if line == "" else (
				line[0:-1] if line[-1] == "\n" else line )

	def _get_invalid_transition_error( self, line ):
		err_msg = None
		for node_cls in _InvalidTrans.m[self._state]:
			if node_cls.parse( self._node, self._line_no, line ):
				err_msg = _InvalidTransErrors.m[self._state][node_cls]
				break

		return ErrorNode( self._line_no, line, parent=self._node, message=err_msg )

	def _run_ast_op( self, op_name, parsed_node ):
		op = getattr( self, "_ast_op_{}".format( op_name ) )
		op( parsed_node )

	def _ast_op_append( self, node ):
		self._node.children.append( node )

	def _ast_op_pop( self, node ):
		self._ast_op_append( node )
		self._node = self._node.parent

	def _ast_op_push( self, node ):
		self._ast_op_append( node )
		self._node = node

	def _step( self ):

		if self._state in [_State.Accept, _State.Reject]:
			return

		self._line_no = self._line_no + 1
		line = Parser._trim_newline_or_check_eof( self._infile.readline() )
		transitions = _StateTrans.m[self._state]

		for node_class, next_state, action in transitions:
			result = node_class.parse( self._node, self._line_no, line )

			if result is not None:
				self._run_ast_op( action, result )
				self._state = next_state
				return

		err = self._get_invalid_transition_error( line )

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

