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
import argparse
import logging
from typing import Callable, List

from cibyl.cli.argument import Argument

LOG = logging.getLogger(__name__)


class CustomAction(argparse.Action):
    """Custom argparse.Action that allows in addition, to specify
    whether an argument data is populated, the function associated
    with the argument and the level in the models.
    """
    def __init__(self, *args, func: Callable = None, populated: bool = False,
                 level: int = -1, ranged: bool = False, **kwargs):
        """
        argparse custom action.
        :param func: the function the argument is associated with
        """
        self.func = func
        self.level = level
        self.populated = populated
        self.ranged = ranged
        super().__init__(*args, **kwargs)

    def __call__(self, parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace, values: List[str],
                 option_string: str = None):
        if self.default and not values:
            values = self.default
        setattr(namespace, self.dest, Argument(
            name=self.dest, description=self.help, arg_type=self.type,
            nargs=self.nargs, level=self.level, func=self.func,
            ranged=self.ranged, populated=self.populated,
            value=values))


class Parser:
    """This is a conceptual class representation of an app parser.
    The parser created as basic argparse based parser and later it's
    extended with arguments collected from the different CI models'
    attributes.
    """

    def __init__(self, ci_args: dict = None, app_args: dict = None):
        self.ci_args = ci_args
        if not ci_args:
            self.ci_args = {}
        self.app_args = app_args
        if not app_args:
            self.app_args = {}
        self.argument_parser = argparse.ArgumentParser()
        self.__add_arguments()

    def __add_arguments(self) -> None:
        """Creates argparse parser with all its sub-parsers."""
        self.argument_parser.add_argument(
            '--debug', '-d', action='store_true',
            dest="debug", help='turn on debug')
        self.argument_parser.add_argument(
            '--config', '-c', dest="config_file_path")
        self.argument_parser.add_argument(
            '--log-file', dest="log_file",
            help='Path to store the output, default is cibyl_output.log')
        self.argument_parser.add_argument(
            '--log-mode', dest="log_mode",
            choices=("terminal", "file", "both"),
            help='Where to write the output, default is both')
        self.argument_parser.add_argument(
            '--output-format', '-f', choices=("text", "colorized", "json"),
            dest="output_style", default="colorized",
            help="Sets the output format."
        )
        self.argument_parser.add_argument(
            '--plugin', '-p', dest="plugin", default="openstack")
        self.argument_parser.add_argument(
            '-v', '--verbose', dest="verbosity", default=0, action="count",
            help="Causes Cibyl to print more debug messages. "
                 "Adding multiple -v will increase the verbosity.")

    def print_help(self) -> None:
        """Call argparse's print_help method to show the help message with the
        arguments that are currently added."""
        self.argument_parser.print_help()

    def parse(self, arguments: List[Argument] = None) -> None:
        """Parse application and CI models arguments.

        Sets the attributes ci_args and app_args with dictionaries
        including the parsed arguments.

        :param arguments: Arguments to parse
        """
        arguments = vars(self.argument_parser.parse_args(arguments))
        # Keep only the used arguments
        self.ci_args = {arg_name: arg_value for arg_name, arg_value in
                        arguments.items() if isinstance(arg_value, Argument)}
        self.app_args = {arg_name: arg_value for arg_name, arg_value in
                         arguments.items() if arg_value is not None and not
                         isinstance(arg_value, Argument)}

    def get_group(self, group_name: str) -> argparse._ArgumentGroup:
        """Returns the argument parser group based on a given group_name

        :param group_name: The name of the group

        :return: An argparse argument group if it exists and matches
                 the given group name, otherwise returns None
        """
        # pylint: disable=protected-access
        # Access the private member '_action_groups' to check
        # whether the group exists
        for action_group in self.argument_parser._action_groups:
            if action_group.title == group_name:
                return action_group
        return None

    def extend(self, arguments: List[Argument], group_name: str,
               level: int = 0) -> None:
        """Adds arguments to a specific argument parser group.

        :param arguments: A list of argument objects
        :param group_name: The name of the argument parser group
        :param level: The level of the arguments in models
        """
        group = self.get_group(group_name)
        # If the group doesn't exists, we would like to add it
        # so arguments are grouped based on the model class they belong to
        if not group:
            group = self.argument_parser.add_argument_group(group_name)

        try:
            for arg in arguments:
                group.add_argument(
                    arg.name, type=arg.arg_type,
                    help=arg.description, nargs=arg.nargs,
                    action=CustomAction, func=arg.func,
                    ranged=arg.ranged,
                    populated=arg.populated,
                    default=arg.default,
                    level=level, choices=arg.choices)
        except argparse.ArgumentError:
            pass
