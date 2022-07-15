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
import sys
from unittest import TestCase

from tripleo.insights import DeploymentLookUp
from tripleo.insights import DeploymentOutline as Outline
from tripleo.utils.logging import LogOutput, enable_logging


class TestInsights(TestCase):
    """Checks that the deployment summary generated by insights is correct.
    """

    def setUp(self):
        # Enable output into console
        enable_logging(logging.DEBUG, LogOutput.ToStream, stream=sys.stdout)

    def test_tls_everywhere(self):
        """Checks that the state of TLS-Everywhere is extracted from a
        scenario file.
        """
        outline = Outline(featureset='config/general_config/featureset039.yml')
        lookup = DeploymentLookUp()
        result = lookup.run(outline)

        self.assertEqual('On', result.tls_everywhere)

    def test_cinder_backend(self):
        """Checks that the cinder backend is extracted from a scenario
        file.
        """
        outline = Outline(featureset='config/general_config/featureset016.yml')
        lookup = DeploymentLookUp()
        result = lookup.run(outline)

        self.assertEqual('rbd', result.cinder_backend)

    def test_neutron_backend(self):
        """Checks that the neutron backend is extracted from a scenario
        file.
        """
        outline = Outline(featureset='config/general_config/featureset030.yml')
        lookup = DeploymentLookUp()
        result = lookup.run(outline)

        self.assertEqual('vxlan', result.neutron_backend)
