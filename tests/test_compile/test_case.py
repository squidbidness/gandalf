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
