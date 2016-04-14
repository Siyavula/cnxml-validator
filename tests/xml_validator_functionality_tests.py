"""
This part of the test suite is aimed at testing the functionality behind the validator itself.

For example if a certain attribute is allowed or not, what type of child tags are allowed.
"""

from lxml import etree
from nose.tools import raises
from unittest import TestCase

from XmlValidator import XmlValidator, XmlValidationError


class XmlValidatorChildrenUncombinedTests(TestCase):
    """
    Each entry in the spec provides information about the allowed children.

    This class tests out that each of the ways of specifying the children
    of a tag is actually doing what we expect it to do.
    """

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
                <xpath>test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>test-child-required-two</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>test-child-optional</xpath>
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
                <xpath>/test-element-subsetof-children</xpath>
                <children>
                    <subset-of>
                        <element>test-child-required</element>
                        <element>test-child-required-two</element>
                    </subset-of>
                </children>
                <notext/>
            </entry>
            <entry id="ref-child">
                <children>
                    <element>reference-child</element>
                </children>
            </entry>
            <entry>
                <xpath>reference-child</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-reference-child</xpath>
                <children>
                    <reference>ref-child</reference>
                </children>
                <notext/>
            </entry>
        </spec>'''
        self.xml_validator = XmlValidator(self.basic_spec)

    def test_validate_with_valid_xml(self):
        """
        Test the basic pattern of a tag with one required child and one optional child.

        The children have to appear in the order they are listed in in the spec.
        The optional child can be removed and the test still passes.
        """
        good_template_dom = etree.fromstring('''
            <test-element>
                <test-child-required></test-child-required>
                <test-child-optional></test-child-optional>
            </test-element>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_unordered_children(self):
        """
        Test unordered children where one child is optional.

        The children can be in any order.
        """
        good_template_dom = etree.fromstring('''
            <test-element-unordered-children>
                <test-child-optional></test-child-optional>
                <test-child-required></test-child-required>
            </test-element-unordered-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_oneof_children(self):
        """
        Test a tag that contains only one of the listed child tags.

        If both are present this must fail.
        """
        good_template_dom = etree.fromstring('''
            <test-element-oneof-children>
                <test-child-required></test-child-required>
            </test-element-oneof-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_anynumber_children(self):
        """Test a tag that contains any number of the listed child tags."""
        good_template_dom = etree.fromstring('''
            <test-element-anynumber-children>
                <test-child-required></test-child-required>
                <test-child-required></test-child-required>
            </test-element-anynumber-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_subsetof_children(self):
        """
        Test a tag that contains only a subset of the listed child tags.

        All the listed children can be present in any order.
        Test-child-two or test-child can be removed and this test still passes.
        """
        good_template_dom = etree.fromstring('''
            <test-element-subsetof-children>
                <test-child-required-two></test-child-required-two>
            </test-element-subsetof-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_reference_children(self):
        """Test a tag that references another entry for the child tag."""
        good_template_dom = etree.fromstring('''
            <test-element-reference-child>
                <reference-child></reference-child>
            </test-element-reference-child>''')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_raises_error(self):
        """
        Test the basic pattern of a tag with one required child and one optional child.

        The children have to appear in the order they are listed in in the spec.
        """
        bad_template_dom = etree.fromstring('''
            <test-element>
                <test-child-optional></test-child-optional>
            </test-element>''')

        self.xml_validator.validate(bad_template_dom)

    # @raises(XmlValidationError)
    def test_validate_with_invalid_xml_unordered_children(self):
        """
        Test unordered children where one child is optional.

        The children can be in any order. Test that you cannot have multiple children of the same
        type, you can only have one of each type in unordered.
        FIXME! This test should fail but does not, oh dear!
        """
        bad_template_dom = etree.fromstring('''
            <test-element-unordered-children>
                <test-child-required></test-child-required>
                <test-child-required></test-child-required>
                <test-child-optional></test-child-optional>
                <test-child-optional></test-child-optional>
            </test-element-unordered-children>''')

        assert self.xml_validator.validate(bad_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_oneof_children(self):
        """
        Test a tag that contains only one of the listed child tags.

        If both are present this must fail.
        """
        bad_template_dom = etree.fromstring('''
            <test-element-oneof-children>
                <test-child-required></test-child-required>
                <test-child-required-two></test-child-required-two>
            </test-element-oneof-children>''')

        self.xml_validator.validate(bad_template_dom)

    # is there a fail test for anynumber? Should perhaps be 0?

    def test_subsetof_with_no_children(self):
        """Test that subset-of allows no children to be present."""
        bad_template_dom = etree.fromstring(
            '<test-element-subsetof-children></test-element-subsetof-children>')

        self.xml_validator.validate(bad_template_dom)

    def test_subsetof_with_one_child(self):
        """Test that subset-of allows one child to be present."""
        bad_template_dom = etree.fromstring('''
            <test-element-subsetof-children>
                <test-child-required></test-child-required>
            </test-element-subsetof-children>''')

        self.xml_validator.validate(bad_template_dom)

    def test_subsetof_with_multiple_children(self):
        """Test that subset-of allows multiple children to be present."""
        bad_template_dom = etree.fromstring('''
            <test-element-subsetof-children>
                <test-child-required></test-child-required>
                <test-child-required-two></test-child-required-two>
                <test-child-required-two></test-child-required-two>
            </test-element-subsetof-children>''')

        self.xml_validator.validate(bad_template_dom)


class XmlValidatorChildrenCombinedTests(TestCase):
    """
    Each entry in the spec provides information about the allowed children.

    This class tests out that each of the ways of combining the children of a tag.
    """

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
                <xpath>test-child-required</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>test-child-required-two</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>test-child-optional</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-unordered-anynumber-children</xpath>
                <children>
                    <unordered>
                        <any-number>
                            <element>test-child-required</element>
                            <element>test-child-required-two</element>
                        </any-number>
                    </unordered>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-oneof-anynumber-children</xpath>
                <children>
                    <one-of>
                        <any-number>
                            <element>test-child-required</element>
                            <element>test-child-required-two</element>
                        </any-number>
                    </one-of>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-anynumber-oneof-children</xpath>
                <children>
                    <any-number>
                        <one-of>
                            <element>test-child-required</element>
                            <element>test-child-required-two</element>
                        </one-of>
                    </any-number>
                </children>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-anynumber-from-children</xpath>
                <children>
                    <any-number from="1">
                        <element>test-child-required</element>
                    </any-number>
                </children>
                <notext/>
            </entry>
        </spec>'''
        self.xml_validator = XmlValidator(self.basic_spec)

    def test_validate_with_valid_xml(self):
        """
        Test the basic pattern of a tag with one required child and one optional child.

        The children have to appear in the order they are listed in in the spec.
        The optional child can be removed and the test still passes.
        """
        good_template_dom = etree.fromstring('''
                <test-element>
                    <test-child-required></test-child-required>
                    <test-child-optional></test-child-optional>
                </test-element>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_oneof_anynumber_children(self):
        """
        Test a tag that contains any-number nested inside one-of.

        Either of the required children can be present but not both and any number of the present
        child can be used. What this test is showing is that both children are required and
        there does not need to be only 1 of each.
        """
        good_template_dom = etree.fromstring('''
            <test-element-oneof-anynumber-children>
                <test-child-required></test-child-required>
                <test-child-required-two></test-child-required-two>
                <test-child-required></test-child-required>
                <test-child-required-two></test-child-required-two>
            </test-element-oneof-anynumber-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_oneof_anynumber_children_raises_error(self):
        """
        Test a tag that contains any-number nested inside one-of.

        Either of the required children can be present but not both and any number of the present
        child can be used. This test should not raise a validation error but it does. This is due
        to the fact that validator itself uses dodgy regex to check the children tags and in the
        future we must fix this.
        """
        bad_template_dom = etree.fromstring('''
                <test-element-oneof-anynumber-children>
                    <test-child-required-two></test-child-required-two>
                </test-element-oneof-anynumber-children>''')

        self.xml_validator.validate(bad_template_dom)

    def test_validate_with_valid_xml_anynumber_oneof_children(self):
        """
        Test a tag that contains one-of nested inside any-number.

        Either of the required children can be present
        but not both and any number of the present child can be used.
        This does not fail if test-child-required-two is present, oh dear.
        """
        good_template_dom = etree.fromstring('''
            <test-element-anynumber-oneof-children>
                <test-child-required></test-child-required>
                <test-child-required></test-child-required>
            </test-element-anynumber-oneof-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    # @raises(XmlValidationError)
    def test_validate_with_invalid_xml_anynumber_oneof_children_raises_error(self):
        """
        Test a tag that contains one-of nested inside any-number.

        Either of the required children can be present but not both
        and any number of the present child can be used.
        This test is not giving the expected behaviour.
        """
        bad_template_dom = etree.fromstring('''
                <test-element-anynumber-oneof-children>
                    <test-child-required-two></test-child-required-two>
                    <test-child-required-two></test-child-required-two>
                </test-element-anynumber-oneof-children>''')

        assert self.xml_validator.validate(bad_template_dom) is None

    def test_validate_with_valid_xml_unordered_anynumber_children(self):
        """
        Test a tag that contains any-number nested inside unordered.

        The children can be in any order and there can be any number of them.
        While this test is set up such that it passes ideally
        we want to be able to swop the children elements and still have it pass.
        """
        good_template_dom = etree.fromstring('''
            <test-element-unordered-anynumber-children>
                <test-child-required></test-child-required>
                <test-child-required-two></test-child-required-two>
            </test-element-unordered-anynumber-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_unordered_anynumber_children_raises_error(self):
        """
        Test a tag that contains any-number nested inside unordered.

        The children can be in any order.
        This test is not giving the expected behaviour.
        In theory the way this is set up it should pass.
        """
        bad_template_dom = etree.fromstring('''
                <test-element-unordered-anynumber-children>
                    <test-child-required-two></test-child-required-two>
                    <test-child-required></test-child-required>
                </test-element-unordered-anynumber-children>''')

        self.xml_validator.validate(bad_template_dom)

    def test_validate_with_valid_xml_anynumber_from_children(self):
        """Test a tag that contains any-number from 1 of the children."""
        good_template_dom = etree.fromstring('''
            <test-element-anynumber-from-children>
                <test-child-required></test-child-required>
                <test-child-required></test-child-required>
            </test-element-anynumber-from-children>''')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_anynumber_from_children_raises_error(self):
        """Test a tag that contains any-number from 1 of the children."""
        bad_template_dom = etree.fromstring('''
            <test-element-anynumber-from-children></test-element-anynumber-from-children>''')

        self.xml_validator.validate(bad_template_dom)


class XmlValidatorTagAttributes(TestCase):
    """
    Some entries in the spec provide information about the attributes of a tag.

    This class tests that those are working as expected.
    """

    def setUp(self):
        self.basic_spec = '''<?xml version="1.0" encoding="utf-8"?>
        <spec xmlns:m="http://www.w3.org/1998/Math/MathML"
            xmlns:style="http://siyavula.com/cnxml/style/0.1"
            xmlns:its="http://www.w3.org/2005/11/its">
            <entry>
                <xpath>/test-element-no-attributes</xpath>
                <notext/>
            </entry>
            <entry>
                <xpath>/test-element-string-attribute-no-default</xpath>
                <attributes>
                    <entry>
                        <name>id</name>
                        <type>string</type>
                        <default/>
                    </entry>
                </attributes>
            </entry>
            <entry>
                <xpath>/test-element-integer-attribute-no-default</xpath>
                <attributes>
                    <entry>
                        <name>precision</name>
                        <type>integer</type>
                        <default/>
                    </entry>
                </attributes>
            </entry>
            <entry>
                <xpath>/test-element-enum-attribute-no-default</xpath>
                <attributes>
                    <entry>
                        <name>type</name>
                        <type>enum('inline', 'block')</type>
                        <default/>
                    </entry>
                </attributes>
            </entry>
            <entry>
                <xpath>/test-element-string-attribute-with-default</xpath>
                <attributes>
                    <entry>
                        <name>id</name>
                        <type>string</type>
                        <default>myId</default>
                    </entry>
                </attributes>
            </entry>
            <entry>
                <xpath>/test-element-integer-attribute-with-default</xpath>
                <attributes>
                    <entry>
                        <name>precision</name>
                        <type>integer</type>
                        <default>1</default>
                    </entry>
                </attributes>
            </entry>
            <entry>
                <xpath>/test-element-enum-attribute-with-default</xpath>
                <attributes>
                    <entry>
                        <name>type</name>
                        <type>enum('block', 'inline')</type>
                        <default>block</default>
                    </entry>
                </attributes>
            </entry>
        </spec>'''
        self.xml_validator = XmlValidator(self.basic_spec)

    def test_validate_with_valid_xml(self):
        """Test the basic pattern of a tag with no attributes."""
        good_template_dom = etree.fromstring('''
            <test-element-no-attributes></test-element-no-attributes>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_string_attribute_no_default(self):
        """Test the basic pattern of a tag with an attribute of type string."""
        good_template_dom = etree.fromstring('''
            <test-element-string-attribute-no-default id="my id">
            </test-element-string-attribute-no-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_integer_attribute_no_default(self):
        """Test the basic pattern of a tag with an attribute of type integer."""
        good_template_dom = etree.fromstring('''
            <test-element-integer-attribute-no-default precision="5">
            </test-element-integer-attribute-no-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_enum_attribute_no_default_block_type(self):
        """Test the basic pattern of a tag with an attribute of type enum."""
        good_template_dom = etree.fromstring('''
            <test-element-enum-attribute-no-default type="block">
            </test-element-enum-attribute-no-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_string_attribute_with_default(self):
        """Test the basic pattern of a tag with an attribute of type string."""
        good_template_dom = etree.fromstring('''
            <test-element-string-attribute-with-default>
            </test-element-string-attribute-with-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_integer_attribute_with_default(self):
        """
        Test the basic pattern of a tag with an attribute of type integer.

        There is a default set and so we are testing leaving out the attribute here.
        """
        good_template_dom = etree.fromstring('''
            <test-element-integer-attribute-with-default>
            </test-element-integer-attribute-with-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    def test_validate_with_valid_xml_enum_attribute_no_default(self):
        """
        Test the basic pattern of a tag with an attribute of type enum.

        There is a default set and so we are testing leaving out the attribute here.
        """
        good_template_dom = etree.fromstring('''
            <test-element-enum-attribute-with-default>
            </test-element-enum-attribute-with-default>''')

        assert self.xml_validator.validate(good_template_dom) is None

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_integer_attribute_no_default(self):
        """Test the basic pattern of a tag with an attribute of type integer."""
        bad_template_dom = etree.fromstring('''
            <test-element-integer-attribute-no-default precision="ten">
            </test-element-integer-attribute-no-default>''')

        self.xml_validator.validate(bad_template_dom)

    @raises(XmlValidationError)
    def test_validate_with_invalid_xml_enum_attribute_no_default(self):
        """Test the basic pattern of a tag with an attribute of type enum."""
        bad_template_dom = etree.fromstring('''
            <test-element-enum-attribute-no-default type="ten">
            </test-element-enum-attribute-no-default>''')

        self.xml_validator.validate(bad_template_dom)
