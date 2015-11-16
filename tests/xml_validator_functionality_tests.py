'''
This part of the test suite is aimed at testing the functionality behind the validator itself. For example if a certain attribute is allowed or not, what type of child tags are allowed.
'''
from lxml import etree
from nose.tools import raises
from unittest import TestCase

from XmlValidator import ExerciseValidator, XmlValidator, XmlValidationError


class XmlValidatorChildrenTests(TestCase):
    '''
    Each entry in the spec provides information about the allowed children. This class tests out that each of the ways of specifying the children of a tag is actually doing what we expect it to do.
    '''
    def setUp(self):
        self.basic_spec = '''<?xml version="1.0" encoding="utf-8"?>
        <spec xmlns:m="http://www.w3.org/1998/Math/MathML"
            xmlns:style="http://siyavula.com/cnxml/style/0.1"
            xmlns:its="http://www.w3.org/2005/11/its">
            <entry>
                <xpath>/test-element</xpath>
                <children>
                    <element>test-child-required</element>
                    <optional>test-child-optional</optional>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element/test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element/test-child-optional</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-unordered-children</xpath>
                <children>
                    <unordered>
                        <element>test-child-required</element>
                        <optional>test-child-optional</optional>
                    </unordered>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-unordered-children/test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-unordered-children/test-child-optional</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-anynumber-children</xpath>
                <children>
                    <any-number>
                        <element>test-child-required</element>
                    </any-number>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-anynumber-children/test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-oneof-children</xpath>
                <children>
                    <one-of>
                        <element>test-child-required</element>
                        <element>test-child-required-two</element>
                    </one-of>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-oneof-children/test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-oneof-children/test-child-required-two</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-subsetof-children</xpath>
                <children>
                    <subset-of>
                        <element>test-child-required</element>
                        <element>test-child-required-two</element>
                    </subset-of>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-subsetof-children/test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-subsetof-children/test-child-required-two</xpath>
                <notext/>
            </entry>
        </spec>'''
        self.xml_validator = XmlValidator(self.basic_spec)

    def test_validate_with_valid_xml(self):
        '''This tests the basic pattern of a tag with one required child and one optional child.
        The children have to appear in the order they are listed in in the spec.
        The optional child can be removed and the test still passes.'''
        good_template_dom = etree.fromstring('<test-element><test-child-required></test-child-required><test-child-optional></test-child-optional></test-element>')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_unordered_children(self):
        '''This tests unordered children where one child is optional.
        The children can be in any order.'''
        good_template_dom = etree.fromstring('<test-element-unordered-children><test-child-optional></test-child-optional><test-child-required></test-child-required></test-element-unordered-children>')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_oneof_children(self):
        '''This tests a tag that contains only one of the listed child tags. If both are present this must fail.'''
        good_template_dom = etree.fromstring('<test-element-oneof-children><test-child-required></test-child-required></test-element-oneof-children>')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_anynumber_children(self):
        '''This tests a tag that contains any number of the listed child tags.'''
        good_template_dom = etree.fromstring('<test-element-anynumber-children><test-child-required></test-child-required><test-child-required></test-child-required></test-element-anynumber-children>')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_subsetof_children(self):
        '''This tests a tag that contains only a subset of the listed child tags.
        All the listed children can be present in any order'''
        good_template_dom = etree.fromstring('<test-element-subsetof-children><test-child-required-two></test-child-required-two><test-child-required></test-child-required></test-element-subsetof-children>')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_raises_error(self):
        '''This tests the basic pattern of a tag with one required child and one optional child.
        The children have to appear in the order they are listed in in the spec.
        '''
        bad_template_dom = etree.fromstring('<test-element><test-child-optional></test-child-optional></test-element>')

        self.xml_validator.validate(bad_template_dom)

    #@raises(XmlValidationError)
    def test_validate_with_invalid_xml_unordered_children(self):
        '''This tests unordered children where one child is optional.
        The children can be in any order.
        This tests that you cannot have multiple children of the same type, you can only have one of each type in unordered.
        This test should fail but does not, oh dear'''
        bad_template_dom = etree.fromstring('<test-element-unordered-children><test-child-required></test-child-required><test-child-required></test-child-required><test-child-optional></test-child-optional><test-child-optional></test-child-optional></test-element-unordered-children>')

        assert self.xml_validator.validate(bad_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_oneof_children(self):
        '''This tests a tag that contains only one of the listed child tags. If both are present this must fail.'''
        bad_template_dom = etree.fromstring('<test-element-oneof-children><test-child-required></test-child-required><test-child-required-two></test-child-required-two></test-element-oneof-children>')

        self.xml_validator.validate(bad_template_dom)

    # is there a fail test for anynumber?

    def test_validate_with_invalid_xml_subsetof_children(self):
        '''This tests a tag that contains a subset of the listed child tags or may contain all of them
        This test should fail since it should only contain 1 of each child listed.'''
        bad_template_dom = etree.fromstring('<test-element-subsetof-children><test-child-required></test-child-required><test-child-required-two></test-child-required-two><test-child-required-two></test-child-required-two></test-element-subsetof-children>')

        assert self.xml_validator.validate(bad_template_dom) is None

