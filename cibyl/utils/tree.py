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
from typing import Any, Generic, Iterable, Optional, TypeVar

from anytree import NodeMixin, findall

T = TypeVar("T", bound=Any)


class Leaf(Generic[T], NodeMixin):
    def __init__(
        self,
        name: str,
        parent: Optional['Leaf[T]'] = None,
        children: Optional[Iterable['Leaf[T]']] = None,
        value: Optional[T] = None
    ):
        super().__init__()

        if children is None:
            children = ()

        # Mixin values
        self.parent = parent
        self.children = children

        # Own values
        self.name = name
        self.value = value


class Tree(Generic[T]):
    def __init__(self, root: Leaf[T]):
        self._root = root

    @property
    def root(self) -> Leaf[T]:
        return self._root

    def find_by_name(self, name: str) -> Iterable[Leaf[T]]:
        return findall(self.root, lambda leaf: leaf.name == name)
