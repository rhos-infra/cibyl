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
import re
import xml.etree.ElementTree as ET
from io import StringIO

from cibyl.models.attribute import AttributeDictValue
from cibyl.models.ci.base.job import Job
from cibyl.plugins.openstack.deployment import Deployment
from cibyl.plugins.openstack.network import Network
from cibyl.plugins.openstack.node import Node
from cibyl.sources.plugins import SourceExtension
from cibyl.sources.source import speed_index

LOG = logging.getLogger(__name__)

TOPOLOGY = r'[a-zA-Z0-9:,]+:[0-9]+'  # controller:3,database:3,compute:2
NODE_NAME_COUNTER = r'[a-zA-Z]+:[0-9]+'
IP_VERSION = r'--network-protocol\s+ipv[4|6]'
IP_VERSION_NUMBER = r'4|6'


class JenkinsJobBuilder(SourceExtension):
    def _parse_xml(self, path):
        """
        Parse xml file generated by the jenkins job builder and get all
        groovy script sections found in the file.

        param: str path: the path to the xml file
        return: the StringIO instance (in memory file like instance) containing
                the groovy scripts found in the generated xml file.
        rtype: StringIO
        """
        root = ET.parse(path).getroot()
        result = ""
        for script in root.iter("script"):
            result = result + "\n" + script.text
        return StringIO(result)

    def _get_nodes(self, path, **kwargs):
        """
        extract topology from the JJB xml file and
        represent as a Nodes dictionary

        Note: this function is not used to support filtering

        :param path: to JJB xml file
        :param **kwargs: cibyl command line

        :return: dictionary of Nodes
        """
        topology = self._get_topology(path, **kwargs)
        nodes = {}
        for component in topology.split(","):
            try:
                role, amount = component.split(":")
            except ValueError:
                continue
            for i in range(int(amount)):
                node_name = role + f"-{i}"
                nodes[node_name] = Node(node_name, role=role)
        return nodes

    def _get_topology(self, path, **kwargs):
        """
        extract topology from the JJB xml file and
        represent it in the form of string, e.g
           controller:3,compute:2

        Note: this function is used to support filtering
            e.g. --topology cont, --topology controller:3
        :param path: to JJB xml file
        :param **kwargs: cibyl command line

        :return: topology string
        """
        topology_str = ""
        if "topology" in kwargs:
            in_mem_file = self._parse_xml(path)
            result = set([])

            lines = [line.rstrip() for line in in_mem_file if
                     "TOPOLOGY=" in line or "TOPOLOGY =" in line]
            for line in lines:
                topology_lst = re.findall(TOPOLOGY, line)
                for el in topology_lst:
                    nodeSet = set(re.findall(NODE_NAME_COUNTER, el))
                    result = result.union(nodeSet)

            topology_str = ",".join(sorted(result))
            # filtering support e.g. --topology cont, --topology controller:3
            if kwargs['topology'].value and len(
                    list(filter(lambda x: len(
                        [el for el in kwargs['topology'].value
                         if el in x]) > 0,
                                result))) == 0:
                return None

        return topology_str

    def _get_ip_version(self, path, **kwargs):
        """
        extract ip_version from the JJB xml file and
        represent it in the form of string, e.g
           4 or 6

        Note: this function is used to support filtering
            e.g. --ip_version 4
        :param path: to JJB xml file
        :param **kwargs: cibyl command line

        :return: ip version string
        """
        ip_version_str = ""
        if "ip_version" in kwargs:
            in_mem_file = self._parse_xml(path)
            result = set([])

            lines = [line.rstrip() for line in in_mem_file if
                     "--network-protocol" in line]
            for line in lines:
                ip_version_lst = re.findall(IP_VERSION, line)
                for el in ip_version_lst:
                    nodeSet = set(re.findall(IP_VERSION_NUMBER, el))
                    result = result.union(nodeSet)
            ip_version_str = ",".join(result)
            # filtering support e.g. --ip-version 4
            if kwargs['ip_version'].value and len(
                    list(filter(lambda x: len(
                        [el for el in str(kwargs['ip_version'].value) if
                         el in x]) > 0,
                                result))) == 0:
                return None
        return ip_version_str

    @speed_index({'base': 3, 'cinder_backend': 1})
    def get_deployment(self, **kwargs):
        """
        extract different aspects of deployment information
        for jobs dictionary generated by calling to  self.get_jobs_from_repo

        some aspects (e.g. topology) facilitate additional filtering
        of the jobs.

        :param **kwargs: cibyl command line

        :return: AttributeDictValue of the resulting (possibly filtered) job
                 list along with the deployment information.
        """
        filterted_out = []
        jobs = {}
        for repo in self.repos:
            # filter according to jobs parameter if specified by kwargs
            jobs.update(
                self.get_jobs_from_repo(repo, **kwargs))

        for job_name in jobs:
            path = self._xml_files[job_name]

            topology = self._get_topology(path, **kwargs)

            # compute what is filtered out according to topology filter
            if topology is None and kwargs['topology'].value is not None:
                filterted_out += [job_name]
                continue

            ipv = self._get_ip_version(path, **kwargs)

            # compute what is filtered out according to ip version filter
            if ipv is None and kwargs['ip_version'].value is not None:
                filterted_out += [job_name]
                continue

            network = Network(ip_version=ipv,
                              ml2_driver="",
                              network_backend="",
                              dvr="",
                              tls_everywhere="",
                              security_group="")

            deployment = Deployment("",
                                    "",
                                    nodes=self._get_nodes(path, **kwargs),
                                    services={},
                                    topology=topology,
                                    network=network,
                                    storage="",
                                    ironic="",
                                    test_collection="",
                                    overcloud_templates="",
                                    stages="")

            jobs[job_name].add_deployment(deployment)

        # filter out jobs
        for el in filterted_out:
            del jobs[el]

        return AttributeDictValue("jobs", attr_type=Job, value=jobs)
