from __future__ import print_function

import sys
from ast import *


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
			(CodeNode, _State.Start, "append_code")
			],

		_State.TestBeforeAssertion : [
			(AssertionNode, _State.Assertion, "push"),
			(CodeNode, _State.TestBeforeAssertion, "append_code")
			],
		_State.Assertion : [
			(EndNode, _State.TestAfterAssertion, "pop"),
			(CodeNode, _State.Assertion, "append_code")
			],
		_State.TestAfterAssertion : [
			(EndNode, _State.Start, "pop"),
			(AssertionNode, _State.Assertion, "push"),
			(CodeNode, _State.TestAfterAssertion, "append_code")
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


class _Parser(object):

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

	def _run_ast_op( self, op_name, new_node ):
		op = getattr( self, "_ast_op_{}".format( op_name ) )
		op( new_node )

	def _ast_op_append( self, new_node ):
		self._node.children.append( new_node )

	def _ast_op_pop( self, new_node ):
		self._ast_op_append( new_node )
		self._node = self._node.parent

	def _ast_op_push( self, new_node ):
		self._ast_op_append( new_node )
		self._node = new_node

	def _ast_op_append_code( self, new_node ):
		children = self._node.children
		if children and isinstance( children[-1], CodeNode ):
			children[-1].end_line = new_node.end_line
		else:
			children.append( new_node )

	def _step( self ):

		if self._state in [_State.Accept, _State.Reject]:
			return

		self._line_no = self._line_no + 1
		line = _Parser._trim_newline_or_check_eof( self._infile.readline() )
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


def parse_test_input( infile ):
	return _Parser( infile ).run()

