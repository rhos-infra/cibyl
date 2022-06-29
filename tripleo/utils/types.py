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
import pathlib
from typing import Any, Dict

from tripleo.utils.strings import is_url

YAML = Dict[str, Any]


class Path(pathlib.Path):
    def to_str(self) -> str:
        return str(self)


class URL(str):
    def __new__(cls, value: str) -> 'URL':
        # Avoid false positives by removing leading and trailing whitespaces
        value = value.strip()

        if not is_url(value):
            msg = f"String does not represent a valid URL: '{value}'."
            raise ValueError(msg)

        return super().__new__(cls, value)
