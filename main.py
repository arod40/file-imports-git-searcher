import json
import logging
from argparse import ArgumentParser
from pathlib import Path

from repo_searcher import search_repos, RepoSearchConfig

if __name__ == "__main__":
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("-r", "--repos-file", type=str, help="Path to repos file")
    parser.add_argument(
        "-c", "--config-file", type=str, help="Path to the search config file"
    )
    parser.add_argument(
        "-o", "--output-file", type=str, help="CSV file to save results to. If file is already existing, it will resume from the last non-error record."
    )

    args = parser.parse_args()

    config = RepoSearchConfig(Path(args.config_file))
    repos = json.loads(Path(args.repos_file).read_text())
    search_repos(repos, config, args.output_file)
