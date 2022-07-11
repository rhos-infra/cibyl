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
from unittest import TestCase

from tripleo.insights.tripleo import THTPathCreator


class TestTHTPathCreator(TestCase):
    """Tests for :class:`THTPathCreator`.
    """

    def test_creates_scenario_path(self):
        """Checks the default template for a scenario path.
        """
        file = 'scenario001.yaml'

        creator = THTPathCreator()

        self.assertEqual(
            f'ci/environments/{file}',
            creator.create_scenario_path(file)
        )
