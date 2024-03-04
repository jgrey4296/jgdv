"""
The how a parser behaves in Instal, and a utility to test parsing
"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import pathlib as pl
from dataclasses import InitVar, dataclass, field
from importlib.readers import MultiplexedPath
from types import NoneType
from typing import (IO, TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, List, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from unittest.util import safe_repr

import instal.interfaces.ast as InASTs
import pyparsing as pp
import pyparsing.testing as ppt

##-- end imports

logging = logmod.getLogger(__name__)

class InstalParser_i(metaclass=abc.ABCMeta):
    """
    The abstract api of an Instal Parser.
    default implementations use pyparsing,
    but that isn't necessary.

    """


    @abc.abstractmethod
    def parse_institution(self, text:str|pl.Path, *, parser_source=str|pl.Path) -> list[InASTs.InstalAST]: pass
    @abc.abstractmethod
    def parse_bridge(self, text:str|pl.Path, *, parser_source=str|pl.Path) -> list[InASTs.InstalAST]: pass
    @abc.abstractmethod
    def parse_domain(self, text:str|pl.Path, *, parser_source=str|pl.Path) -> list[InASTs.InstalAST]: pass
    @abc.abstractmethod
    def parse_situation(self, text:str|pl.Path, *, parser_source=str|pl.Path) -> list[InASTs.InstalAST]: pass
    @abc.abstractmethod
    def parse_query(self, text:str|pl.Path, *, parser_source=str|pl.Path) -> list[InASTs.InstalAST]: pass




class InstalParserTestCase(TestCase):
    """
    A Utility class for simplifying testing parsers
    """

    current_parse_text : None|str = None

    @classmethod
    def setUpClass(cls):
        # pylint: disable=consider-using-f-string
        LOGLEVEL      = logmod.DEBUG
        LOG_FILE_NAME = "log.{}".format(pl.Path(__file__).stem)

        cls.file_h        = logmod.FileHandler(LOG_FILE_NAME, mode="w")
        cls.file_h.setLevel(LOGLEVEL)

        logging.root.addHandler(cls.file_h)
        logging.root.setLevel(logmod.NOTSET)


    @classmethod
    def tearDownClass(cls):
        logmod.root.removeHandler(cls.file_h)


    def assertFilesParse(self, dsl:pp.ParserElement, *files:str|pl.Path, loc:None|MultiplexedPath=None):
        """
        Assert all files parse without error.
        Can be simple names all appended to the path `loc` if provided,
        which is expected to be a MultiplexedPath provided by
        importlib.resources.files
        """
        self.assertIsInstance(dsl, pp.ParserElement)
        self.assertTrue(isinstance(loc, (NoneType, MultiplexedPath)))
        file_paths = (pl.Path(path) for path in files)
        file_locs  = (loc / path for path in file_paths) if loc is not None else file_paths

        for path in file_locs:
            with self.subTest(msg=path):
                self.assertTrue(path.exists())
                try:
                    dsl.parse_file(path, parse_all=True)
                except pp.ParseException as err:
                    raise self.failureException("\n"+err.explain(0)) from None

    def yieldParseResults(self, dsl:pp.ParserElement, *tests) -> Iterator[Any]:
        """
        For each test, yield its result and additional values
        for manual testing
        """
        for test in tests:
            text, data = None, None
            self.assertIsInstance(test, (str, tuple, dict))
            match test:
                case str():
                    text = test
                    data = None
                case tuple():
                    text = test[0]
                    data = test
                case dict():
                    self.assertIn("text", test)
                    text = test['text']
                    data = test
                case _:
                    self.failureException("Test passed to yieldParseResults is confusing: %s", test)

            self._set_current_parse_text(text)
            try:
                result   = dsl.parse_string(text, parse_all=True)
            except pp.ParseException as err:
                raise self.failureException("\n"+err.explain(0)) from None

            yield result, data

        self._clear_current_parse_text()

    def assertParseResults(self, dsl:pp.ParserElement, *tests):
        """
        Run Tests of definition (testStr, {namedresults}?, listResults...)
        """
        self.assertIsInstance(dsl, pp.ParserElement)
        for test in tests:
            self.assertIsInstance(test, tuple, test[0])
            self.assertGreaterEqual(len(test), 2, test[0])
            with self.subTest(msg=test[0]):
                try:
                    result   = dsl.parse_string(test[0], parse_all=True)
                except pp.ParseException as err:
                    raise self.failureException("\n"+err.explain(0)) from None

                named    = test[1] if isinstance(test[1], dict) else {}
                expected = test[1 if not bool(named) else 2:]

                for x,y in named.items():
                    self.assertIn(x, result, test[0])
                    self.assertEqual(result[x], y, test[0])

                self.assertEqual(len(result), len(expected), test[0])
                for x,y in zip(result, expected):
                    self.assertEqual(x, y, test[0])


    def assertParseResultsIsInstance(self, dsl:pp.ParserElement, *tests):
        """
        Run Tests of definition (testStr, {namedresults}?, listResults...)
        """
        self.assertIsInstance(dsl, pp.ParserElement)
        for test in tests:
            self.assertIsInstance(test, tuple)
            self.assertGreaterEqual(len(test), 2)
            with self.subTest(test[0]):
                result   = dsl.parse_string(test[0], parse_all=True)
                expected = test[1:]
                self.assertEqual(len(result), len(expected))
                self.assertTrue(all(isinstance(x, type) for x in expected))

                for x,y in zip(result, expected):
                    self.assertIsInstance(x, y)

    def assertParserFails(self, dsl:pp.ParserElement, *tests):
        """
        Run Tests expected to fail: (testStr, failLoc)
        """
        self.assertIsInstance(dsl, pp.ParserElement)
        for test in tests:
            with self.subTest(test[0]):
                fail_loc = test[1]
                test_exc = test[2] if len(test) > 2 else pp.ParseException
                self.assertIsInstance(fail_loc, int)
                self.assertLess(fail_loc, len(test[0]))

                with self.assertRaises(test_exc) as cm:
                    dsl.parse_string(test[0], parse_all=True)

                exc = cm.exception
                if hasattr(exc, "loc"):
                    self.assertEqual(exc.loc, fail_loc,
                                     "\n"+exc.explain(0))


    def assertAllIn(self, values, container):
        for value in values:
            self.assertIn(value, container)


    def _formatMessage(self, msg, standardMsg):
        """Honour the longMessage attribute when generating failure messages.
        If longMessage is False this means:
        * Use only an explicit message if it is provided
        * Otherwise use the standard message for the assert

        If longMessage is True:
        * Use the standard message
        * If an explicit message is provided, plus ' : ' and the explicit message
        """
        # pylint: disable=too-many-return-statements, consider-using-f-string
        if not self.longMessage:
            return msg or standardMsg

        if msg is None and self.current_parse_text is None:
            return standardMsg

        if msg is None and self.current_parse_text is not None:
            return standardMsg + f'\n\n in:\n{self.current_parse_text}'

        try:
            # don't switch to '{}' formatting in Python 2.X
            # it changes the way unicode input is handled
            if self.current_parse_text:
                return '%s : %s\n\nin:\n%s' % (standardMsg, msg, self.current_parse_text)

            return '%s : %s' % (standardMsg, msg)
        except UnicodeDecodeError:
            if self.current_parse_text is not None:
                return  '%s : %s\n\nin:\n%s' % (safe_repr(standardMsg), safe_repr(msg), safe_repr(self.current_parse_text))

            return  '%s : %s' % (safe_repr(standardMsg), safe_repr(msg or self.current_parse_text))


    def _set_current_parse_text(self, text:str):
        as_lines = text.split("\n")
        rejoined = "\n".join(x.strip() for x in as_lines)
        self.current_parse_text = f'"{rejoined}"\n(ws trimmed)'

    def _clear_current_parse_text(self):
        self.current_parse_text = None
