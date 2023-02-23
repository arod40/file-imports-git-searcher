import json
import logging
from argparse import ArgumentParser
from pathlib import Path

from repo_searcher import search_repos
from searchers_config import IMPORT_SEARCHERS

if __name__ == "__main__":
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("-r", "--repos-file", type=str, help="Path to repos file")
    parser.add_argument(
        "-f", "--frameworks-file", type=str, help="Path to frameworks file"
    )
    parser.add_argument(
        "-w",
        "--num-workers",
        type=int,
        default=4,
        help="Number of parallel workers to use",
    )
    parser.add_argument("-s", "--save-dir", type=str, help="Path to save results to")

    args = parser.parse_args()

    repos = json.loads(Path(args.repos_file).read_text())
    frameworks = json.loads(Path(args.frameworks_file).read_text())
    file_searchers = {}
    for ext in frameworks:
        if ext not in IMPORT_SEARCHERS:
            logging.warning(f"Unsupported file extension {ext}")
        else:
            file_searchers[ext] = IMPORT_SEARCHERS[ext](frameworks[ext])

    results, errors = search_repos(repos, file_searchers, max_workers=args.num_workers)

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    Path(save_dir / "results.json").write_text(json.dumps(results, indent=4))
    Path(save_dir / "errors.json").write_text(json.dumps(errors, indent=4))
