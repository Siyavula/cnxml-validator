from lxml import etree
from nose.tools import raises
from unittest import TestCase

from XmlValidator import ExerciseValidator, XmlValidator, XmlValidationError


class XmlValidatorTests(TestCase):
    '''
    The XmlValidator takes a spec and validates a given XML string against it. Test that the
    XmlValidator correctly loads a spec and uses it.
    '''
    def setUp(self):
        self.basic_spec = '''<?xml version="1.0" encoding="utf-8"?>
        <spec xmlns:m="http://www.w3.org/1998/Math/MathML"
            xmlns:style="http://siyavula.com/cnxml/style/0.1"
            xmlns:its="http://www.w3.org/2005/11/its">
            <entry>
                <xpath>/test-element</xpath>
                <notext/>
            </entry>
        </spec>'''
        self.xml_validator = XmlValidator(self.basic_spec)

    def test_validate_with_valid_xml(self):
        good_template_dom = etree.fromstring('<test-element></test-element>')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_unhandled_element_still_passes(self):
        bad_template_dom = etree.fromstring('<bad-element></bad-element>')

        assert self.xml_validator.validate(bad_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_broken_rule_raises_error(self):
        bad_template_dom = etree.fromstring("<test-element>This text can't be here</test-element>")

        self.xml_validator.validate(bad_template_dom)


class ExerciseValidatorTests(TestCase):
    '''
    This will test that the ExerciseValidator class correctly validates a given XML structure
    (according to a specific exercise layout specification).
    '''
    def setUp(self):
        self.exercise_validator = ExerciseValidator()

    def test_validate_with_valid_xml(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                </problem>
                <response>
                </response>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
        </exercise-container>''')

        self.exercise_validator.validate(good_template_dom)
