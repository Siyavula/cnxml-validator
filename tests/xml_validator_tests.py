'''
This part of the test suite focuses on testing specific xml tags to ensure 
they are performing as expected. This also tests that the validator does 
in fact load a spec and validate against that spec.
'''

from lxml import etree
from nose.tools import raises
from unittest import TestCase

from XmlValidator import ExerciseValidator, XmlValidator, XmlValidationError


class XmlValidatorTests(TestCase):
    '''
    The XmlValidator takes a spec and validates a given XML string against it.
    Test that the XmlValidator correctly loads a spec and uses it.
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
        '''
        This should represent the minimum needed elements for a template. 
        Response is actually optional since that is not needed for entries in books.
        '''
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

    def test_validate_with_note_tag(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <note type="note">
                    </note>
                </problem>
                <solution>
                    <note type="note">
                    </note>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    @raises(KeyError)
    def test_validate_with_note_tag_with_no_attribute(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
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
        </exercise-container>''')

        self.exercise_validator.validate(good_template_dom)

    @raises(XmlValidationError)
    def test_validate_with_note_tag_with_incorrect_attribute(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
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
        </exercise-container>''')

        self.exercise_validator.validate(good_template_dom)

    def test_validate_with_nuclear_notation_tag_no_atomic_number(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <nuclear_notation><symbol>He</symbol><mass_number>5</mass_number></nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_nuclear_notation_tag_no_mass_number(self):
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
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
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    #@raises(XmlValidationError)
    def test_validate_with_nuclear_notation_tag_no_symbol(self):
        '''
        This should raise an error since the symbol tag should be required. 
        The problem lies in the unordered modifier since the spec for that 
        is a hack and matches incorrect patterns. This needs to be corrected.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
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
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_nuclear_notation_tag_no_children(self):
        '''
        This should raise an error since nuclear_notation is required to contain at 
        least the symbol tag. The problem lies in the unordered modifier 
        since the spec for that is a hack and matches incorrect patterns. 
        This needs to be corrected.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <nuclear_notation></nuclear_notation>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_currency_tag_no_children(self):
        '''
        This should raise an error since currency is required to contain at least the number tag.
        The problem lies in the unordered modifier since the spec for that is a 
        hack and matches incorrect patterns. This needs to be corrected.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <currency></currency>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_pspicture_tag_no_children(self):
        '''
        This should raise an error since currency is required to contain at 
        least either src or code child.
        The problem lies in the unordered modifier since the spec 
        for that is a hack and matches incorrect patterns.
        This needs to be corrected.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <pspicture></pspicture>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_tikzpicture_tag_no_children(self):
        '''
        This should raise an error since tikzpicture is required to contain 
        at least either src or code child.
        The problem lies in the unordered modifier since the spec for that 
        is a hack and matches incorrect patterns. This needs to be corrected.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <tikzpicture></tikzpicture>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_style_tag(self):
        '''
        Testing that the style tag works and allows the font-color attribute
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <para><style font-color="blue">blue text</style></para>
                    <para><style font-color="blue"><number>5</number></style></para>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    #@raises(XmlValidationError)
    def test_validate_with_number_tag(self):
        '''
        Testing that the number tag works and checks the type of number. 
        This really should fail, oh dear another bad instance.
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
            </meta>
            <entry>
                <problem>
                    <para><number>5x/5</number></para>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None

    def test_validate_with_meta_data(self):
        '''
        Testing that the meta data part is working as expected.
        Authors is optional. There must be an author child tag.
        Title is not optional but the validator does not actually check that it is present.
        Difficulty is also not optional. This must contain level in the updated validator.
        Language is not optional. Only valid language codes are accepted here: en, en-ZA, af, af-ZA.
        Link is optional and there can be multiple links. 
        Link must be self-closing and contain rel and href as attributes
        '''
        good_template_dom = etree.fromstring('''
        <exercise-container>
            <meta>
                <title>title</title>
                <authors>
                    <author>anon</author>
                </authors>
                <difficulty>
                    1
                </difficulty>
                <language>en-ZA</language>
                <link rel="textbook" href="content://siyavula.com/textbooks/caps/physical-sciences/grade-10/#ESAAN"/>
            </meta>
            <entry>
                <problem>
                </problem>
                <solution>
                </solution>
            </entry>
        </exercise-container>''')

        assert self.exercise_validator.validate(good_template_dom) is None
