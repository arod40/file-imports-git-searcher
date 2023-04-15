import concurrent.futures
import json
import logging
import os
import shutil
import sys
import stat
from pathlib import Path
import csv

import git
from git import Repo

from import_searcher.python_import_searcher import PythonFileImportSearcher
from import_searcher.java_import_searcher import JavaFileImportSearcher
from import_searcher.cpp_import_searcher import CppFileImportSearcher

# Set GIT_ASKPASS to avoid interactive authentication prompt
os.environ["GIT_ASKPASS"] = "./askpass.py"

# Allow large csv files
max_int = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int / 10)


def _unsupported_file_ext(f):
    def wrapper(self, *args, **kwargs):
        ext = args[0]
        if ext not in self._supported_file_exts:
            raise ValueError(f"Unsupported file extension {f}")
        return f(self, *args, **kwargs)

    return wrapper


class RepoSearchConfig:
    IMPORT_SEARCHERS = {
        ".py": PythonFileImportSearcher,
        ".java": JavaFileImportSearcher,
        ".h": CppFileImportSearcher,
        ".hpp": CppFileImportSearcher,
        ".cpp": CppFileImportSearcher,
    }

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
    for file_path in (
        f
        for f in root_dir.rglob("*")
        if not any(d in f.parts for d in excluded_dirs_by_ext.get(f.suffix, []))
        and f.is_file()
        and f.suffix in file_extensions
    ):
        if file_path.is_file():
            yield file_path


def __write_to_csv(record, csv_writer):
    csv_writer.writerow(record)


def __search(
    repo_info,
    config,
    repos_temp_path,
    writing_executor,
    output_writer,
    ignore_repos,
):
    repo_full_name = repo_info["full_name"]

    if repo_full_name in ignore_repos:
        logging.info(f"Ignoring {repo_full_name}")
        return

    repo_url = repo_info["url"]
    repo_path = repos_temp_path / repo_full_name.replace("/", "_")
    repo_commit_hash = repo_info["commit_hash"]

    try:
        logging.info(f"Cloning {repo_full_name}")
        repo = Repo.clone_from(repo_url, repo_path, multi_options=["--config credential.helper=''"])
        repo.git.checkout(repo_commit_hash)
        logging.info(
            f"Cloned {repo_full_name} and checkout to commit {repo_commit_hash}"
        )
    except git.exc.GitError as e:
        logging.error(f"Error cloning  {repo_full_name}")
        record = [repo_full_name, repo_url, False, None, str(e)]
        writing_executor.submit(__write_to_csv, record, output_writer)

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

    record = [repo_full_name, repo_url, True, list(found_frameworks), None]
    writing_executor.submit(__write_to_csv, record, output_writer)


def search_repos(repos, config, output_file):
    repos_temp_path = Path("__repos_temp__")
    repos_temp_path.mkdir(parents=True, exist_ok=True)

    rewrite_records = []
    ignore_repos = set()
    if os.path.exists(output_file):
        with open(output_file, newline="") as csvfile:
            output_reader = csv.reader(csvfile, delimiter=",", quotechar='"')
            next(output_reader, None)  # skipping the header
            for record in output_reader:
                repo_name, _, success, *_ = record
                if success == "True":
                    ignore_repos.add(repo_name)
                    rewrite_records.append(record)

    with open(output_file, "w", newline="") as csvfile:
        output_writer = csv.writer(
            csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        output_writer.writerow(["full_name", "url", "success", "frameworks", "error"])
        for record in rewrite_records:
            logging.info(f"Rewriting {record[0]}")
            output_writer.writerow(record)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as writing_executor:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=config.max_workers
            ) as executor:
                for repo in repos:
                    executor.submit(
                        __search,
                        repo,
                        config,
                        repos_temp_path,
                        writing_executor,
                        output_writer,
                        ignore_repos,
                    )

    repos_temp_path.rmdir()
