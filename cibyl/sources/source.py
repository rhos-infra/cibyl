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
import logging

import requests

from cibyl.exceptions.source import (NoSupportedSourcesFound,
                                     TooManyValidSources)

LOG = logging.getLogger(__name__)


def safe_request_generic(request, custom_error):
    """Decorator that wraps any errors coming out of a call around a
    custom_error class.

    :param request: The unsafe call to watch errors on.
    :return: The input call decorated to raise the desired error type.
    """

    def request_handler(*args, **kwargs):
        """Calls the unsafe function and wraps any errors coming out of it
        around a custom_error class.

        :param args: Arguments with which the function is called.
        :return: Output of the called function.
        """
        try:
            return request(*args, **kwargs)
        except requests.exceptions.SSLError as ex:
            raise custom_error(
                "Please set certificates in order to connect to the system"
            ) from ex
        except Exception as ex:
            raise custom_error('Failure on request to target host.') from ex

    return request_handler


class Source:
    """Represents a source of a system on which queries are performed."""

    def __init__(self, name: str, driver: str, url: str = None,
                 priority: int = 0):
        self.name = name
        self.driver = driver
        self.url = url
        self.priority = priority

    @staticmethod
    def get_source_method(system_name: str, sources: list, func_name: str):
        """Returns a method of a single source given all the sources
        of the system and the name of function.

        An exception is raised if there are no sources with such function
        name or if there are multiple sources that have this function.

        :param system_name: The name of system
        :type system_name: str
        :param sources: List of Source instances
        :type sources: list[Source]
        :param func_name: The name of the function to invoke
        :type func_name: str
        """
        valid_sources = []
        for source in sources:
            if hasattr(source, func_name):
                valid_sources.append(source)
        if len(valid_sources) == 0:
            raise NoSupportedSourcesFound(system_name,
                                          func_name)
        if len(valid_sources) > 1:
            raise TooManyValidSources(system_name)
        return getattr(valid_sources[0], func_name)
