"""
#    Copyright 2022 Red Hat
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
from abc import ABC

from cibyl.cli.query import QueryType
from cibyl.utils.colors import ColorPalette, DefaultPalette


class Printer(ABC):
    """Base class for all implementations of an output style.
    """

    def __init__(self,
                 query: QueryType = QueryType.NONE,
                 verbosity: int = 0):
        """Constructor.

        :param query: Type of query requested by the user. Determines how
            far down the model hierarchy the printer will go.
        :param verbosity: How verbose the output is to be expected. The
            bigger this is, the more is printed for each hierarchy level.
        """
        self._query = query
        self._verbosity = verbosity

    @property
    def query(self) -> QueryType:
        """
        :return: Query type requested by user.
        """
        return self._query

    @property
    def verbosity(self):
        """
        :return: Verbosity level of this printer.
        :rtype: int
        """
        return self._verbosity


class ColoredPrinter(Printer, ABC):
    """Base class for output styles based around coloring.
    """

    def __init__(self,
                 query: QueryType = QueryType.NONE,
                 verbosity: int = 0,
                 palette: ColorPalette = DefaultPalette(),
                 args=None):
        """Constructor.

        See parents for more information.

        :param palette: Palette of colors to be used.
        """
        super().__init__(query, verbosity)

        self._palette = palette
        self._args = args

    @property
    def palette(self) -> ColorPalette:
        """
        :return: The palette currently in use.
        """
        return self._palette

    @property
    def args(self):
        """
        :return: The command line arguments. Used to determine what to print
        :rtype: dict
        """
        return self._args
