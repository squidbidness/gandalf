import parser

class TestCase( object ):

	def __init__( self, assertion, baseline_codes, codes ):
		self.assertion = assertion
		self.baseline_codes = baseline_codes
		self.codes = codes

	def __eq__( self, other ):
		return (
				self.assertion == other.assertion
				and self.baseline_codes == other.baseline_codes
				and self.codes == other.codes
				)


class TestCaseBuilder( object ):

	@classmethod
	def buildAll( cls, ast_root ):
		assertions = cls._descendantAssertions( ast_root )
		return [ cls._buildTestCase( case ) for case in assertions ]

	@classmethod
	def _descendantAssertions( cls, cur_node ):
		assertions = []
		if isinstance( cur_node, parser.AssertionNode ):
			assertions.append( cur_node )
		for child in cur_node.children:
			assertions.extend( cls._descendantAssertions( child ) )
		return assertions

	@classmethod
	def _immediateChildCodes( cls, parent_node ):
			return [ child for child in parent_node.children
						if isinstance( child, parser.CodeNode ) ]


	@classmethod
	def _buildTestCase( cls, assertion_node ):
		assert isinstance( assertion_node, parser.AssertionNode )

		baseline_codes = []
		cur_parent = assertion_node.parent
		while cur_parent:
			baseline_codes.extend(
					cls._immediateChildCodes( cur_parent ) )
			cur_parent = cur_parent.parent

		codes = list( baseline_codes )
		codes.extend( cls._immediateChildCodes( assertion_node ) )

		baseline_codes.sort()
		codes.sort()

		return TestCase( assertion_node, baseline_codes, codes )
