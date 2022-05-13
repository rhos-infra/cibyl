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

from overrides import overrides

from cibyl.cli.query import QueryType
from cibyl.outputs.cli.ci.systems.common.jobs import get_plugin_section
from cibyl.outputs.cli.ci.systems.printer import CISystemPrinter
from cibyl.outputs.cli.printer import ColoredPrinter
from cibyl.utils.strings import IndentedTextBuilder
from cibyl.utils.time import as_minutes

LOG = logging.getLogger(__name__)


class ColoredBaseSystemPrinter(ColoredPrinter, CISystemPrinter):
    """Default printer for all system models. This one is decorated with
    colors for easier read.
    """

    @overrides
    def print_system(self, system):
        """
        :param system: The system.
        :type system: :class:`cibyl.models.ci.base.system.JobsSystem`
        :return: Textual representation of the provided model.
        :rtype: str
        """
        printer = IndentedTextBuilder()

        printer.add(self._palette.blue('System: '), 0)
        printer[-1].append(system.name.value)

        if self.verbosity > 0:
            printer[-1].append(f' (type: {system.system_type.value})')

        if self.query != QueryType.NONE:
            for job in system.jobs.values():
                printer.add(self.print_job(job), 1)

            if system.is_queried():
                header = 'Total jobs found in query: '

                printer.add(self._palette.blue(header), 1)
                printer[-1].append(len(system.jobs))
            else:
                printer.add(self._palette.blue('No query performed'), 1)

        return printer.build()

    def print_job(self, job):
        """
        :param job: The job.
        :type job: :class:`cibyl.models.ci.base.job.Job`
        :return: Textual representation of the provided model.
        :rtype: str
        """
        printer = IndentedTextBuilder()

        printer.add(self._palette.blue('Job: '), 0)
        printer[-1].append(job.name.value)

        if self.verbosity > 0:
            if job.url.value:
                printer.add(self._palette.blue('URL: '), 1)
                printer[-1].append(job.url.value)

        if job.builds.value:
            for build in job.builds.values():
                printer.add(self.print_build(build), 1)

        printer.add(get_plugin_section(self, job), 1)

        return printer.build()

    def print_build(self, build):
        """
        :param build: The build.
        :type build: :class:`cibyl.models.ci.base.build.Build`
        :return: Textual representation of the provided model.
        :rtype: str
        """
        printer = IndentedTextBuilder()

        printer.add(self._palette.blue('Build: '), 0)
        printer[0].append(build.build_id.value)

        if build.status.value:
            status_x_color_map = {
                'SUCCESS': lambda: self._palette.green(build.status.value),
                'FAILURE': lambda: self._palette.red(build.status.value),
                'UNSTABLE': lambda: self._palette.yellow(
                    build.status.value)
            }

            status = status_x_color_map.get(
                build.status.value,
                lambda: self._palette.underline(build.status.value)
            )()

            printer.add(self._palette.blue('Status: '), 1)
            printer[-1].append(status)

        if self.verbosity > 0:
            if build.duration.value:
                duration = as_minutes(build.duration.value)

                printer.add(self._palette.blue('Duration: '), 1)
                printer[-1].append(f'{duration:.2f}m')

        if build.tests.value:
            for test in build.tests.values():
                printer.add(self.print_test(test), 1)

        return printer.build()

    def print_test(self, test):
        """
        :param test: The test.
        :type test: :class:`cibyl.models.ci.base.test.Test`
        :return: Textual representation of the provided model.
        :rtype: str
        """
        printer = IndentedTextBuilder()

        printer.add(self._palette.blue('Test: '), 0)
        printer[-1].append(test.name.value)

        if test.result.value:
            printer.add(self._palette.blue('Result: '), 1)

            if test.result.value in ['SUCCESS', 'PASSED']:
                printer[-1].append(self._palette.green(test.result.value))
            elif test.result.value in ['FAILURE', 'FAILED', 'REGRESSION']:
                printer[-1].append(self._palette.red(test.result.value))
            elif test.result.value == "UNSTABLE":
                printer[-1].append(self._palette.yellow(test.result.value))
            elif test.result.value == "SKIPPED":
                printer[-1].append(self._palette.blue(test.result.value))

        if test.class_name.value:
            printer.add(self._palette.blue('Class name: '), 1)
            printer[-1].append(test.class_name.value)

        if self.verbosity > 0:
            if test.duration.value:
                duration = as_minutes(test.duration.value)

                printer.add(self._palette.blue('Duration: '), 1)
                printer[-1].append(f'{duration:.2f}m')

        return printer.build()
