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

from cibyl.plugins.openstack.deployment import Deployment
from cibyl.plugins.openstack.node import Node
from cibyl.plugins.openstack.service import Service


class TestOpenstackDeployment(TestCase):
    """Test openstack deployment model."""
    def setUp(self):
        self.release = '17.0'
        self.infra = 'ovb'
        self.services = {'nova': Service('nova', {})}
        self.nodes = {'controller-0': Node('controller-0', 'controller')}
        self.ip_version = "4"
        self.topology = "controllers:1"
        self.network = "vxlan"
        self.storage = "ceph"
        self.dvr = "true"
        self.tls_everywhere = "false"

        self.deployment = Deployment(self.release, self.infra, {}, {})
        self.second_deployment = Deployment(self.release, self.infra,
                                            self.nodes,
                                            self.services,
                                            ip_version=self.ip_version,
                                            topology=self.topology,
                                            network_backend=self.network,
                                            storage_backend=self.storage,
                                            dvr=self.dvr,
                                            tls_everywhere=self.tls_everywhere)

    def test_merge_method(self):
        """Test merge method of Deployment class."""
        self.assertIsNone(self.deployment.ip_version.value)
        self.assertEqual({}, self.deployment.services.value)
        self.assertEqual({}, self.deployment.nodes.value)
        self.deployment.merge(self.second_deployment)
        self.assertEqual(self.nodes, self.deployment.nodes.value)
        self.assertEqual(self.services, self.deployment.services.value)
        self.assertEqual(self.ip_version, self.deployment.ip_version.value)

    def test_add_node(self):
        """Test add_node method of Deployment class."""
        self.assertEqual({}, self.deployment.nodes.value)
        self.deployment.add_node(self.nodes['controller-0'])
        self.assertEqual(self.nodes, self.deployment.nodes.value)

    def test_add_service(self):
        """Test add_service method of Deployment class."""
        self.assertEqual({}, self.deployment.services.value)
        self.deployment.add_service(self.services['nova'])
        self.assertEqual(self.services, self.deployment.services.value)

    def test_merge_method_existing_service(self):
        """Test merge method of Deployment class."""

        service_to_add = Service('nova', {'option': 'false'})
        self.deployment.add_service(service_to_add)
        self.second_deployment.merge(self.deployment)
        service = self.second_deployment.services.value['nova']
        self.assertEqual(service.name.value, service_to_add.name.value)
        self.assertEqual(service.configuration.value,
                         service_to_add.configuration.value)