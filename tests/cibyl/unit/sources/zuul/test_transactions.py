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
from unittest.mock import Mock

from cibyl.models.ci.zuul.test import TestKind, TestStatus
from cibyl.sources.zuul.transactions import TestResponse
from cibyl.sources.zuul.utils.tests.tempest.types import TempestTest
from cibyl.sources.zuul.utils.tests.types import Test, TestResult


class TestTestsRequest(TestCase):
    """Tests for :class:`TestsRequest`.
    """

    def test_kind(self):
        """Checks that the correct test types are returned.
        """
        generic_test = Mock(spec=Test)
        tempest_test = Mock(spec=TempestTest)

        response = TestResponse(Mock(), Mock(), generic_test)

        self.assertEqual(TestKind.UNKNOWN, response.kind)

        response = TestResponse(Mock(), Mock(), tempest_test)

        self.assertEqual(TestKind.TEMPEST, response.kind)

    def test_status(self):
        """Checks that the correct result is returned.
        """
        test = Mock()

        response = TestResponse(Mock(), Mock(), test)

        test.result = TestResult.SUCCESS

        self.assertEqual(TestStatus.SUCCESS, response.status)

        test.result = TestResult.FAILURE

        self.assertEqual(TestStatus.FAILURE, response.status)

        test.result = TestResult.SKIPPED

        self.assertEqual(TestStatus.SKIPPED, response.status)

        test.result = TestResult.UNKNOWN

        self.assertEqual(TestStatus.UNKNOWN, response.status)
