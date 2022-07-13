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
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Sequence

from overrides import overrides

from tripleo.insights.exceptions import DownloadError, InvalidURL
from tripleo.utils.fs import Dir
from tripleo.utils.git import Git
from tripleo.utils.git import Repository as GitRepo
from tripleo.utils.git.gitpython import GitPython
from tripleo.utils.git.utils import get_repository_fullname
from tripleo.utils.github import GitHub
from tripleo.utils.github import Repository as GitHubRepo
from tripleo.utils.github.pygithub import PyGitHub
from tripleo.utils.paths import resolve_home
from tripleo.utils.urls import URL, is_git, is_github
from tripleo.utils.yaml import YAML, StandardYAMLParser, YAMLError, YAMLParser

LOG = logging.getLogger(__name__)


class GitDownloader(ABC):
    """Utility that makes it easy to access files on a Git repository.

    This will handle all the boilerplate needed to get to a file
    on a Git repository so that the user can leave all of that out and
    concentrate on what they need.
    """

    def __init__(self, repository: URL, branch: Optional[str] = None):
        """Constructor.

        :param repository: URL to the Git repository.
        :param branch: Name of the branch to download from. 'None' to use the
            repo's default branch.
        """
        self._repository = repository
        self._branch = branch

    @property
    def repository(self) -> URL:
        """
        :return: URL to the Git repository.
        """
        return self._repository

    @property
    def branch(self) -> Optional[str]:
        """
        :return: Name of the branch to download from. 'None' to use the
            repo's default branch.
        """
        return self._branch

    @abstractmethod
    def download_as_text(self, file: str) -> str:
        """

        :param file: Relative path to the repository's root pointing to the
            file to be downloaded.
        :return: Contents of that file.
        :raises DownloadError: If the file could not be downloaded.
        """
        raise NotImplementedError


class GitCLIDownloader(GitDownloader):
    """Implements the 'GitDownloader' interface through the use of the Git CLI.

    Have in mind that this will need to clone the Git repository and, thus,
    will affect the filesystem.
    """

    def __init__(
        self,
        repository: URL,
        working_dir: Dir,
        branch: Optional[str] = None,
        api: Git = GitPython()
    ):
        """Constructor. See parent for more information.

        :param working_dir: Directory where the repository will get cloned in.
        :param api: API used to interact with the Git CLI.
        """
        super().__init__(repository, branch)

        self._api = api
        self._working_dir = working_dir

    @property
    def api(self) -> Git:
        """
        :return: API used to interact with the Git CLI.
        """
        return self._api

    @property
    def working_dir(self) -> Dir:
        """
        :return: Directory where the repository will get cloned in.
        """
        return self._working_dir

    @overrides
    def download_as_text(self, file: str) -> str:
        repo = self._get_repo()

        if self.branch:
            repo.checkout(self.branch)

        return repo.get_as_text(file)

    def _get_repo(self) -> GitRepo:
        # Check if working directory is ready
        if not self.working_dir.exists():
            self.working_dir.mkdir(recursive=True)

        # Check if the repository is present on the filesystem
        if self.working_dir.is_empty():
            # Download it then
            return self.api.clone(self.repository, self.working_dir)

        # Being it already here, let's try to reuse it
        return self.api.open(self.working_dir)


class GitHubDownloader(GitDownloader):
    """Implements the 'GitDownloader' interface through the use of the GitHub
    API.
    """

    def __init__(
        self,
        repository: URL,
        branch: Optional[str] = None,
        api: GitHub = PyGitHub.from_no_login()
    ):
        """Constructor. See parent for more information.

        :param api: API to interact with GitHub.
        """
        super().__init__(repository, branch)

        self._api = api

    @property
    def api(self) -> GitHub:
        """
        :return: API to interact with GitHub.
        """
        return self._api

    @overrides
    def download_as_text(self, file: str) -> str:
        repo = self._get_repository()

        if self.branch:
            repo.checkout(self.branch)

        return repo.download_as_text(file)

    def _get_repository(self) -> GitHubRepo:
        def get_repository_owner():
            return get_repository_fullname(self.repository).split('/')[0]

        def get_repository_name():
            return get_repository_fullname(self.repository).split('/')[1]

        return self.api.get_repository(
            get_repository_owner(),
            get_repository_name()
        )


class GitDownloaderFetcher:
    """Tool used to find the downloaders that are compatible with a certain
    URL.
    """
    DEFAULT_CLONE_PATH = Dir('~/.cibyl', resolve_home)
    """Default directory where Git repositories are cloned to if needed."""

    def __init__(self, clone_path: Dir = DEFAULT_CLONE_PATH):
        """
        :param clone_path: Directory where Git repositories are cloned in if
            required.
        """
        self._clone_path = clone_path

    @property
    def clone_path(self) -> Dir:
        """
        :return: Directory where Git repositories are cloned in if required.
        """
        return self._clone_path

    def get_downloaders_for(
        self,
        url: URL,
        branch: Optional[str] = None
    ) -> Sequence[GitHubDownloader]:
        """
        :param url: URL to test.
        :param branch: Name of the branch to download from. 'None' to use the
            repo's default branch.
        :return: List of downloaders that can provide support
            for the tested URL, ordered from most preferred to least.
            Can also be empty.
        """
        result = []

        if is_git(url):
            if is_github(url):
                result.append(self._get_new_github_downloader(url, branch))

            result.append(self._get_new_cli_downloader(url, branch))

        return result

    def _get_new_cli_downloader(
        self,
        url: URL,
        branch: Optional[str]
    ) -> GitCLIDownloader:
        return GitCLIDownloader(
            repository=url,
            branch=branch,
            working_dir=self.clone_path
        )

    def _get_new_github_downloader(
        self,
        url: URL,
        branch: Optional[str]
    ) -> GitHubDownloader:
        return GitHubDownloader(
            repository=url,
            branch=branch
        )


class GitDownload:
    """Takes care of joining all the tools in this module together and
    allow to safely download files from a Git repository.
    """

    def __init__(
        self,
        downloader_fetcher: GitDownloaderFetcher = GitDownloaderFetcher()
    ):
        """Constructor.

        :param downloader_fetcher: Tool that provides the APIs that this
            will use to interact with Git.
        """
        self._download_fetcher = downloader_fetcher

    @property
    def download_fetcher(self) -> GitDownloaderFetcher:
        """
        :return: Tool that provides the APIs that this
            will use to interact with Git.
        """
        return self._download_fetcher

    def download_as_yaml(
        self,
        repo: URL,
        file: str,
        branch: Optional[str] = None,
        yaml_parser: YAMLParser = StandardYAMLParser()
    ) -> YAML:
        """Downloads a YAML file from a Git repository and parses it into
        a Python object.

        :param repo: The Git repository.
        :param file: Relative path to the repo's root to the file to download.
        :param branch: Name of the branch to download from. 'None' to use the
            repo's default branch.
        :param yaml_parser: Tool used to parse the YAML file.
        :return: The file as a Python object.
        :raises DownloadError:
            If no API is available to download the file.
            If all APIs failed to download the file.
            If the file is not in YAML format.
        """
        try:
            for api in self._get_apis_for(repo, branch):
                LOG.info(
                    "Trying to download file: '%s' with API: '%s'...",
                    file, type(api).__name__
                )

                try:
                    return yaml_parser.as_yaml(api.download_as_text(file))
                except YAMLError as ex:
                    msg = f"Failed to parse YAML file: '{file}'."
                    raise DownloadError(msg) from ex
                except DownloadError as ex:
                    LOG.warning(
                        "Failed to download file through API: '%s'. "
                        "Reason: '%s'.",
                        type(api).__name__, ex
                    )

            raise DownloadError(
                f"All APIs failed to download file: '{file}' "
                f"at URL: '{repo}'."
            )
        except InvalidURL as ex:
            msg = f"No API available to handle URL: '{repo}'."
            raise DownloadError(msg) from ex

    def _get_apis_for(
        self,
        url: URL,
        branch: Optional[str]
    ) -> Iterable[GitDownloader]:
        result = self._download_fetcher.get_downloaders_for(url, branch)

        if not result:
            raise InvalidURL(f"Found no handlers for URL: '{url}'.")

        return result