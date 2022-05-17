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
import os
import re
from functools import partial
from typing import Dict

import yaml

from cibyl.cli.argument import Argument
from cibyl.exceptions.jenkins import JenkinsError
from cibyl.models.attribute import AttributeDictValue
from cibyl.models.ci.base.job import Job
from cibyl.plugins.openstack.container import Container
from cibyl.plugins.openstack.deployment import Deployment
from cibyl.plugins.openstack.node import Node
from cibyl.plugins.openstack.package import Package
from cibyl.plugins.openstack.service import Service
from cibyl.plugins.openstack.utils import translate_topology_string
from cibyl.sources.jenkins import detect_job_info_regex, filter_jobs
from cibyl.sources.source import speed_index
from cibyl.utils.dicts import subset
from cibyl.utils.filtering import (DEPLOYMENT_PATTERN, DVR_PATTERN_NAME,
                                   IP_PATTERN, NETWORK_BACKEND_PATTERN,
                                   RELEASE_PATTERN, SERVICES_PATTERN,
                                   STORAGE_BACKEND_PATTERN, TOPOLOGY_PATTERN,
                                   apply_filters, filter_topology,
                                   satisfy_exact_match)

LOG = logging.getLogger(__name__)


def filter_models_by_name(job: dict, user_input: Argument,
                          field_to_check: str):
    """Check whether job should be included according to the user input. The
    model should be added if the models provided in the field designated by the
    variable field_to_check are present in the user_input values.

    :param job: job information obtained from jenkins
    :type job: str
    :param user_input: input argument specified by the user
    :type model_urls: :class:`.Argument`
    :param field_to_check: Job field to perform the check
    :param field_to_check: str
    :returns: Whether the model satisfies user input
    :rtype: bool
    """
    job[field_to_check] = subset(job[field_to_check], user_input.value)
    # if the subset is empty, job should be filtered
    return bool(job[field_to_check])


def should_query_for_nodes_topology(**kwargs):
    """Check the user cli arguments to ascertain whether we should query for
    nodes and the topology value of a deployment.
    :returns: Whether we should query for nodes and topology
    :rtype: bool, bool
    """
    spec = "spec" in kwargs
    query_nodes = "nodes" in kwargs or "controllers" in kwargs
    query_nodes |= "computes" in kwargs
    query_nodes |= "packages" in kwargs or "containers" in kwargs
    # query_topology stores whether there is any argument that will require
    # the topology to be queried, which might be the topology itself, or
    # any information about the nodes, containers or packages or the spec
    # argument
    query_topology = "topology" in kwargs or spec or query_nodes
    return query_nodes, query_topology


def filter_nodes(job: dict, user_input: Argument, field_to_check: str):
    """Check whether job should be included according to the user input. The
    model should be added if the node models provided in the field designated
    by the variable field_to_check are present in the user_input values.

    :param job: job information obtained from jenkins
    :type job: str
    :param user_input: input argument specified by the user
    :type model_urls: :class:`.Argument`
    :param field_to_check: Job field to perform the check
    :param field_to_check: str
    :returns: Whether the model satisfies user input
    :rtype: bool
    """
    valid_nodes = 0
    for node in job['nodes'].values():
        attr = getattr(node, field_to_check)
        attr.value = subset(attr.value, user_input.value)
        valid_nodes += len(attr)
    # if the subset is empty, job should be filtered
    return valid_nodes > 0


class Jenkins:
    """A class representation of Jenkins client."""

    deployment_attr = ["topology", "release",
                       "network_backend", "storage_backend",
                       "infra_type", "dvr", "ip_version",
                       "tls_everywhere", "ml2_driver"]

    def add_job_info_from_name(self, job:  Dict[str, str], **kwargs):
        """Add information to the job by using regex on the job name. Check if
        properties exist before adding them in case it's used as fallback when
        artifacts do not contain all the necessary information.

        :param job: Dictionary representation of a jenkins job
        :type job: dict
        :param spec: Whether to provide full spec information
        :type spec: bool
        """
        spec = "spec" in kwargs
        job_name = job['name']
        _, query_topology = should_query_for_nodes_topology(**kwargs)
        missing_topology = "topology" not in job or not job["topology"]
        if missing_topology and query_topology:
            self.get_topology_from_job_name(job)

        missing_release = "release" not in job or not job["release"]
        if missing_release and ("release" in kwargs or spec):
            job["release"] = detect_job_info_regex(job_name,
                                                   RELEASE_PATTERN)

        missing_infra_type = "infra_type" not in job or not job["infra_type"]
        if missing_infra_type and ("infra_type" in kwargs or spec):
            infra_type = detect_job_info_regex(job_name,
                                               DEPLOYMENT_PATTERN)
            if not infra_type and "virt" in job_name:
                infra_type = "virt"
            job["infra_type"] = infra_type

        missing_network_backend = not bool(job.get("network_backend", ""))
        if missing_network_backend and ("network_backend" in kwargs or spec):
            network_backend = detect_job_info_regex(job_name,
                                                    NETWORK_BACKEND_PATTERN)
            job["network_backend"] = network_backend

        missing_storage_backend = not bool(job.get("storage_backend", ""))
        if missing_storage_backend and ("storage_backend" in kwargs or spec):
            storage_backend = detect_job_info_regex(job_name,
                                                    STORAGE_BACKEND_PATTERN)
            job["storage_backend"] = storage_backend

        missing_ip_version = "ip_version" not in job or not job["ip_version"]
        if missing_ip_version and ("ip_version" in kwargs or spec):
            job["ip_version"] = detect_job_info_regex(job_name, IP_PATTERN,
                                                      group_index=1,
                                                      default="unknown")
        missing_dvr = "dvr" not in job or not job["dvr"]
        if missing_dvr and ("dvr" in kwargs or spec):
            dvr = detect_job_info_regex(job_name, DVR_PATTERN_NAME)
            job["dvr"] = ""
            if dvr:
                job["dvr"] = str(dvr == "dvr")

        missing_tls_everywhere = not bool(job.get("tls_everywhere", ""))
        if missing_tls_everywhere and ("tls_everywhere" in kwargs or spec):
            # some jobs have TLS in their name as upper case
            job["tls_everywhere"] = ""
            if "tls" in job_name.lower():
                job["tls_everywhere"] = "True"

    def job_missing_deployment_info(self, job: Dict[str, str]):
        """Check if a given Jenkins job has all deployment attributes.

        :param job: Dictionary representation of a jenkins job
        :type job: dict
        :returns: Whether all deployment attributes are found in the job
        :rtype bool:
        """
        for attr in self.deployment_attr:
            if attr not in job or not job[attr]:
                return True
        return False

    @speed_index({'base': 2})
    def get_deployment(self, **kwargs):
        """Get deployment information for jobs from jenkins server.

        :returns: container of jobs with deployment information from
        jenkins server
        :rtype: :class:`AttributeDictValue`
        """
        jobs_found = self.send_request(self.jobs_query_for_deployment)["jobs"]

        spec = "spec" in kwargs

        jobs_found = filter_jobs(jobs_found, **kwargs)

        use_artifacts = True
        if spec:
            spec_value = kwargs["spec"].value
            jobs_args = kwargs.get("jobs")
            # if user called cibyl just with --spec without value and no --jobs
            # argument, we have not enough information to pull the spec
            spec_missing_input = not bool(spec_value) and (jobs_args is None)
            if len(jobs_found) == 0 or spec_missing_input:
                msg = "No job was found, please pass --spec job-name with an "
                msg += " exact match or --jobs job-name with a valid job name "
                msg += "or pattern."
                raise JenkinsError(msg)

            if len(jobs_found) > 1:
                raise JenkinsError("Full Openstack specification can be shown "
                                   "only for one job, please restrict the "
                                   "query.")
        if len(jobs_found) > 12:
            LOG.warning("Requesting deployment information for %d jobs \
will be based on the job name and approximate, restrict the query for more \
accurate results", len(jobs_found))
            use_artifacts = False

        job_deployment_info = []
        for job in jobs_found:
            last_build = job.get("lastCompletedBuild")
            if spec:
                if last_build is None:
                    # jenkins only has a logs link for completed builds
                    raise JenkinsError("Openstack specification requested for"
                                       f" job {job['name']} but job has no "
                                       "completed build.")
                else:
                    self.add_job_info_from_artifacts(job, **kwargs)
            elif use_artifacts and last_build is not None:
                # if we have a lastBuild, we will have artifacts to pull
                self.add_job_info_from_artifacts(job, **kwargs)
            else:
                self.add_job_info_from_name(job, **kwargs)
            job_deployment_info.append(job)

        checks_to_apply = []
        for attribute in self.deployment_attr:
            # check for user provided that should have an exact match
            input_attr = kwargs.get(attribute)
            if input_attr and input_attr.value:
                checks_to_apply.append(partial(satisfy_exact_match,
                                       user_input=input_attr,
                                       field_to_check=attribute))

        input_controllers = kwargs.get('controllers')
        if input_controllers and input_controllers.value:
            for range_arg in input_controllers.value:
                operator, value = range_arg
                checks_to_apply.append(partial(filter_topology,
                                       operator=operator,
                                       value=value,
                                       component='controller'))

        input_computes = kwargs.get('computes')
        if input_computes and input_computes.value:
            for range_arg in input_computes.value:
                operator, value = range_arg
                checks_to_apply.append(partial(filter_topology,
                                       operator=operator,
                                       value=value,
                                       component='compute'))

        input_services = kwargs.get('services')
        if input_services and input_services.value:
            checks_to_apply.append(partial(filter_models_by_name,
                                           field_to_check='services',
                                           user_input=input_services))

        for attribute in ['containers', 'packages']:
            input_attr = kwargs.get(attribute)
            if input_attr and input_attr.value:
                checks_to_apply.append(partial(filter_nodes,
                                       user_input=input_attr,
                                       field_to_check=attribute))

        job_deployment_info = apply_filters(job_deployment_info,
                                            *checks_to_apply)

        job_objects = {}
        for job in job_deployment_info:
            name = job.get('name')
            job_objects[name] = Job(name=name, url=job.get('url'))
            topology = job.get("topology", "")
            if not job.get("nodes") and topology:
                job["nodes"] = {}
                for component in topology.split(","):
                    role, amount = component.split(":")
                    for i in range(int(amount)):
                        node_name = role+f"-{i}"
                        job["nodes"][node_name] = Node(node_name, role=role)
            network_backend = job.get("network_backend", "")
            storage_backend = job.get("storage_backend", "")
            tls_everywhere = job.get("tls_everywhere", "")
            deployment = Deployment(job.get("release", ""),
                                    job.get("infra_type", ""),
                                    nodes=job.get("nodes", {}),
                                    services=job.get("services", {}),
                                    ip_version=job.get("ip_version", ""),
                                    ml2_driver=job.get("ml2_driver", ""),
                                    topology=topology,
                                    network_backend=network_backend,
                                    storage_backend=storage_backend,
                                    dvr=job.get("dvr", ""),
                                    tls_everywhere=tls_everywhere)
            job_objects[name].add_deployment(deployment)

        return AttributeDictValue("jobs", attr_type=Job, value=job_objects)

    def add_job_info_from_artifacts(self, job: dict, **kwargs):
        """Add information to the job by querying the last build artifacts.

        :param job: Dictionary representation of a jenkins job
        :type job: dict
        """
        spec = "spec" in kwargs
        query_nodes, query_topology = should_query_for_nodes_topology(**kwargs)
        job_name = job['name']
        build_description = job["lastCompletedBuild"].get("description")
        if not build_description:
            LOG.debug("Resorting to get deployment information from job name"
                      " for job %s", job_name)
            self.add_job_info_from_name(job, **kwargs)
            return
        logs_url_pattern = re.compile(r'href="(.*)">Browse logs')
        logs_url = logs_url_pattern.search(build_description)
        if logs_url is None:
            LOG.debug("Resorting to get deployment information from job name"
                      " for job %s", job_name)
            self.add_job_info_from_name(job, **kwargs)
            return
        logs_url = logs_url.group(1)

        if query_topology:
            artifact_path = "infrared/provision.yml"
            artifact_url = f"{logs_url.rstrip('/')}/{artifact_path}"
            try:
                artifact = self.send_request(item="", query="",
                                             url=artifact_url,
                                             raw_response=True)
                artifact = yaml.safe_load(artifact)
                provision = artifact.get('provision', {})
                nodes = provision.get('topology', {}).get('nodes', {})
                topology = []
                for node_path, amount in nodes.items():
                    node = os.path.split(node_path)[1]
                    node = os.path.splitext(node)[0]
                    topology.append(f"{node}:{amount}")
                job["topology"] = ",".join(topology)

            except JenkinsError:
                LOG.debug("Found no artifact %s for job %s", artifact_path,
                          job_name)

        artifact_path = "infrared/overcloud-install.yml"
        artifact_url = f"{logs_url.rstrip('/')}/{artifact_path}"
        try:
            artifact = self.send_request(item="", query="",
                                         url=artifact_url,
                                         raw_response=True)
            artifact = yaml.safe_load(artifact)
            overcloud = artifact.get('install', {})
            if "release" in kwargs or spec:
                job["release"] = overcloud.get("version", "")
            deployment = overcloud.get('deployment', {})
            if "infra_type" in kwargs or spec:
                infra = os.path.split(deployment.get('files', ""))[1]
                job["infra_type"] = infra
            storage = overcloud.get("storage", {})
            if "storage_backend" in kwargs or spec:
                job["storage_backend"] = storage.get("backend", "")
            network = overcloud.get("network", {})
            if "network_backend" in kwargs or spec:
                job["network_backend"] = network.get("backend", "")
            ip_string = network.get("protocol", "")
            if "network_backend" in kwargs or spec:
                job["ip_version"] = detect_job_info_regex(ip_string,
                                                          IP_PATTERN,
                                                          group_index=1,
                                                          default="unknown")
            if "dvr" in kwargs or spec:
                job["dvr"] = str(network.get("dvr", ""))
            if "tls_everywhere" in kwargs or spec:
                tls = overcloud.get("tls", {})
                job["tls_everywhere"] = str(tls.get("everywhere", ""))
            if "ml2_driver" in kwargs or spec:
                job["ml2_driver"] = "ovn"
                if network.get("ovs"):
                    job["ml2_driver"] = "ovs"

        except JenkinsError:
            LOG.debug("Found no artifact %s for job %s", artifact_path,
                      job_name)
        if query_topology:
            if not job.get("topology", ""):
                self.get_topology_from_job_name(job)
            topology = job["topology"]
            if query_nodes:
                job["nodes"] = {}
                if topology:
                    for component in topology.split(","):
                        role, amount = component.split(":")
                        for i in range(int(amount)):
                            node_name = role+f"-{i}"
                            container = {}
                            packages = {}
                            if "packages" in kwargs and not spec:
                                packages = self.get_packages_node(node_name,
                                                                  logs_url,
                                                                  job_name)
                            if "containers" in kwargs and not spec:
                                container = self.get_containers_node(node_name,
                                                                     logs_url,
                                                                     job_name)
                            node = Node(node_name, role=role,
                                        containers=container,
                                        packages=packages)
                            job["nodes"][node_name] = node

        artifact_path = "undercloud-0/var/log/extra/services.txt.gz"
        artifact_url = f"{logs_url.rstrip('/')}/{artifact_path}"
        job["services"] = {}
        if "services" in kwargs and not spec:
            try:
                artifact = self.send_request(item="", query="",
                                             url=artifact_url,
                                             raw_response=True)
                for service in SERVICES_PATTERN.findall(artifact):
                    job["services"][service] = Service(service)

            except JenkinsError:
                LOG.debug("Found no artifact %s for job %s", artifact_path,
                          job_name)

        if self.job_missing_deployment_info(job):
            LOG.debug("Resorting to get deployment information from job name"
                      " for job %s", job_name)
            self.add_job_info_from_name(job, **kwargs)
            release = job.get("release")
            query_ml2_driver = (spec or "ml2_driver" in kwargs)
            if query_ml2_driver and release and not job.get("ml2_driver"):
                # ovn is the default starting from OSP 15.0
                if float(release) > 15.0:
                    job["ml2_driver"] = "ovn"
                else:
                    job["ml2_driver"] = "ovs"
                LOG.warning("Some logs are missing for job %s, information "
                            "will be retrieved from the job name, but will "
                            "be incomplete", job_name)
                self.add_unable_to_find_info_message(job)

    def get_packages_node(self, node_name, logs_url, job_name):
        """Get a list of packages installed in a openstack node from the job
        logs.

        :params node_name: Name of the node to inspect
        :type node_name: str
        :params logs_url: Url of the job's logs
        :type logs_url: str
        :params job_name: Name of the job to inspect
        :type job_name: str

        :returns: Packages found in the node
        :rtype: dict
        """
        artifact_path = "var/log/extra/rpm-list.txt.gz"
        artifact_url = f"{logs_url.rstrip('/')}/{node_name}/{artifact_path}"
        packages = {}
        try:
            artifact = self.send_request(item="", query="",
                                         url=artifact_url,
                                         raw_response=True)
            package_list = artifact.rstrip().split("\n")
            for package in package_list:
                packages[package] = Package(package)

        except JenkinsError:
            LOG.debug("Found no artifact %s for job %s", artifact_path,
                      job_name)
        return packages

    def get_packages_container(self, container_name, logs_url, job_name):
        """Get a list of packages installed in a container from the job
        logs.

        :params container_name: Name of the container to inspect
        :type node_name: str
        :params logs_url: Url of the job's logs
        :type logs_url: str
        :params job_name: Name of the job to inspect
        :type job_name: str

        :returns: Packages found in the container
        :rtype: dict
        """
        artifact_path = f"{container_name}/log/dnf.rpm.log.gz"
        artifact_url = f"{logs_url.rstrip('/')}/{artifact_path}"
        packages = {}
        package_pattern = re.compile(r"SUBDEBUG .*: (.*)")
        try:
            artifact = self.send_request(item="", query="",
                                         url=artifact_url,
                                         raw_response=True)
            for package in package_pattern.findall(artifact):
                packages[package] = Package(package)

        except JenkinsError:
            LOG.debug("Found no artifact %s for job %s", artifact_path,
                      job_name)
        return packages

    def get_containers_node(self, node_name, logs_url, job_name):
        """Get a list of containers used in a openstack node from the job
        logs.

        :params node_name: Name of the node to inspect
        :type node_name: str
        :params logs_url: Url of the job's logs
        :type logs_url: str
        :params job_name: Name of the job to inspect
        :type job_name: str

        :returns: Packages found in the node
        :rtype: dict
        """
        artifact_path = "var/log/extra/podman/containers"
        artifact_url = f"{logs_url}/{node_name}/{artifact_path}"
        containers = {}
        try:
            artifact = self.send_request(item="", query="",
                                         url=artifact_url,
                                         raw_response=True)
            names_pattern = re.compile(r'<a href=\"([\w+/\.]*)\">([\w/]*)</a>')
            for folder in names_pattern.findall(artifact):
                # the page listing the containers has many links, most of them
                # point to folders with container information, which have the
                # same text in the link and the displayed text
                if folder[1] not in folder[0]:
                    continue
                container_name = folder[1].rstrip("/")
                packages = self.get_packages_container(container_name,
                                                       artifact_url,
                                                       job_name)
                containers[container_name] = Container(container_name,
                                                       packages=packages)

        except JenkinsError:
            LOG.debug("Found no artifact %s for job %s", artifact_path,
                      job_name)
        return containers

    def get_topology_from_job_name(self, job: Dict[str, str]):
        """Extract the openstack topology from the job name.

        :param job: Dictionary representation of a jenkins job
        :type job: dict
        """
        job_name = job["name"]
        short_topology = detect_job_info_regex(job_name,
                                               TOPOLOGY_PATTERN)
        if short_topology:
            # due to the regex used, short_topology may contain a trailing
            # underscore that should be removed
            short_topology = short_topology.rstrip("_")
            job["topology"] = translate_topology_string(short_topology)
        else:
            job["topology"] = ""

    def add_unable_to_find_info_message(self, job):
        """Set a message explaining the reason for missing fields in spec.

        :param job: Dictionary representation of a jenkins job
        :type job: dict
        """
        message = "Unable to find information"
        for attr in self.deployment_attr:
            if not job.get(attr):
                job[attr] = message
