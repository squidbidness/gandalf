from parser import *
import unittest

def runParserTest( parser_test, input_str, expected ):
	input_file = cStringIO.StringIO( input_str )
	parser = Parser( input_file )
	succeeded, result = parser.run()
	input_file.close()
	parser_test.assertEqual(
			expected,
			(succeeded, result),
			"For _ParserTestCase {}:\nExpected:\n{}\nActual:\n{}\n".format(
					parser_test, expected[1].tree_string(),
					result.tree_string()
					)
			)


class ParserTest( unittest.TestCase ):

	def test_empty_test( self ):
		runParserTest(
				self,
				"""
					@TEST test_empty_test {
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						TestNode( 2, 'test_empty_test', children=[
							ErrorNode( 3, "					@}" )
							] )
						] )
					)
				)

	def test_brief_valid( self ):
		runParserTest(
				self,
				"""
					#include <nonsense>
					@TEST test_brief_valid {
						setup();
						@EXPECT {
							do_the_thing();
						@}
						
						@EXPECT_NOT {
							do_the_other_thing();
						@}
						
					@}
					
					""",
				(
					True,
					RootNode( children=[
						CodeNode( 1 ),
						CodeNode( 2 ),
						TestNode( 3, 'test_brief_valid', children=[
							CodeNode( 4 ),
							ExpectNode( 5, children=[
								CodeNode( 6 ),
								EndNode( 7 )
								] ),
							CodeNode( 8 ),
							ExpectNotNode( 9, children=[
								CodeNode( 10 ),
								EndNode( 11 )
								] ),
							CodeNode( 12 ),
							EndNode( 13 )
							] ),
						CodeNode( 14 ),
						CodeNode( 15 ),
						EofNode( 16 )
						] )
					)
				)

	def test_unclosed_test( self ):
		runParserTest(
				self,
				"""
					@TEST unclosed {
						do_the_thing();
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						TestNode( 2, "unclosed", children=[
							CodeNode( 3 ),
							CodeNode( 4 ),
							ErrorNode( 5, None )
							] )
						] )
					)
				)

	def test_unnamed_test( self ):
		runParserTest(
				self,
				"""
					@TEST {
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@TEST {" )
						] )
					)
				)

	def test_mismatched_closing_brace( self ):
		runParserTest(
				self,
				"""
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@}" )
						] )
					)
				)

	def test_test_without_assertions( self ):
		runParserTest(
				self,
				"""
					@TEST empty {
						do_the_thing();
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						TestNode( 2, "empty", children=[
							CodeNode( 3 ),
							ErrorNode( 4, "					@}" )
							] )
						] )
					)
				)

	def test_expect_outside_test( self ):
		runParserTest(
				self,
				"""
					@EXPECT {
						do_the_thing();
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@EXPECT {" )
						] )
					)
				)

	def test_expect_not_outside_test( self ):
		runParserTest(
				self,
				"""
					@EXPECT_NOT {
						do_the_thing();
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@EXPECT_NOT {" )
						] )
					)
				)

	def test_assert_outside_test( self ):
		runParserTest(
				self,
				"""
					@ASSERT {
						do_the_thing();
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@ASSERT {" )
						] )
					)
				)

	def test_assert_not_outside_test( self ):
		runParserTest(
				self,
				"""
					@ASSERT_NOT {
						do_the_thing();
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						ErrorNode( 2, "					@ASSERT_NOT {" )
						] )
					)
				)

	def test_test_inside_another( self ):
		runParserTest(
				self,
				"""
					@TEST outer {
						do_the_thing();
						@TEST inner {
							do_the_inner_thing();
						@}
					@}
					""",
				(
					False,
					RootNode( children=[
						CodeNode( 1 ),
						TestNode( 2, "outer", children=[
							CodeNode( 3 ),
							ErrorNode( 4, "						@TEST inner {" )
							] )
						] )
					)
				)

	def test_nested_assertions( self ):

		all_assertion_errors = []

		types = {
				"EXPECT" : ExpectNode,
				"EXPECT_NOT" : ExpectNotNode,
				"ASSERT" : AssertNode,
				"ASSERT_NOT" : AssertNotNode
				}

		for keyword_i, node_class_i in types.iteritems():
			for keyword_j, node_class_j in types.iteritems():
				try:
					runParserTest(
							self,
							"""
								@TEST test {{
									@{} {{
										do_the_thing();
										@{} {{
											do_the_nested_thing();
										@}}
										do_the_after_thing();
									@}}
								@}}
								""".format( keyword_i, keyword_j ),
							(
								False,
								RootNode( children=[
									CodeNode( 1 ),
									TestNode( 2, "test", children=[
										node_class_i( 3, children=[
											CodeNode( 4 ),
											ErrorNode(
													5,
													"										@{} {{".format( keyword_j )
													)
											] )
										] )
									] )
								)
							)
				except AssertionError, e:
					all_assertion_errors.append( e )

		for e in all_assertion_errors:
			print( e )
		self.assertEqual( [], all_assertion_errors )

