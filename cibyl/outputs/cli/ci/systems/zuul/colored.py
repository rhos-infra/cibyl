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
from cibyl.outputs.cli.ci.systems.base.colored import ColoredBaseSystemPrinter
from cibyl.outputs.cli.ci.systems.common.builds import (get_duration_section,
                                                        get_status_section)
from cibyl.outputs.cli.ci.systems.common.jobs import (get_plugin_section,
                                                      has_plugin_section)
from cibyl.outputs.cli.printer import ColoredPrinter
from cibyl.utils.strings import IndentedTextBuilder

LOG = logging.getLogger(__name__)


class ColoredZuulSystemPrinter(ColoredBaseSystemPrinter):
    class ProjectCascade(ColoredPrinter):
        def print_project(self, project):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Project: '), 0)
            result[-1].append(project.name)

            if self.verbosity > 0:
                result.add(self._palette.blue('URL: '), 1)
                result[-1].append(project.url)

            if self.query >= QueryType.PIPELINES:
                for pipeline in project.pipelines.values():
                    result.add(self._print_pipeline(project, pipeline), 1)

                result.add(
                    self._palette.blue(
                        "Total pipelines found in query for project '"
                    ), 1
                )

                result[-1].append(self._palette.underline(project.name))
                result[-1].append(self._palette.blue("': "))
                result[-1].append(len(project.pipelines))

            return result.build()

        def _print_pipeline(self, project, pipeline):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Pipeline: '), 0)
            result[-1].append(pipeline.name)

            if self.query >= QueryType.JOBS:
                for job in pipeline.jobs.values():
                    result.add(self._print_job(project, pipeline, job), 1)

                result.add(
                    self._palette.blue(
                        "Total jobs found in query for pipeline '"
                    ), 1
                )

                result[-1].append(self._palette.underline(pipeline.name))
                result[-1].append(self._palette.blue(': '))
                result[-1].append(len(pipeline.jobs))

            return result.build()

        def _print_job(self, project, pipeline, job):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Job: '), 0)
            result[-1].append(job.name.value)

            if self.query >= QueryType.BUILDS:
                for build in job.builds.values():
                    # This cascade only wants builds of this project
                    if build.project.value != project.name.value:
                        continue

                    # This cascade only wants builds triggered by this pipeline
                    if build.pipeline.value != pipeline.name.value:
                        continue

                    result.add(
                        self._print_build(project, pipeline, job, build), 1
                    )

            return result.build()

        def _print_build(self, project, pipeline, job, build):
            # Unused, but left for future use
            del project, pipeline, job

            result = IndentedTextBuilder()

            result.add(self._palette.blue('Build: '), 1)
            result[-1].append(build.build_id.value)

            if build.status.value:
                result.add(get_status_section(self.palette, build), 2)

            return result.build()

    class JobCascade(ColoredPrinter):
        def print_job(self, job):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Job: '), 0)
            result[-1].append(job.name.value)

            if self.verbosity > 0:
                if job.url.value:
                    result.add(self._palette.blue('URL: '), 1)
                    result[-1].append(job.url.value)

            if job.variants.value:
                result.add(self._palette.blue('Variants: '), 1)

                for variant in job.variants:
                    result.add(self._print_variant(variant), 2)

            if job.builds.value:
                result.add(self._palette.blue('Builds: '), 1)

                for build in job.builds.values():
                    result.add(self._print_build(build), 2)

            if has_plugin_section(job):
                result.add(get_plugin_section(self, job), 1)

            return result.build()

        def _print_variant(self, variant):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Variant: '), 0)

            result.add(self._palette.blue('Description: '), 1)
            result[-1].append(variant.description)

            result.add(self._palette.blue('Parent: '), 1)
            result[-1].append(variant.parent)

            result.add(self._palette.blue('Branches: '), 1)
            for branch in variant.branches:
                result.add('- ', 2)
                result[-1].append(branch)

            result.add(self._palette.blue('Variables: '), 1)
            for key, value in variant.variables.items():
                result.add(self._palette.blue(f'{key}: '), 2)
                result[-1].append(value)

            return result.build()

        def _print_build(self, build):
            result = IndentedTextBuilder()

            result.add(self._palette.blue('Build: '), 0)
            result[0].append(build.build_id.value)

            if build.project.value:
                result.add(self._palette.blue('Project: '), 1)
                result[-1].append(build.project.value)

            if build.pipeline.value:
                result.add(self._palette.blue('Pipeline: '), 1)
                result[-1].append(build.pipeline.value)

            if build.status.value:
                result.add(get_status_section(self.palette, build), 1)

            if self.verbosity > 0:
                if build.duration.value:
                    result.add(get_duration_section(self.palette, build), 1)

            return result.build()

    @overrides
    def print_system(self, system):
        printer = IndentedTextBuilder()

        # Begin with the text common to all systems
        printer.add(super().print_system(system), 0)

        # Continue with text specific for this system type
        if self.query >= QueryType.TENANTS:
            if hasattr(system, 'tenants'):
                for tenant in system.tenants.values():
                    printer.add(self._print_tenant(tenant), 1)

                if system.is_queried():
                    header = 'Total tenants found in query: '

                    printer.add(self._palette.blue(header), 1)
                    printer[-1].append(len(system.tenants))
                else:
                    printer.add(self._palette.blue('No query performed.'), 1)
            else:
                LOG.warning(
                    'Requested tenant printing on a non-zuul interface. '
                    'Ignoring...'
                )

        return printer.build()

    def _print_tenant(self, tenant):
        """
        :param tenant: The tenant.
        :type tenant: :class:`cibyl.models.ci.zuul.tenant.Tenant`
        :return: Textual representation of the provided model.
        :rtype: str
        """

        def print_projects():
            def create_printer():
                return ColoredZuulSystemPrinter.ProjectCascade(
                    self.query, self.verbosity, self.palette
                )

            # Avoid header if there are no project
            if tenant.projects.value:
                result.add(self._palette.blue('Projects: '), 1)

                for project in tenant.projects.values():
                    result.add(create_printer().print_project(project), 2)

            result.add(
                self._palette.blue(
                    "Total projects found in query for tenant '"
                ), 1
            )
            result[-1].append(self._palette.underline(tenant.name))
            result[-1].append(self._palette.blue("': "))
            result[-1].append(len(tenant.projects))

        def print_jobs():
            def create_printer():
                return ColoredZuulSystemPrinter.JobCascade(
                    self.query, self.verbosity, self.palette
                )

            # Avoid header if there are no jobs
            if tenant.jobs.value:
                result.add(self._palette.blue('Jobs: '), 1)

                for job in tenant.jobs.values():
                    result.add(create_printer().print_job(job), 2)

            result.add(
                self._palette.blue(
                    "Total jobs found in query for tenant '"
                ), 1
            )

            result[-1].append(self._palette.underline(tenant.name))
            result[-1].append(self._palette.blue("': "))
            result[-1].append(len(tenant.jobs))

        result = IndentedTextBuilder()

        result.add(self._palette.blue('Tenant: '), 0)
        result[-1].append(tenant.name)

        if self.query >= QueryType.PROJECTS:
            print_projects()

            if self.query >= QueryType.JOBS:
                print_jobs()

        return result.build()
