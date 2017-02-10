from test_case_builder import *
from parser import *
import unittest


class TestCaseBuilderTest( unittest.TestCase ):

	def test_basic_valid( self ):

		ast = RootNode( children=[
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

		code1 = ast.children[0]
		test3 = ast.children[1]
		code4 = test3.children[0]
		expect5 = test3.children[1]
		code6 = expect5.children[0]
		end7 = expect5.children[1]
		code8 = test3.children[2]
		expect_not9 = test3.children[3]
		code10 = expect_not9.children[0]
		end11 = expect_not9.children[1]
		code12 = test3.children[4]
		end13 = test3.children[5]
		code14 = ast.children[2]
		end16 = ast.children[3]

		expected = [
			TestCase(
				expect5,
				[ code1, code4, code8, code12, code14 ],
				[ code1, code4, code6, code8, code12, code14 ],
				),
			TestCase(
				expect_not9,
				[ code1, code4, code8, code12, code14 ],
				[ code1, code4, code8, code10, code12, code14 ]
				)
			]

		self.assertEqual( expected, TestCaseBuilder.buildAll( ast ) )
