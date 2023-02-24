import concurrent.futures
import json
import logging
import os
import shutil
import stat
from pathlib import Path

import git
from git import Repo

from import_searcher.python_import_searcher import PythonFileImportSearcher


def _unsupported_file_ext(f):
    def wrapper(self, *args, **kwargs):
        ext = args[0]
        if ext not in self._supported_file_exts:
            raise ValueError(f"Unsupported file extension {f}")
        return f(self, *args, **kwargs)

    return wrapper


class RepoSearchConfig:
    IMPORT_SEARCHERS = {".py": PythonFileImportSearcher}

    def __init__(self, config_path: Path):
        self._config_path = config_path
        self._config = json.loads(self._config_path.read_text())
        self._supported_file_exts = set(self._config.keys())
        self._supported_file_exts.remove("_global")

        for ext in self._supported_file_exts:
            if ext not in self.IMPORT_SEARCHERS:
                raise ValueError(f"Unsupported file extension {ext}")

            self._config[ext]["file_searcher"] = self.IMPORT_SEARCHERS[ext](
                self._config[ext]["frameworks"]
            )

    @_unsupported_file_ext
    def excluded_dirs(self, ext):
        return (
            self._config[ext]["excluded_dirs"]
            + self._config["_global"]["excluded_dirs"]
        )

    @_unsupported_file_ext
    def file_searcher(self, ext):
        return self._config[ext]["file_searcher"]

    @property
    def max_workers(self):
        return self._config["_global"]["max_workers"]

    @property
    def supported_file_exts(self):
        return self._supported_file_exts

    @property
    def excluded_dirs_by_ext(self):
        return {ext: self.excluded_dirs(ext) for ext in self.supported_file_exts}


def __iter_files(root_dir, file_extensions, excluded_dirs_by_ext):
    pattern = f'*{"|".join(file_extensions)}'
    for file_path in (
        f
        for f in root_dir.rglob(pattern)
        if not any(d in f.parts for d in excluded_dirs_by_ext.get(f.suffix, []))
    ):
        if file_path.is_file():
            yield file_path


def __search(
    repo_info,
    config,
    repos_temp_path,
):
    repo_full_name = repo_info["full_name"]
    repo_url = repo_info["url"]
    repo_path = repos_temp_path / repo_full_name.replace("/", "_")

    try:
        logging.info(f"Cloning {repo_full_name}")
        Repo.clone_from(repo_url, repo_path)
        logging.info(f"Cloned {repo_full_name}")
    except git.exc.GitError as e:
        logging.error(f"Error cloning  {repo_full_name}")
        return False, repo_full_name, repo_url, str(e)

    found_frameworks = set()
    logging.info(f"Analyzing {repo_full_name}")
    for file_path in __iter_files(
        repo_path,
        file_extensions=config.supported_file_exts,
        excluded_dirs_by_ext=config.excluded_dirs_by_ext,
    ):
        file_content = file_path.read_text()
        file_ext = file_path.suffix

        found_frameworks = found_frameworks.union(
            config.file_searcher(file_ext).search_import(file_content)
        )
    logging.info(f"Analyzed {repo_full_name}")

    def remove_readonly(func, path, _):
        "Clear the readonly bit and reattempt the removal"
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(repo_path, onerror=remove_readonly)

    return True, repo_full_name, repo_url, list(found_frameworks)


def search_repos(repos, config):
    repos_temp_path = Path("__repos_temp__")
    repos_temp_path.mkdir(parents=True, exist_ok=True)

    futures = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config.max_workers
    ) as executor:
        for repo in repos:
            futures.append(
                executor.submit(
                    __search,
                    repo,
                    config,
                    repos_temp_path,
                )
            )

    successful = []
    errors = []
    for future in concurrent.futures.as_completed(futures):
        success, repo_full_name, repo_url, results = future.result()
        if success:
            successful.append(
                {"full_name": repo_full_name, "url": repo_url, "frameworks": results}
            )
        else:
            errors.append(
                {"full_name": repo_full_name, "url": repo_url, "error": results}
            )

    repos_temp_path.rmdir()

    return successful, errors
