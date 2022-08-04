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
from typing import NamedTuple

from cibyl.sources.zuul.apis import ZuulAPI as Zuul
from cibyl.sources.zuul.output import QueryOutput, QueryOutputBuilderFactory
from cibyl.sources.zuul.source import Zuul as Source


class SourceManager(ABC):
    class Tools(NamedTuple):
        output: QueryOutputBuilderFactory = QueryOutputBuilderFactory()

    def __init__(self, source: Source, tools: Tools = Tools()):
        self._api = source.api
        self._tools = tools

    @property
    def api(self) -> Zuul:
        return self._api

    @property
    def tools(self) -> Tools:
        return self._tools

    @abstractmethod
    def handle_tenants_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_projects_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_pipelines_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_jobs_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_variants_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_builds_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError

    @abstractmethod
    def handle_tests_query(self, **kwargs) -> QueryOutput:
        raise NotImplementedError
