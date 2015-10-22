'''
Series of tests to ensure that new code added to the xml validator and the associated xml to html transforms actually works as expected. This will also begin to put in place the test suite for the validator and associated transforms.
'''
import unittest


# Start with importing the necessary bits - what do I need to import? I think I need to bring in the entire utils.py bit and maybe the cnxml to html bit because these are what I wish to test. I may also need some stuff from the monassis.buildout repo such as the core.py file in transforms
from XmlValidator.utils import format_number
from XmlValidator import entities

# test that the format_number function in utils actually works as expected. There are several cases to consider here so perhaps we write a class for the 1000's separator as a whole and then define functions for each aspect to test?
# test cases: numbers between 0 and 1000, numbers between 10000 and infinity, numbers between -1000 and 0, numbers between -1000 and -infinity. Also include decimals and scientific notation?
class FormatNumberTest(unittest.TestCase):
    def test_thousand_separator(self):
        assert format_number('1000') == u'1\xa0000'  # xa0 is unicode for no breaking space
        assert format_number('14739') == u'14\xa0739'
        assert format_number('999') == u'999'
        assert format_number('+5') == u'+5'  # might need to be in a new function?

    def test_thousand_separator_with_parameter(self):
        assert format_number('1000', thousandsSeparator='|') == u'1|000'

    def test_scientific_notation_with_parameter(self):
        assert format_number('1e10', iScientificNotation=u'%s\u00a0\u00d7\u00a010<sup>%s</sup>') == u'1\u00a0\u00d7\u00a010<sup>10</sup>' # u00a0 is unicode for no breaking space, u00d7 is unicode for times, the last bit of this string before the sup is actually \u00a0 followed by 10. Final output of this is assert 1 * 10^10 but with the appropriate unicode and html in it as well
        assert format_number('1e10', iScientificNotation=u'%se%s') == u'1e10'
        assert format_number('1e-10', iScientificNotation=u'%s\u00a0\u00d7\u00a010<sup>%s</sup>') == u'1\u00a0\u00d7\u00a010<sup>\u221210</sup>'

    def test_minus_symbol_with_parameter(self):
        assert format_number('-5', minusSymbol=entities.unicode['minus']) == u'\u22125'  # minus symbol is \u2212
        assert format_number('-5', minusSymbol='-') == u'-5'

    def test_thousandths_separator_with_parameter(self):
        assert format_number('0.03872432', thousandthsSeparator='') == '0,03872432'
        assert format_number(u'0.039478987192', thousandthsSeparator=u' ') == '0,039 478 987 192'

    def test_decimal_separator_with_parameter(self):
        assert format_number('0.0547', decimalSeparator=',') == '0,0547'
        assert format_number('0.0547', decimalSeparator='.') == '0.0547'

# for the number tag we need to test that only numbers are accepted and not letters. But decimals must be accepted. This tag also needs additional functionality to allow | and perhaps () or [] for rounding and indicating repeating numbers. Also this tag allows notation such as 1e10 to indicate scientific notation. Latex and python might also be allowed here. However there are some checks already run by the validator on what gets passed into the number tag so perhaps we do not need these tests?

# currency tag: should accept the same input as number tag but with an additional currency symbol. $ symbol needs to be allowed in the symbol part if it is not already allowed. I'm not sure if we can test the spacing modifier here but maybe something can be done.

# chemistry tags: must be extended to include all alphanumeric chars in all subtags, as well as accepting decimal numbers.

# there might be some tests around unit numbers needed, e.g. only numbers in the number part, only letters in the unit part, the separator that gets added in must be correct

