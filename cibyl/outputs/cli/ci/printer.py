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
from abc import ABC, abstractmethod


class CIPrinter(ABC):
    """Interface for printers of a CI model hierarchy.
    """

    @abstractmethod
    def print_environment(self, env):
        """
        :param env: The environment.
        :type env: :class:`cibyl.models.ci.base.environment.Environment`
        :return: Textual representation of the provided model.
        :rtype: str
        """
        raise NotImplementedError