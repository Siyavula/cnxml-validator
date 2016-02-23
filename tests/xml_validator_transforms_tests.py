'''
This test suite is specifically for testing functions in the transformation process.
'''

import unittest
from lxml import etree

from XmlValidator.utils import format_number
from XmlValidator import entities
from XmlValidator.callbacks import is_numeric_value
from XmlValidator.callbacks import is_number

class FormatNumberTest(unittest.TestCase):
    '''
    This class tests that numbers are formatted correctly.
    It tests that the function input variables are working as expected.
    It also tests that we are getting the expected output.
    '''
    def test_thousand_separator(self):
        assert format_number('1000') == u'1\xa0000'  
        # xa0 is unicode for no breaking space
        assert format_number('14739') == u'14\xa0739'
        assert format_number('999') == u'999'
        assert format_number('+5') == u'+5'

    def test_thousand_separator_with_parameter(self):
        assert format_number('1000', thousandsSeparator='|') == u'1|000'

    def test_scientific_notation_with_parameter(self):
        assert format_number('1e10', iScientificNotation=u'%s\u00a0\u00d7\u00a010<sup>%s</sup>') == u'1\u00a0\u00d7\u00a010<sup>10</sup>' 
        # u00a0 is unicode for no breaking space, 
        # u00d7 is unicode for times, 
        # the last bit of this string before the sup is actually \u00a0 followed by 10. 
        # Final output of this is assert 1 * 10^10 
        # but with the appropriate unicode and html in it as well
        assert format_number('1e10', iScientificNotation=u'%se%s') == u'1e10'
        assert format_number('1e-10', iScientificNotation=u'%s\u00a0\u00d7\u00a010<sup>%s</sup>') == u'1\u00a0\u00d7\u00a010<sup>\u221210</sup>'

    def test_minus_symbol_with_parameter(self):
        assert format_number('-5', minusSymbol=entities.unicode['minus']) == u'\u22125'
        assert format_number('-5', minusSymbol='-') == u'-5'

    def test_thousandths_separator_with_parameter(self):
        assert format_number('0.03872432', thousandthsSeparator='') == '0,03872432'
        assert format_number(u'0.039478987192', thousandthsSeparator=u' ') == '0,039 478 987 192'

    def test_decimal_separator_with_parameter(self):
        assert format_number('0.0547', decimalSeparator=',') == '0,0547'
        assert format_number('0.0547', decimalSeparator='.') == '0.0547'

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
