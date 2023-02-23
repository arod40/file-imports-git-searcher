import concurrent.futures
import logging
import os
import shutil
import stat
from pathlib import Path

import git
from git import Repo


def __iter_files(root_dir, exclude_dirs, file_extensions):
    pattern = f'*{"|".join(file_extensions)}'
    for file_path in (
        f
        for f in root_dir.rglob(pattern)
        if not any(d in f.parts for d in exclude_dirs)
    ):
        if file_path.is_file():
            yield file_path


def __search(
    repo_info,
    file_searchers,
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
        exclude_dirs=[".git", "env", "Lib", "site-packages", "venv"],
        file_extensions=[".py"],
    ):
        file_content = file_path.read_text()
        file_ext = file_path.suffix
        file_searcher = file_searchers[file_ext]
        found_frameworks = found_frameworks.union(
            file_searcher.search_import(file_content)
        )
    logging.info(f"Analyzed {repo_full_name}")

    def remove_readonly(func, path, _):
        "Clear the readonly bit and reattempt the removal"
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(repo_path, onerror=remove_readonly)

    return True, repo_full_name, repo_url, list(found_frameworks)


def search_repos(repos, file_searchers, max_workers=4):
    repos_temp_path = Path("__repos_temp__")
    repos_temp_path.mkdir(parents=True, exist_ok=True)

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for repo in repos:
            futures.append(
                executor.submit(__search, repo, file_searchers, repos_temp_path)
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
