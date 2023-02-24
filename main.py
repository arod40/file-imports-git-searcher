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
    parser.add_argument("-s", "--save-dir", type=str, help="Path to save results to")

    args = parser.parse_args()

    config = RepoSearchConfig(Path(args.config_file))
    repos = json.loads(Path(args.repos_file).read_text())
    results, errors = search_repos(repos, config)

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    Path(save_dir / "results.json").write_text(json.dumps(results, indent=4))
    Path(save_dir / "errors.json").write_text(json.dumps(errors, indent=4))
