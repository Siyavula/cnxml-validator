'''
Series of tests to ensure that new code added to the xml validator and the associated xml to html transforms actually works as expected. This will also begin to put in place the test suite for the validator and associated transforms.
'''
import unittest


# Start with importing the necessary bits - what do I need to import? I think I need to bring in the entire utils.py bit and maybe the cnxml to html bit because these are what I wish to test. I may also need some stuff from the monassis.buildout repo such as the core.py file in transforms
from XmlValidator.utils import format_number


class FormatNumberTest(unittest.TestCase):
    def test_thousand_separator(self):
        assert format_number('1000') == u'1\xa0000'
        assert format_number('14739') == u'14\xa0739'
        assert format_number('999') == u'999'

    def test_thousand_separator_with_parameter(self):
        assert format_number('1000', thousandsSeparator='|') == u'1|000'

# test that the 1000's separator works. There are several cases to consider here so perhaps we write a class for the 1000's separator as a whole and then define functions for each aspect to test?
# test cases: numbers between 0 and 1000, numbers between 10000 and infinity, numbers between -1000 and 0, numbers between -1000 and -infinity. Also include decimals and scientific notation?
def thousand_separator(number):
    '''checks to see if space or \ is in the number if the number is greater than 999 or less than -999'''
    if '0' <= number <= '999':
        assert number.find(' ') == -1
        assert number.find('\\') == -1
    elif number > '999':
        assert number.find(' ') != -1
        assert number.find('\\') != -1
    elif '999' < number < '0':
        assert number.find(' ') != -1
        assert number.find('\\') != -1
    else:
        assert number.find(' ') == -1
        assert number.find('\\') == -1

# for the number tag we need to test that only numbers are accepted and not letters. But decimals must be accepted. This tag also needs additional functionality to allow | and perhaps () or [] for rounding and indicating repeating numbers. Also this tag allows notation such as 1e10 to indicate scientific notation. Latex and python might also be allowed here. However there are some checks already run by the validator on what gets passed into the number tag so perhaps we do not need these tests?

# currency tag: should accept the same input as number tag but with an additional currency symbol. $ symbol needs to be allowed in the symbol part if it is not already allowed. I'm not sure if we can test the spacing modifier here but maybe something can be done.

# chemistry tags: must be extended to include all alphanumeric chars in all subtags, as well as accepting decimal numbers.

# there might be some tests around unit numbers needed, e.g. only numbers in the number part, only letters in the unit part, the separator that gets added in must be correct

