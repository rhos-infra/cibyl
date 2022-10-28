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

from kernel.git.apis.cli import GitError
from kernel.tools.urls import URL
from tripleo.insights import DeploymentLookUp, DeploymentOutline


class TestOpenDev(TestCase):
    """Verifies that the library is capable of working with repositories
    hosted on OpenDev.
    """

    def test_no_error_on_clone(self):
        """Checks that the library does not crash when trying to clone an
        OpenDev repository.
        """
        url = URL('https://opendev.org/openstack/tripleo-quickstart.git')
        outline = DeploymentOutline(quickstart=url)

        lookup = DeploymentLookUp()

        try:
            lookup.run(outline)
        except GitError as ex:
            self.fail(f"Test threw an unwanted error: '{type(ex).__name__}'.")
