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
							ErrorNode( 3, "\t\t\t\t\t@}" )
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
						CodeNode( 1, end_line=3 ),
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
						CodeNode( 14, end_line=16 ),
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
							CodeNode( 3, end_line=5 ),
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
						ErrorNode( 2, "\t\t\t\t\t@TEST {" )
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
						ErrorNode( 2, "\t\t\t\t\t@}" )
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
							ErrorNode( 4, "\t\t\t\t\t@}" )
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
						ErrorNode( 2, "\t\t\t\t\t@EXPECT {" )
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
						ErrorNode( 2, "\t\t\t\t\t@EXPECT_NOT {" )
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
						ErrorNode( 2, "\t\t\t\t\t@ASSERT {" )
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
						ErrorNode( 2, "\t\t\t\t\t@ASSERT_NOT {" )
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
							ErrorNode( 4, "\t\t\t\t\t\t@TEST inner {" )
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
												"\t\t\t\t\t\t\t\t\t\t@{} {{".
													format( keyword_j )
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

	def test_multiple_consec_code_lines( self ):
		runParserTest(
				self,
				"""code1
					code2
					code3
					code4
					@TEST test1 {
						code6
						code7
						code8
						@EXPECT {
							code10
							code11
						@}
						code13
						@EXPECT {
							code15
						@}
						code17
						code18
						code19
					@}



					""",
				(
					True,
					RootNode( children=[
						CodeNode( 1, end_line=5 ),
						TestNode( 5, "test1", children=[
							CodeNode( 6, end_line=9 ),
							ExpectNode( 9, children=[
								CodeNode( 10, end_line=12 ),
								EndNode( 12 )
								] ),
							CodeNode( 13, end_line=14 ),
							ExpectNode( 14, children=[
								CodeNode( 15, end_line=16 ),
								EndNode( 16 ),
								] ),
							CodeNode( 17, end_line=20 ),
							EndNode( 20 ),
							] ),
						CodeNode( 21, end_line=25 ),
						EofNode( 25 )
						] )
					)
				)


	# TODO: test_unconventional_whitespace_in_test_decl
