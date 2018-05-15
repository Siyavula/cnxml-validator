"""Tests for the coordinate tag."""

from lxml import etree
from unittest import TestCase
from XmlValidator import ExerciseValidator


class IntervalTagTests(TestCase):
    """SEt tag validation tests."""

    def setUp(self):
        """Instantiate the ExerciseValidator class."""
        self.exercise_validator = ExerciseValidator()
        self.template_dom = etree.parse('tests/interval_tag_tests/test_interval_tag.xml')

    def test_validate_template_with_coordinate_tags(self):
        """Validate: coordinate tag in a para tag within a problem tag."""
        self.assertEqual(self.exercise_validator.validate(etree.tostring(self.template_dom)), None)
