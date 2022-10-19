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
from dataclasses import dataclass, field
from typing import Optional

from overrides import overrides

from cibyl.sources.zuul.apis import ZuulAPI as Zuul
from cibyl.sources.zuul.queries.composition import AggregatedQuery
from cibyl.sources.zuul.queries.composition.quick import QuickQuery
from cibyl.sources.zuul.queries.jobs import perform_jobs_query
from cibyl.sources.zuul.queries.variants import perform_variants_query
from cibyl.sources.zuul.utils.variants.hierarchy import HierarchyCrawlerFactory


class HierarchyQuery(QuickQuery):
    @dataclass
    class Tools(AggregatedQuery.Tools):
        """Tools this uses to do its task.
        """
        crawlers: HierarchyCrawlerFactory = field(
            default_factory=lambda: HierarchyCrawlerFactory()
        )

    def __init__(self, api: Zuul, tools: Optional[Tools] = None):
        if tools is None:
            tools = HierarchyQuery.Tools()

        super().__init__(api, tools)

    @property
    @overrides
    def tools(self) -> Tools:
        """
        :return: Tools used by this to perform its task.
        """
        return self._tools

    @overrides
    def with_jobs_query(self, **kwargs) -> 'AggregatedQuery':
        for job in perform_jobs_query(self.api, **kwargs):
            for variant in perform_variants_query(job):
                crawler = self.tools.crawlers.from_variant(variant)

                for level in crawler:
                    if level.name == variant.name:
                        continue

                    kwargs['jobs'].value.append(f'^{level.name}$')

        return super().with_variants_query(**kwargs)