"""
Test specific xml tags to ensure they are performing as expected.

This also tests that the validator does in fact load a spec and validate against that spec.
"""
import sys

from lxml import etree
from StringIO import StringIO
from unittest import TestCase

from XmlValidator import ExerciseValidator, XmlValidator


class XmlValidatorTests(TestCase):
    """
    The XmlValidator takes a spec and validates a given XML string against it.

    Test that the XmlValidator correctly loads a spec and uses it.
    """

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

        self.assertIsNone(self.xml_validator.validate(good_template_dom))

    def test_validate_with_unhandled_element_still_passes(self):
        bad_template_dom = etree.fromstring('<bad-element></bad-element>')

        sys.stderr = StringIO()

        self.assertIsNone(self.xml_validator.validate(bad_template_dom))
        self.assertIn('Unhandled element at /bad-element', self.xml_validator.warnings)

    def test_validate_with_broken_rule_raises_error(self):
        bad_template_dom = etree.fromstring("<test-element>This text can't be here</test-element>")

        self.xml_validator.validate(bad_template_dom)
        self.assertEqual(
            self.xml_validator.errors,
            ["/test-element element must not have any text.\n"
             "*** Found the following text at the beginning of the element: "
             "This text can't be here\n"
             "*** The offending element looks like this: "
             "<test-element>This text can't be here</test-element>"])


class ExerciseValidatorTests(TestCase):
    """
    Test that the ExerciseValidator class correctly validates a given XML structure.

    This assume a specific exercise layout specification.
    """

    def setUp(self):
        self.exercise_validator = ExerciseValidator()
        self.maxDiff = None

    def test_validate_with_valid_xml(self):
        """
        Test the minimum needed elements for a template.

        Response is actually optional since that is not needed for entries in books.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem></problem>
                <response></response>
                <solution></solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_invalid_xml(self):
        invalid_template_dom = etree.fromstring('<template></template>')

        self.exercise_validator.validate(invalid_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Child match failed for a /template element.\n'
             '*** I was expecting the children to follow this pattern:\n'
             '((title,)((multi-part,)|(entry,)))\n'
             '*** Instead I got these children:\n\n'
             '*** The offending element looks like this:\n'
             '<template></template>\n'])

    def test_validate_with_meta_tag(self):
        invalid_template_dom = etree.fromstring('''
        <template>
            <meta></meta>
            <entry>
                <problem></problem>
                <solution></solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(invalid_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Child match failed for a /template element.\n*** '
             'I was expecting the children to follow this pattern:\n'
             '((title,)((multi-part,)|(entry,)))\n'
             '*** Instead I got these children:\nmeta,entry,\n*** '
             'The offending element looks like this:\n<template>\n            '
             '<meta></meta>\n            <entry>\n'
             '                <problem></problem>\n                '
             '<solution></solution>\n            </entry>\n        </template>\n'])

    def test_validate_missing_title(self):
        invalid_template_dom = etree.fromstring('''
        <template>
            <entry>
                <problem></problem>
                <solution></solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(invalid_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Child match failed for a /template element.\n*** '
             'I was expecting the children to follow this pattern:\n'
             '((title,)((multi-part,)|(entry,)))\n'
             '*** Instead I got these children:\nentry,\n'
             '*** The offending element looks like this:\n'
             '<template>\n            <entry>\n                <problem></problem>'
             '\n                <solution></solution>\n            </entry>\n        '
             '</template>\n'])

    def test_validate_missing_entry(self):
        invalid_template_dom = etree.fromstring('''
        <template>
            <title></title>
        </template>''')

        self.exercise_validator.validate(invalid_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Child match failed for a /template element.\n*** '
             'I was expecting the children to follow this pattern:\n'
             '((title,)((multi-part,)|(entry,)))\n'
             '*** Instead I got these children:\ntitle,\n*** '
             'The offending element looks like this:\n<template>\n            '
             '<title></title>\n        </template>\n'])

    def test_validate_title_tag_with_other_elements(self):
        """
        Test validation with a title tag containing other elements.

        Allowed tags are: br, space, newline, chem_compound, correct, currency
        emphasis, latex, link, nth, nuclear_notation, number, percentage
        spec_note, sub, sup, unit_number, unit, input, style, check
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title><latex>x</latex> makes <sup>the</sup> title. '
            '<unit>Units</unit> are needed.</title>
            <entry>
                <problem></problem>
                <response></response>
                <solution></solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_note_tag(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="note"></note>
                </problem>
                <solution>
                    <note type="note"></note>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_note_tag_with_variety_of_typical_subtags(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="note">
                        In-line Elements
                        <number>5</number>
                        <sup>2</sup>
                    </note>
                </problem>
                <solution>
                    <note type="note">
                        Para Elements
                        <list><item>1</item><item>2</item><item>3</item></list>
                        <latex></latex>
                    </note>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_note_tag_with_text(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="note">Note Content</note>
                </problem>
                <solution>
                    <note type="tip">Note Content</note>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_note_tag_with_para(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="note"><para>Note Content</para></note>
                </problem>
                <solution>
                    <note type="tip"><para>Note Content</para></note>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_note_tag_with_no_attribute(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note>
                    </note>
                </problem>
                <solution>
                    <note>
                    </note>
                </solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(good_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ["Missing attribute 'type' in /template/entry/problem/note",
             "Missing attribute 'type' in /template/entry/solution/note"])

    def test_validate_with_note_tag_with_incorrect_attribute(self):
        bad_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="bob">
                    </note>
                </problem>
                <solution>
                    <note type="bob">
                    </note>
                </solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(bad_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Attribute value \'bob\' does not conform to type \'enum'
             '("note","tip","inlinetip","instruction","instructions","examnote")\' in '
             '/template/entry/problem/note',
             'Attribute value \'bob\' does not conform to type \'enum'
             '("note","tip","inlinetip","instruction","instructions","examnote")\' in '
             '/template/entry/solution/note'])

    def test_validate_with_note_tag_with_book_note_attribute(self):
        bad_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <note type="warning">
                    </note>
                </problem>
                <solution>
                    <note type="warning">
                    </note>
                </solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(bad_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Attribute value \'warning\' does not conform to type \'enum'
             '("note","tip","inlinetip","instruction","instructions","examnote")\' in '
             '/template/entry/problem/note',
             'Attribute value \'warning\' does not conform to type \'enum'
             '("note","tip","inlinetip","instruction","instructions","examnote")\' in '
             '/template/entry/solution/note'])

    def test_validate_with_nuclear_notation_tag_no_atomic_number(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <nuclear_notation><symbol>He</symbol><mass_number>5</mass_number></nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_nuclear_notation_tag_no_mass_number(self):
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <nuclear_notation>
                        <symbol>He</symbol>
                        <atomic_number>5</atomic_number>
                    </nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_nuclear_notation_tag_no_symbol(self):
        """
        Raise an error since the symbol tag should be required.

        The problem lies in the unordered modifier since the spec for that is a hack and matches
        incorrect patterns. This needs to be corrected.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <nuclear_notation>
                        <atomic_number>He</atomic_number>
                        <mass_number>5</mass_number>
                    </nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_nuclear_notation_tag_no_children(self):
        """
        Raise an error since nuclear_notation is required to contain at least the symbol tag.

        The problem lies in the unordered modifier since the spec for that is a hack and matches
        incorrect patterns. This needs to be corrected.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <nuclear_notation></nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_currency_tag_no_children_no_text(self):
        """Test the currency tag with no children and no text."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <currency></currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_currency_tag_no_children_text(self):
        """Test the currency tag with no children and text."""
        bad_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <currency>R 5</currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(bad_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['//currency element must not have any text.\n*** Found the following text at the '
             'beginning of the element: R 5\n*** The offending element looks like this: '
             '<currency>R 5</currency>\n                '])

    def test_validate_currency_tag_with_only_symbol_child(self):
        """Test the currency tag with only symbol child."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <currency>
                        <symbol>R</symbol>
                    </currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_currency_tag_with_only_number_child(self):
        """Test the currency tag with only number child."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <currency>
                        <number>5</number>
                    </currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_currency_tag_with_both_children(self):
        """Test the currency tag with both children."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <currency>
                        <number>5</number><symbol>R</symbol>
                    </currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_pspicture_tag_no_children(self):
        """
        Test validation of pspicture with no child tags.

        This should raise an error since pspicture is required to contain at
        least either src or code child.
        The problem lies in the unordered modifier since the spec
        for that is a hack and matches incorrect patterns.
        This needs to be corrected.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <pspicture></pspicture>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_tikzpicture_tag_no_children(self):
        """
        Raise an error since tikzpicture is required to contain at least either src or code child.

        The problem lies in the unordered modifier since the spec for that is a hack and matches
        incorrect patterns. This needs to be corrected.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <tikzpicture></tikzpicture>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_style_tag(self):
        """Test that the style tag works and allows the font-color attribute."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <para><style font-color="blue">blue text</style></para>
                    <para><style font-color="blue"><number>5</number></style></para>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    # @raises(XmlValidationError)
    def test_validate_with_number_tag(self):
        """
        Test that the number tag works and checks the type of number.

        This really should fail, oh dear another bad instance.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <para><number>5x/5</number></para>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_quote_tag_block_children(self):
        """Test that the quote tag works with block children."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <quote><para>Some text</para></quote>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_quote_tag_inline_children_no_para(self):
        """Test that the quote tag works with inline children and no para tag."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <quote>Some <emphasis>emphasised</emphasis> text not in a paragraph</quote>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_table_tag_notes_and_latex(self):
        """Test that the table tag works with multiple inline tags."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <html5table>
                        <tbody>
                            <tr>
                                <td><note type="inlinetip">inline tip</note> and
                                <latex>x</latex></td>
                            </tr>
                        </tbody>
                    </html5table>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_table_tag_notes_and_quotes(self):
        """Test that the table tag works with multiple block tags."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <html5table>
                        <tbody>
                            <tr>
                                <td><note type="tip">tip</note> and
                                <quote>quote</quote></td>
                            </tr>
                        </tbody>
                    </html5table>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_table_tag_notes_and_emphasis(self):
        """Test that the table tag works with inline and block tags."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <html5table>
                        <tbody>
                            <tr>
                                <td><note type="inlinetip">inline tip</note> and
                                <emphasis>emphas</emphasis></td>
                            </tr>
                        </tbody>
                    </html5table>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_list_tag_notes_and_emphasis(self):
        """Test that the list tag works with inline and block tags."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <list>
                        <item><unit_number><number>5</number><unit>h</unit></unit_number> and
                        <note type="inlinetip">emphas</note></item>
                    </list>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_check_tag_not_in_latex(self):
        """
        Test that the check tag works with inline and block tags (not latex).

        In this case the check tag is not inside a latex tag.
        """
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <para><check>Some text</check></para>
                    <note type="note">
                        <check/>
                    </note>
                    <list>
                        <item><check> this is correct</check></item>
                    </list>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_with_check_tag_in_latex(self):
        """Test that the check tag works with inline and block latex."""
        good_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <para>
                        <latex>x <check/></latex>
                    </para>
                    <latex display="block">
                        x = 2 <check> for subtraction</check>
                    </latex>
                </problem>
                <solution>
                </solution>
            </entry>
        </template>''')

        self.assertIsNone(self.exercise_validator.validate(good_template_dom))
        self.assertEqual(self.exercise_validator.errors, [])
        self.assertEqual(self.exercise_validator.warnings, [])

    def test_validate_book_tag_is_invalid(self):
        """Test that using a tag specific to books gives an error."""
        bad_template_dom = etree.fromstring('''
        <template>
            <title></title>
            <entry>
                <problem>
                    <presentation>
                        <title>The title</title>
                        <url>google.com</url>
                    </presentation>
                </problem>
                <solution>
                    <presentation>
                        <title>The title</title>
                        <url>google.com</url>
                    </presentation>
                </solution>
            </entry>
        </template>''')

        self.exercise_validator.validate(bad_template_dom)
        self.assertEqual(
            self.exercise_validator.errors,
            ['Child match failed for a //entry/problem element.\n'
             '*** I was expecting the children to follow this pattern:\n'
             '((((((((((para,)|(((list,)|(pspicture,)|(tikzpicture,)|(image,)|(html5table,)|'
             '(figure,)|(equation,)|(latex,)|(correct,)|(note,)|(centre,)))))|(definition,)|'
             '(quote,)|(note,)|(radio,)|(centre,)))){,}))|((((((br,)|(space,)|(newline,)|'
             '(chem_compound,)|(correct,)|(currency,)|(emphasis,)|(latex,)|(link,)|(nth,)|'
             '(nuclear_notation,)|(number,)|(percentage,)|(spec_note,)|(sub,)|(sup,)|'
             '(unit_number,)|(unit,)|(input,)|(style,)|(check,)))){,}))))\n'
             '*** Instead I got these children:\npresentation,\n'
             '*** The offending element looks like this:\n<problem>\n'
             '                    <presentation>\n'
             '                        <title>The title</title>\n'
             '                        <url>google.com</url>\n'
             '                    </presentation>\n'
             '                </problem>\n                \n',
             'Child match failed for a //entry/solution element.\n'
             '*** I was expecting the children to follow this pattern:\n'
             '((((((step,)|(hint,))){,})|((((((((para,)|(((list,)|(pspicture,)|(tikzpicture,)|'
             '(image,)|(html5table,)|(figure,)|(equation,)|(latex,)|(correct,)|(note,)|'
             '(centre,)))))|(definition,)|(quote,)|(note,)|(radio,)|(centre,)))){,}))|((((((br,)|'
             '(space,)|(newline,)|(chem_compound,)|(correct,)|(currency,)|(emphasis,)|(latex,)|'
             '(link,)|(nth,)|(nuclear_notation,)|(number,)|(percentage,)|(spec_note,)|(sub,)|'
             '(sup,)|(unit_number,)|(unit,)|(input,)|(style,)|(check,)))){,}))))\n'
             '*** Instead I got these children:\npresentation,\n'
             '*** The offending element looks like this:\n<solution>\n'
             '                    <presentation>\n'
             '                        <title>The title</title>\n'
             '                        <url>google.com</url>\n'
             '                    </presentation>\n                </solution>\n            \n'])
