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
from unittest.mock import Mock, call

from tripleo.insights.deployment import (EnvironmentInterpreter,
                                         FeatureSetInterpreter,
                                         NodesInterpreter, ReleaseInterpreter,
                                         ScenarioInterpreter)
from tripleo.insights.exceptions import IllegibleData
from tripleo.insights.io import Topology


class TestEnvironmentInterpreter(TestCase):
    """Tests for :class:`EnvironmentInterpreter`.
    """

    def test_checks_data_validity(self):
        """Verifies that the class checks that the data follows the schema.
        """
        data = {}
        overrides = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        EnvironmentInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        factory.from_file.assert_called_once_with(schema)

        validator.is_valid.assert_has_calls(
            [
                call(data),
                call(overrides)
            ]
        )

    def test_error_if_invalid_data(self):
        """Checks that an error is thrown if the data is not valid.
        """
        data = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = False

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        with self.assertRaises(IllegibleData):
            EnvironmentInterpreter(
                data,
                schema=schema,
                validator_factory=factory
            )

    def test_get_infra_type(self):
        """Checks that it is able to extract the infrastructure type.
        """
        keys = EnvironmentInterpreter.KEYS

        infra_type = 'libvirt'

        data = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        environment = EnvironmentInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(None, environment.get_intra_type())

        data[keys.infra_type] = infra_type

        self.assertEqual(infra_type, environment.get_intra_type())

    def test_override_infra_type(self):
        """Checks that the value of the 'overrides' dictionary is chosen
        before the one from the file.
        """
        keys = EnvironmentInterpreter.KEYS

        infra_type = 'libvirt'
        override = 'ovb'

        data = {keys.infra_type: infra_type}
        overrides = {keys.infra_type: override}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        environment = EnvironmentInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        self.assertEqual(override, environment.get_intra_type())


class TestFeatureSetInterpreter(TestCase):
    """Tests for :class:`FeatureSetInterpreter`.
    """

    def test_checks_data_validity(self):
        """Verifies that the class checks that the data follows the schema.
        """
        data = {}
        overrides = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        FeatureSetInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        factory.from_file.assert_called_once_with(schema)

        validator.is_valid.assert_has_calls(
            [
                call(data),
                call(overrides)
            ]
        )

    def test_error_if_invalid_data(self):
        """Checks that an error is thrown if the data is not valid.
        """
        data = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = False

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        with self.assertRaises(IllegibleData):
            FeatureSetInterpreter(
                data,
                schema=schema,
                validator_factory=factory
            )

    def test_is_ipv6(self):
        """Checks that it is able to tell if the deployment is IPv4 or IPv6.
        """
        keys = FeatureSetInterpreter.KEYS

        data = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        featureset = FeatureSetInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertFalse(featureset.is_ipv6())

        data[keys.ipv6] = False

        self.assertFalse(featureset.is_ipv6())

        data[keys.ipv6] = True

        self.assertTrue(featureset.is_ipv6())

    def test_override_is_ipv6(self):
        """Checks that the value of the 'overrides' dictionary is chosen
        before the one from the file.
        """
        keys = FeatureSetInterpreter.KEYS

        ip_version = True
        override = False

        data = {keys.ipv6: ip_version}
        overrides = {keys.ipv6: override}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        featureset = FeatureSetInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        self.assertEqual(False, featureset.is_ipv6())

    def test_get_scenario(self):
        """Checks that it is possible to get the scenario from the
        featureset file.
        """
        scenario = 'scenario001'

        keys = FeatureSetInterpreter.KEYS

        data = {
            keys.scenario: scenario
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        featureset = FeatureSetInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(scenario, featureset.get_scenario())

    def test_overrides_get_scenario(self):
        """Checks that it is possible to override the scenario file.
        """
        scenario = 'scenario001'

        keys = FeatureSetInterpreter.KEYS

        data = {}
        overrides = {
            keys.scenario: scenario
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        featureset = FeatureSetInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        self.assertEqual(scenario, featureset.get_scenario())


class TestNodesInterpreter(TestCase):
    """Tests for :class:`NodesInterpreter`.
    """

    def test_checks_data_validity(self):
        """Verifies that the class checks that the data follows the schema.
        """
        data = {}
        overrides = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        NodesInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        factory.from_file.assert_called_once_with(schema)

        validator.is_valid.assert_has_calls(
            [
                call(data),
                call(overrides)
            ]
        )

    def test_error_if_invalid_data(self):
        """Checks that an error is thrown if the data is not valid.
        """
        data = {}

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = False

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        with self.assertRaises(IllegibleData):
            NodesInterpreter(
                data,
                schema=schema,
                validator_factory=factory
            )

    def test_get_topology(self):
        """Checks that the topology map is built from the data on the file.
        """
        keys = NodesInterpreter.KEYS

        data = {
            keys.topology: {
                'Controller': {
                    'scale': 1
                },
                'Compute': {
                    'scale': 3
                },
                'CephStorage': {
                    'scale': 2
                },
                'CellController': {
                    'scale': 1
                }
            }
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        nodes = NodesInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        result = nodes.get_topology()

        self.assertEqual(
            Topology(3, 1, 2, 1),
            result
        )

    def test_overrides_get_topology(self):
        """Checks that the topology map can be overridden.
        """
        keys = NodesInterpreter.KEYS

        data = {}
        overrides = {
            keys.topology: {
                'Controller': {
                    'scale': 1
                },
                'Compute': {
                    'scale': 3
                },
                'CephStorage': {
                    'scale': 2
                },
                'CellController': {
                    'scale': 1
                }
            }
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        nodes = NodesInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        result = nodes.get_topology()

        self.assertEqual(
            Topology(3, 1, 2, 1),
            result
        )


class TestReleaseInterpreter(TestCase):
    """Tests for :class:`ReleaseInterpreter`.
    """

    def test_get_release_name(self):
        """Checks that it is possible to get the release name from the file.
        """
        value = 'release'

        keys = ReleaseInterpreter.KEYS

        data = {
            keys.release: value
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        release = ReleaseInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(value, release.get_release_name())

    def test_overrides_get_release_name(self):
        """Checks that it is possible override the release name from the file.
        """
        value = 'release'

        keys = ReleaseInterpreter.KEYS

        data = {}
        overrides = {
            keys.release: value
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        release = ReleaseInterpreter(
            data,
            schema=schema,
            overrides=overrides,
            validator_factory=factory
        )

        self.assertEqual(value, release.get_release_name())


class TestScenarioInterpreter(TestCase):
    """Tests for :class:`ScenarioInterpreter`.
    """

    def test_get_cinder_backend(self):
        """Checks that this figures out the Cinder backend from the scenario.
        """
        keys = ScenarioInterpreter.KEYS.backends
        mapping = ScenarioInterpreter.MAPPINGS.cinder_backends

        data = {
            keys.rbd: True
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        scenario = ScenarioInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(mapping[keys.rbd], scenario.get_cinder_backend())

    def test_ignores_false_cinder_backend(self):
        """Checks that if a backend is present, but False, then it is
        ignored.
        """
        keys = ScenarioInterpreter.KEYS.backends
        mapping = ScenarioInterpreter.MAPPINGS.cinder_backends

        data = {
            keys.rbd: True,
            keys.iscsi: False
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        scenario = ScenarioInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(mapping[keys.rbd], scenario.get_cinder_backend())

    def test_default_cinder_backend(self):
        """Checks that ISCSI is chosen in case no backend is defined on the
        scenario.
        """
        keys = ScenarioInterpreter.KEYS.backends
        mapping = ScenarioInterpreter.MAPPINGS.cinder_backends

        data = {
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        scenario = ScenarioInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        self.assertEqual(mapping[keys.iscsi], scenario.get_cinder_backend())

    def test_error_if_multiple_cinder_backends(self):
        """Checks that if more than one backend is defined for Cinder,
        an error is raised.
        """
        keys = ScenarioInterpreter.KEYS.backends

        data = {
            keys.iscsi: True,
            keys.rbd: True
        }

        schema = Mock()

        validator = Mock()
        validator.is_valid = Mock()
        validator.is_valid.return_value = True

        factory = Mock()
        factory.from_file = Mock()
        factory.from_file.return_value = validator

        scenario = ScenarioInterpreter(
            data,
            schema=schema,
            validator_factory=factory
        )

        with self.assertRaises(IllegibleData):
            scenario.get_cinder_backend()
