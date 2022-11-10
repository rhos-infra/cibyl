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
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase

from cibyl.sources.zuuld.tools.yaml import YAMLSearch, ZuulDFile
from kernel.tools.fs import Dir, File
from kernel.tools.yaml import YAMLError


class TestZuulDFile(TestCase):
    """Tests for :class:`ZuulDFile.`
    """

    def test_error_if_unmet_schema(self):
        """Checks that an error is thrown if the file does not meet the
        schema.
        """
        contents = 'hello_world!'

        with NamedTemporaryFile('w') as file:
            file.write(contents)
            file.flush()

            with self.assertRaises(YAMLError):
                ZuulDFile(file=File(file))


class TestYAMLSearch(TestCase):
    """Tests for :class:`YAMLSearch`.
    """

    def test_finds_files(self):
        """Checks that the class is able to find the desired files.
        """
        contents = \
            '''
            - job:
                name: test
            '''

        with TemporaryDirectory() as folder:
            directory = Dir(folder)

            subdirectory = directory.cd('subdir')
            subdirectory.mkdir()

            file1 = NamedTemporaryFile('w', suffix='.yaml', dir=directory)
            file1.write(contents)
            file1.flush()

            file2 = NamedTemporaryFile('w', suffix='.yml', dir=subdirectory)
            file2.write(contents)
            file2.flush()

            search = YAMLSearch()

            result = list(search.search(directory))

            self.assertEqual(2, len(result))
            self.assertTrue(result[0].file.endswith('.yaml'))
            self.assertTrue(result[1].file.endswith('.yml'))
