"""
Test specific xml tags to ensure they are performing as expected.

This also tests that the validator does in fact load a spec and validate against that spec.
"""

from lxml import etree
from unittest import TestCase
from XmlValidator import ExerciseValidator


class RadioButtonValidatorTests(TestCase):
    """
    Test that the ExerciseValidator class correctly validates a given XML structure for the radio
    buttons.
    """

    def setUp(self):
        self.exercise_validator = ExerciseValidator()

    def test_validate_with_radio_buttons_without_text(self):
        """validate: None when radio buttons do not have text, i.e. <button></button>."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button></button>
                                <button></button>
                                <button></button>
                                <button></button>
                                <button></button>
                             </radio>
                        </query>
                        <type>
                            <value>radiobutton</value>
                        </type>
                        <correct>
                            <value>1</value>
                        </correct>
                        <marks>
                            <value>1</value>
                        </marks>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_text_only(self):
        """validate: None when radio buttons have text only."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                </button>
                                <button>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                </button>
                                <button>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_inline_elements(self):
        """validate: None when radio buttons have inline elements only."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                                    do eiusmod tempor incididunt ut labore et dolore magna.
                                    Number <number>3.14</number> Nth e.g. <nth>1</nth>
                                    Percentages e.g. <percentage>34</percentage> Super- and
                                    subscripts e.g. <sup>up</sup> <sub>down</sub> Units e.g.
                                    <unit>m&#183;s<sup>-1 </sup></unit> Numbers with units e.g.
                                    <unit_number><number>3.14
                                    </number><unit>m&#183;s<sup>-1</sup></unit>
                                    </unit_number> Currency e.g. <currency><number>3.14</number>
                                    </currency> Chemical compound e.g. <chem_compound>H_2O
                                    </chem_compound> Spectroscopic notation e.g.
                                    <spec_note>3s^{2}3p^{5}</spec_note> Nuclear notation e.g.
                                    <nuclear_notation><symbol>Z</symbol><mass_number>x
                                    </mass_number><atomic_number>y</atomic_number>
                                    </nuclear_notation> Emphasis
                                    e.g. <emphasis>boom!</emphasis> Style (font colour) e.g.
                                    <style font-color="red">hypotenuse</style> In-line latex
                                    e.g. <latex>e^{i\pi} + 1 = 0</latex> In-line tip e.g.
                                    <note type="inlinetip">tip your hat</note> Web link e.g.
                                    <link url="www.google.com">Google</link>
                                </button>
                                <button>
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                                    do eiusmod tempor incididunt ut labore et dolore magna.
                                    Number <number>3.14</number> Nth e.g. <nth>1</nth>
                                    Percentages e.g. <percentage>34</percentage> Super- and
                                    subscripts e.g. <sup>up</sup> <sub>down</sub> Units e.g.
                                    <unit>m&#183;s<sup>-1 </sup></unit> Numbers with units e.g.
                                    <unit_number><number>3.14
                                    </number><unit>m&#183;s<sup>-1</sup></unit>
                                    </unit_number> Currency e.g. <currency><number>3.14</number>
                                    </currency> Chemical compound e.g. <chem_compound>H_2O
                                    </chem_compound> Spectroscopic notation e.g.
                                    <spec_note>3s^{2}3p^{5}</spec_note> Nuclear notation e.g.
                                    <nuclear_notation><symbol>Z</symbol><mass_number>x
                                    </mass_number><atomic_number>y</atomic_number>
                                    </nuclear_notation> Emphasis
                                    e.g. <emphasis>boom!</emphasis> Style (font colour) e.g.
                                    <style font-color="red">hypotenuse</style> In-line latex
                                    e.g. <latex>e^{i\pi} + 1 = 0</latex> In-line tip e.g.
                                    <note type="inlinetip">tip your hat</note> Web link e.g.
                                    <link url="www.google.com">Google</link>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_para_tags_with_text_only(self):
        """validate: None when radio buttons have para tags."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                </button>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                </button>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_multiple_para_tags_with_mixed_content(self):
        """validate: None when radio buttons have multiple para tags with mixed content."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                                        do eiusmod tempor incididunt ut labore et dolore magna.
                                        Number <number>3.14</number> Nth e.g. <nth>1</nth>
                                        Percentages e.g. <percentage>34</percentage> Super- and
                                        subscripts e.g. <sup>up</sup> <sub>down</sub> Units e.g.
                                        <unit>m&#183;s<sup>-1 </sup></unit> Numbers with units e.g.
                                        <unit_number><number>3.14
                                        </number><unit>m&#183;s<sup>-1</sup></unit>
                                        </unit_number> Currency e.g. <currency><number>3.14</number>
                                        </currency> Chemical compound e.g. <chem_compound>H_2O
                                        </chem_compound> Spectroscopic notation e.g.
                                        <spec_note>3s^{2}3p^{5}</spec_note> Nuclear notation e.g.
                                        <nuclear_notation><symbol>Z</symbol><mass_number>x
                                        </mass_number><atomic_number>y</atomic_number>
                                        </nuclear_notation> Emphasis
                                        e.g. <emphasis>boom!</emphasis> Style (font colour) e.g.
                                        <style font-color="red">hypotenuse</style> In-line latex
                                        e.g. <latex>e^{i\pi} + 1 = 0</latex> In-line tip e.g.
                                        <note type="inlinetip">tip your hat</note> Web link e.g.
                                        <link url="www.google.com">Google</link>
                                    </para>
                                </button>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                                        do eiusmod tempor incididunt ut labore et dolore magna.
                                        Number <number>3.14</number> Nth e.g. <nth>1</nth>
                                        Percentages e.g. <percentage>34</percentage> Super- and
                                        subscripts e.g. <sup>up</sup> <sub>down</sub> Units e.g.
                                        <unit>m&#183;s<sup>-1 </sup></unit> Numbers with units e.g.
                                        <unit_number><number>3.14
                                        </number><unit>m&#183;s<sup>-1</sup></unit>
                                        </unit_number> Currency e.g. <currency><number>3.14</number>
                                        </currency> Chemical compound e.g. <chem_compound>H_2O
                                        </chem_compound> Spectroscopic notation e.g.
                                        <spec_note>3s^{2}3p^{5}</spec_note> Nuclear notation e.g.
                                        <nuclear_notation><symbol>Z</symbol><mass_number>x
                                        </mass_number><atomic_number>y</atomic_number>
                                        </nuclear_notation> Emphasis
                                        e.g. <emphasis>boom!</emphasis> Style (font colour) e.g.
                                        <style font-color="red">hypotenuse</style> In-line latex
                                        e.g. <latex>e^{i\pi} + 1 = 0</latex> In-line tip e.g.
                                        <note type="inlinetip">tip your hat</note> Web link e.g.
                                        <link url="www.google.com">Google</link>
                                    </para>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_latex_block_elements(self):
        """validate: None when radio buttons have latex block elements."""
        good_template_dom = etree.fromstring(r'''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <latex display="block">
                                        \begin{aligned}
                                             z &amp; = 5x^5 + 4x^4 - 3xy^2 - 6y^{\frac{2}{3}} \\
                                               &amp; = 3x
                                        \end{aligned}
                                    </latex>
                                </button>
                                <button>
                                    <latex display="block">
                                        \begin{aligned}
                                             z &amp; = 5x^5 + 4x^4 - 3xy^2 - 6y^{\frac{2}{3}} \\
                                               &amp; = 3x^{\frac{3}{5}}
                                        \end{aligned}
                                    </latex>
                                </button>
                                <button>
                                    <latex display="block">
                                        \begin{aligned}
                                             z &amp; = 5x^5 + 4x^4 - 3xy^2 - 6y^{\frac{2}{3}} \\
                                               &amp; = \frac{2}{3}x
                                        \end{aligned}
                                    </latex>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_tikzpicture_images(self):
        """validate: None when radio buttons have tikzpicture images."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <tikzpicture>
                                        <usepackage>pgfplots</usepackage>
                                        <src>hist_normal.tikz</src>
                                    </tikzpicture>
                                </button>
                                <button>
                                    <tikzpicture>
                                        <usepackage>pgfplots</usepackage>
                                        <src>hist_flat.tikz</src>
                                    </tikzpicture>
                                </button>
                                <button>
                                    <tikzpicture>
                                        <usepackage>pgfplots</usepackage>
                                        <src>hist_right.tikz</src>
                                    </tikzpicture>
                                </button>
                                <button>
                                    <tikzpicture>
                                        <usepackage>pgfplots</usepackage>
                                        <src>hist_left.tikz</src>
                                    </tikzpicture>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_quote_tags(self):
        """validate: None when radio buttons have quote tags."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <quote>
                                        <emphasis>Something</emphasis> is the thing that defines
                                        the law
                                    </quote>
                                </button>
                                <button>
                                    <quote>
                                        <emphasis>Something</emphasis> is the thing that defines
                                        the law
                                    </quote>
                                </button>
                                <button>
                                    <quote>
                                        <emphasis>Something</emphasis> is the thing that defines
                                        the law
                                    </quote>
                                </button>
                                <button>
                                    <quote>
                                        <emphasis>Something</emphasis> is the thing that defines
                                        the law
                                    </quote>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_radio_button_with_different_block_elements(self):
        """validate: None when radio buttons have different block elements."""
        good_template_dom = etree.fromstring(r'''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <radio>
                                <button>
                                    <quote>
                                        <emphasis>Something</emphasis> is the thing that defines
                                        the law
                                    </quote>
                                </button>
                                <button>
                                    <tikzpicture>
                                        <usepackage>pgfplots</usepackage>
                                        <src>hist_normal.tikz</src>
                                    </tikzpicture>
                                </button>
                                <button>
                                    <latex display="block">
                                        \begin{aligned}
                                             z &amp; = 5x^5 + 4x^4 - 3xy^2 - 6y^{\frac{2}{3}} \\
                                               &amp; = 3x
                                        \end{aligned}
                                    </latex>
                                </button>
                                <button>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                                    </para>
                                    <para>
                                        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                                        do eiusmod tempor incididunt ut labore et dolore magna.
                                        Number <number>3.14</number> Nth e.g. <nth>1</nth>
                                        Percentages e.g. <percentage>34</percentage> Super- and
                                        subscripts e.g. <sup>up</sup> <sub>down</sub> Units e.g.
                                        <unit>m&#183;s<sup>-1 </sup></unit> Numbers with units e.g.
                                        <unit_number><number>3.14
                                        </number><unit>m&#183;s<sup>-1</sup></unit>
                                        </unit_number> Currency e.g. <currency><number>3.14</number>
                                        </currency> Chemical compound e.g. <chem_compound>H_2O
                                        </chem_compound> Spectroscopic notation e.g.
                                        <spec_note>3s^{2}3p^{5}</spec_note> Nuclear notation e.g.
                                        <nuclear_notation><symbol>Z</symbol><mass_number>x
                                        </mass_number><atomic_number>y</atomic_number>
                                        </nuclear_notation> Emphasis
                                        e.g. <emphasis>boom!</emphasis> Style (font colour) e.g.
                                        <style font-color="red">hypotenuse</style> In-line latex
                                        e.g. <latex>e^{i\pi} + 1 = 0</latex> In-line tip e.g.
                                        <note type="inlinetip">tip your hat</note> Web link e.g.
                                        <link url="www.google.com">Google</link>
                                    </para>
                                </button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)

    def test_validate_with_query_tag_with_two_response_types_radio_button_and_numeric(self):
        """validate: None when query tags have two response types, one being radio buttons."""
        good_template_dom = etree.fromstring('''
            <exercise-container>
                <meta>
                </meta>
                <entry>
                    <problem>
                    </problem>
                    <response>
                        <query>
                            <para>
                                <latex>y = </latex> <input/>
                            </para>
                            <para>
                                My favourite colour is:
                            </para>
                            <radio>
                                <button>Blue</button>
                                <button>Green</button>
                                <button>Yellow</button>
                                <button>Purple</button>
                            </radio>
                        </query>
                    </response>
                    <solution>
                    </solution>
                </entry>
            </exercise-container>''')

        self.assertEqual(self.exercise_validator.validate(good_template_dom), None)
