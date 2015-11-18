'''
This test suite is specifically for testing functions in the transformation process. For example does a number get formatted as expected?
'''
import unittest
from lxml import etree

# Start with importing the necessary bits - what do I need to import? I think I need to bring in the entire utils.py bit and maybe the cnxml to html bit because these are what I wish to test. I may also need some stuff from the monassis.buildout repo such as the core.py file in transforms
from XmlValidator.utils import format_number
from XmlValidator import entities
from XmlValidator.callbacks import is_numeric_value
from XmlValidator.callbacks import is_number

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

# for the number tag we need to test that only numbers are accepted and not letters. But decimals must be accepted. This tag also needs additional functionality to allow | and perhaps () or [] for rounding and indicating repeating numbers. Also this tag allows notation such as 1e10 to indicate scientific notation. Latex and python might also be allowed here.
class NumberTextTest(unittest.TestCase):
    '''
    This tests that the number tag correctly checks if the text of the tag is a number.
    If the text is a number then it returns true
    If the text is not a number then it raises an error
    This test uses the is_number function from callbacks.py
    is_number calls is_numeric_value from callbacks.py for non scientific notation
    '''
    def test_integer_input(self):
        element = etree.Element('number')
        element.text = '5'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-3'
        assert is_number(element1) == True

    def test_float_input(self):
        element = etree.Element('number')
        element.text = '5.0'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-4.24'
        assert is_number(element1) == True

    def test_truncation_input(self):
        element = etree.Element('number')
        element.text = '3.6432...'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-0.9274...'
        assert is_number(element1) == True

    def test_scientific_notation_input(self):
        element = etree.Element('number')
        element.text = '34e9'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-34e9'
        assert is_number(element1) == True
        element2 = etree.Element('number')
        element2.text = '34e-9'
        assert is_number(element2) == True
        element3 = etree.Element('number')
        coeff = etree.SubElement(element3, 'coeff')
        coeff.text = '3'
        exp = etree.SubElement(element3, 'exp')
        exp.text = '3'
        assert is_number(element3) == True

    def test_number_with_pipe_input(self):
        element = etree.Element('number')
        element.text = '3.6432|3533'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-0.927|3424...'
        assert is_number(element1) == True

    def test_recurring_input(self):
        element = etree.Element('number')
        element.text = '3.643(2)'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '-0.927(4)'
        assert is_number(element1) == True
        element2 = etree.Element('number')
        element2.text = '3.643[2]'
        assert is_number(element2) == True
        element3 = etree.Element('number')
        element3.text = '-0.927[4]'
        assert is_number(element3) == True

    def test_fraction_input(self):
        element = etree.Element('number')
        element.text = '\\frac{3}{2}'
        assert is_number(element) == True
        element1 = etree.Element('number')
        element1.text = '3/2'
        assert is_number(element1) == True

# currency tag: should accept the same input as number tag but with an additional currency symbol. $ symbol needs to be allowed in the symbol part if it is not already allowed. I'm not sure if we can test the spacing modifier here but maybe something can be done.

# chemistry tags: must be extended to include all alphanumeric chars in all subtags, as well as accepting decimal numbers.

# there might be some tests around unit numbers needed, e.g. only numbers in the number part, only letters in the unit part, the separator that gets added in must be correct
