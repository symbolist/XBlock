"""
Tests for classes extending Field.
"""

# Allow accessing protected members for testing purposes
# pylint: disable=W0212

from mock import MagicMock, Mock
import unittest

import datetime as dt
import pytz
import warnings
from contextlib import contextmanager

from xblock.core import XBlock, Scope
from xblock.field_data import DictFieldData
from xblock.fields import (
    Any, Boolean, Dict, Field, Float,
    Integer, List, String, DateTime, Reference, ReferenceList, Sentinel
)

from xblock.test.tools import assert_equals, assert_not_equals, assert_not_in
from xblock.fields import scope_key, ScopeIds


class FieldTest(unittest.TestCase):
    """ Base test class for Fields. """

    def field_totest(self):
        """Child classes should override this with the type of field
        the test is testing."""
        return None

    def set_and_get_field(self, arg, enforce_type):
        """
        Set the field to arg in a Block, get it and return it
        """
        class TestBlock(XBlock):
            """
            Block for testing
            """
            field_x = self.field_totest(enforce_type=enforce_type)

        block = TestBlock(MagicMock(), DictFieldData({}), Mock())
        block.field_x = arg
        return block.field_x

    @contextmanager
    def assertDeprecationWarning(self, count=1):
        """Asserts that the contained code raises `count` deprecation warnings"""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            yield
        self.assertEquals(count, sum(
            1 for warning in caught
            if issubclass(warning.category, DeprecationWarning)
        ))

    def assertJSONOrSetEquals(self, expected, arg):
        """
        Asserts the result of field.from_json and of setting field.
        """
        # from_json(arg) -> expected
        self.assertEqual(expected, self.field_totest().from_json(arg))
        # set+get with enforce_type arg -> expected
        self.assertEqual(expected, self.set_and_get_field(arg, True))
        # set+get without enforce_type arg -> arg
        # provoking a warning unless arg == expected
        count = 0 if arg == expected else 1
        with self.assertDeprecationWarning(count):
            self.assertEqual(arg, self.set_and_get_field(arg, False))

    def assertToJSONEquals(self, expected, arg):
        """
        Assert that serialization of `arg` to JSON equals `expected`.
        """
        self.assertEqual(expected, self.field_totest().to_json(arg))

    def assertJSONOrSetValueError(self, arg):
        """
        Asserts that field.from_json or setting the field throws a ValueError
        for the supplied value.
        """
        # from_json and set+get with enforce_type -> ValueError
        with self.assertRaises(ValueError):
            self.field_totest().from_json(arg)
        with self.assertRaises(ValueError):
            self.set_and_get_field(arg, True)
        # set+get without enforce_type -> warning
        with self.assertDeprecationWarning():
            self.set_and_get_field(arg, False)

    def assertJSONOrSetTypeError(self, arg):
        """
        Asserts that field.from_json or setting the field throws a TypeError
        for the supplied value.
        """
        # from_json and set+get with enforce_type -> TypeError
        with self.assertRaises(TypeError):
            self.field_totest().from_json(arg)
        with self.assertRaises(TypeError):
            self.set_and_get_field(arg, True)
        # set+get without enforce_type -> warning
        with self.assertDeprecationWarning():
            self.set_and_get_field(arg, False)


class IntegerTest(FieldTest):
    """
    Tests the Integer Field.
    """
    field_totest = Integer

    def test_integer(self):
        self.assertJSONOrSetEquals(5, '5')
        self.assertJSONOrSetEquals(0, '0')
        self.assertJSONOrSetEquals(-1023, '-1023')
        self.assertJSONOrSetEquals(7, 7)
        self.assertJSONOrSetEquals(0, False)
        self.assertJSONOrSetEquals(1, True)

    def test_float_converts(self):
        self.assertJSONOrSetEquals(1, 1.023)
        self.assertJSONOrSetEquals(-3, -3.8)

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')

    def test_error(self):
        self.assertJSONOrSetValueError('abc')
        self.assertJSONOrSetValueError('[1]')
        self.assertJSONOrSetValueError('1.023')

        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})


class FloatTest(FieldTest):
    """
    Tests the Float Field.
    """
    field_totest = Float

    def test_float(self):
        self.assertJSONOrSetEquals(.23, '.23')
        self.assertJSONOrSetEquals(5, '5')
        self.assertJSONOrSetEquals(0, '0.0')
        self.assertJSONOrSetEquals(-1023.22, '-1023.22')
        self.assertJSONOrSetEquals(0, 0.0)
        self.assertJSONOrSetEquals(4, 4)
        self.assertJSONOrSetEquals(-0.23, -0.23)
        self.assertJSONOrSetEquals(0, False)
        self.assertJSONOrSetEquals(1, True)

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')

    def test_error(self):
        self.assertJSONOrSetValueError('abc')
        self.assertJSONOrSetValueError('[1]')

        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})


class BooleanTest(FieldTest):
    """
    Tests the Boolean Field.
    """
    field_totest = Boolean

    def test_false(self):
        self.assertJSONOrSetEquals(False, "false")
        self.assertJSONOrSetEquals(False, "False")
        self.assertJSONOrSetEquals(False, "")
        self.assertJSONOrSetEquals(False, "any other string")
        self.assertJSONOrSetEquals(False, False)

    def test_true(self):
        self.assertJSONOrSetEquals(True, "true")
        self.assertJSONOrSetEquals(True, "TruE")
        self.assertJSONOrSetEquals(True, True)

    def test_none(self):
        self.assertJSONOrSetEquals(False, None)

    def test_everything_converts_to_bool(self):
        self.assertJSONOrSetEquals(True, 123)
        self.assertJSONOrSetEquals(True, ['a'])
        self.assertJSONOrSetEquals(False, [])


class StringTest(FieldTest):
    """
    Tests the String Field.
    """
    field_totest = String

    def test_json_equals(self):
        self.assertJSONOrSetEquals("false", "false")
        self.assertJSONOrSetEquals("abba", "abba")
        self.assertJSONOrSetEquals('"abba"', '"abba"')
        self.assertJSONOrSetEquals('', '')

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['a'])
        self.assertJSONOrSetTypeError(1.023)
        self.assertJSONOrSetTypeError(3)
        self.assertJSONOrSetTypeError([1])
        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError({})


class DateTest(FieldTest):
    """
    Tests of the Date field.
    """
    field_totest = DateTime

    def test_json_equals(self):
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04.567890'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04.000000'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            '2014-04-01T02:03:04Z'
        )
        self.assertJSONOrSetEquals(
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc),
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc)
        )

    def test_serialize(self):
        self.assertToJSONEquals(
            '2014-04-01T02:03:04.567890',
            dt.datetime(2014, 4, 1, 2, 3, 4, 567890).replace(tzinfo=pytz.utc)
        )

        self.assertToJSONEquals(
            '2014-04-01T02:03:04.000000',
            dt.datetime(2014, 4, 1, 2, 3, 4).replace(tzinfo=pytz.utc)
        )

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)
        self.assertJSONOrSetEquals(None, '')
        self.assertEqual(DateTime().to_json(None), None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['a'])
        self.assertJSONOrSetTypeError(5)
        self.assertJSONOrSetTypeError(5.123)

    def test_date_format_error(self):
        with self.assertRaises(ValueError):
            DateTime().from_json('invalid')

    def test_serialize_error(self):
        with self.assertRaises(TypeError):
            DateTime().to_json('not a datetime')


class AnyTest(FieldTest):
    """
    Tests the Any Field.
    """
    field_totest = Any

    def test_json_equals(self):
        self.assertJSONOrSetEquals({'bar'}, {'bar'})
        self.assertJSONOrSetEquals("abba", "abba")
        self.assertJSONOrSetEquals('', '')
        self.assertJSONOrSetEquals('3.2', '3.2')
        self.assertJSONOrSetEquals(False, False)
        self.assertJSONOrSetEquals([3, 4], [3, 4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)


class ListTest(FieldTest):
    """
    Tests the List Field.
    """
    field_totest = List

    def test_json_equals(self):
        self.assertJSONOrSetEquals([], [])
        self.assertJSONOrSetEquals(['foo', 'bar'], ['foo', 'bar'])
        self.assertJSONOrSetEquals([1, 3.4], [1, 3.4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)
        self.assertJSONOrSetTypeError({})


class ReferenceTest(FieldTest):
    """
    Tests the Reference Field.
    """
    field_totest = Reference

    def test_json_equals(self):
        self.assertJSONOrSetEquals({'id': 'bar', 'usage': 'baz'}, {'id': 'bar', 'usage': 'baz'})
        self.assertJSONOrSetEquals("i4x://myu/mycourse/problem/myproblem", "i4x://myu/mycourse/problem/myproblem")
        self.assertJSONOrSetEquals('', '')
        self.assertJSONOrSetEquals(3.2, 3.2)
        self.assertJSONOrSetEquals(False, False)
        self.assertJSONOrSetEquals([3, 4], [3, 4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)


class ReferenceListTest(FieldTest):
    """
    Tests the ReferenceList Field.
    """
    field_totest = ReferenceList

    def test_json_equals(self):
        self.assertJSONOrSetEquals([], [])
        self.assertJSONOrSetEquals(['foo', 'bar'], ['foo', 'bar'])
        self.assertJSONOrSetEquals([1, 3.4], [1, 3.4])

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)
        self.assertJSONOrSetTypeError({})


class DictTest(FieldTest):
    """
    Tests the Dict Field.
    """
    field_totest = Dict

    def test_json_equals(self):
        self.assertJSONOrSetEquals({}, {})
        self.assertJSONOrSetEquals({'a': 'b', 'c': 3}, {'a': 'b', 'c': 3})

    def test_none(self):
        self.assertJSONOrSetEquals(None, None)

    def test_error(self):
        self.assertJSONOrSetTypeError(['foo', 'bar'])
        self.assertJSONOrSetTypeError([])
        self.assertJSONOrSetTypeError('abc')
        self.assertJSONOrSetTypeError('1.23')
        self.assertJSONOrSetTypeError('true')
        self.assertJSONOrSetTypeError(3.7)
        self.assertJSONOrSetTypeError(True)


def test_field_name_defaults():
    # Tests field display name default values
    attempts = Integer()
    attempts._name = "max_problem_attempts"
    assert_equals('max_problem_attempts', attempts.display_name)

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List()

    assert_equals("field_x", TestBlock.field_x.display_name)


def test_scope_key():
    # Tests field display name default values
    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List(scope=Scope.settings, name='')
        settings_lst = List(scope=Scope.settings, name='')
        uss_lst = List(scope=Scope.user_state_summary, name='')
        user_lst = List(scope=Scope.user_state, name='')
        pref_lst = List(scope=Scope.preferences, name='')
        user_info_lst = List(scope=Scope.user_info, name='')

    sids = ScopeIds(user_id="_bob",
                    block_type="b.12#ob",
                    def_id="..",
                    usage_id="..")

    field_data = DictFieldData({})

    from test_runtime import TestRuntime
    runtime = TestRuntime(Mock(), field_data, [])
    block = TestBlock(runtime, field_data, sids)

    # Format: usage or block ID/field_name/user_id
    for item, correct_key in [[TestBlock.field_x, "__..../field__x/NONE.NONE"],
                              [TestBlock.user_info_lst, "NONE.NONE/user__info__lst/____bob"],
                              [TestBlock.pref_lst, "b..12_35_ob/pref__lst/____bob"],
                              [TestBlock.user_lst, "__..../user__lst/____bob"],
                              [TestBlock.uss_lst, "__..../uss__lst/NONE.NONE"],
                              [TestBlock.settings_lst, "__..../settings__lst/NONE.NONE"]]:
        key = scope_key(item, block)
        assert_equals(key, correct_key)


def test_field_display_name():
    attempts = Integer(display_name='Maximum Problem Attempts')
    attempts._name = "max_problem_attempts"
    assert_equals("Maximum Problem Attempts", attempts.display_name)

    boolean_field = Boolean(display_name="boolean field")
    assert_equals("boolean field", boolean_field.display_name)

    class TestBlock(XBlock):
        """
        Block for testing
        """
        field_x = List(display_name="Field Known as X")

    assert_equals("Field Known as X", TestBlock.field_x.display_name)


def test_values():
    # static return value
    field_values = ['foo', 'bar']
    test_field = String(values=field_values)
    assert_equals(field_values, test_field.values)

    # function to generate values
    test_field = String(values=lambda: [1, 4])
    assert_equals([1, 4], test_field.values)

    # default if nothing specified
    assert_equals(None, String().values)


def test_values_boolean():
    # Test Boolean, which has values defined
    test_field = Boolean()
    assert_equals(
        ({'display_name': "True", "value": True}, {'display_name': "False", "value": False}),
        test_field.values
    )


def test_values_dict():
    # Test that the format expected for integers is allowed
    test_field = Integer(values={"min": 1, "max": 100})
    assert_equals({"min": 1, "max": 100}, test_field.values)


def test_twofaced_field_access():
    # Check that a field with different to_json and from_json representations
    # persists and saves correctly.
    class TwoFacedField(Field):
        """A field that emits different 'json' than it parses."""
        def from_json(self, thestr):
            """Store an int, the length of the string parsed."""
            return len(thestr)

        def to_json(self, value):
            """Emit some number of X's."""
            return "X" * value

    class FieldTester(XBlock):
        """Test block for TwoFacedField."""
        how_many = TwoFacedField(scope=Scope.settings)

    original_json = "YYY"
    field_tester = FieldTester(MagicMock(), DictFieldData({'how_many': original_json}), Mock())

    # Test that the native value isn't equal to the original json we specified.
    assert_not_equals(field_tester.how_many, original_json)
    # Test that the native -> json value isn't equal to the original json we specified.
    assert_not_equals(TwoFacedField().to_json(field_tester.how_many), original_json)

    # The previous accesses will mark the field as dirty (via __get__)
    assert_equals(len(field_tester._dirty_fields), 1)
    # However, the field should not ACTUALLY be marked as a field that is needing to be saved.
    assert_not_in('how_many', field_tester._get_fields_to_save())   # pylint: disable=W0212


class SentinelTest(unittest.TestCase):
    """
    Tests of :ref:`xblock.fields.Sentinel`.
    """
    def test_equality(self):
        base = Sentinel('base')
        self.assertEquals(base, base)
        self.assertEquals(base, Sentinel('base'))
        self.assertNotEquals(base, Sentinel('foo'))
        self.assertNotEquals(base, 'base')

    def test_hashing(self):
        base = Sentinel('base')
        a_dict = {base: True}
        self.assertEquals(a_dict[Sentinel('base')], True)
        self.assertEquals(a_dict[base], True)
        self.assertNotIn(Sentinel('foo'), a_dict)
        self.assertNotIn('base', a_dict)
