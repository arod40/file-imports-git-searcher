Hello, all! Refer back to this resource for guidance. To add support for a specific language follow these two steps:

1. Create a class that inherits `FileImportSearcher` at `import_searcher/file_import_searcher.py` and override the method `search_import(self, file_content: str) -> Iterable[str]`. The method should return a list of unique frameworks used in the file whose content is passed.

2. Also, in the `searchers_config.py` file add the appropriate entry to the dictionary.

To run the CLI you need to pass the list of repos and the frameworks list per file type to search for (currently these are meant to be JSON files, but we can change that). Also, pass the number of workers, i.e., CPU cores you want to commit to the task. Finally, pass the path to a directory to store the results. These are going to be two files: `results.json` and `errors.json` with the successfully and the unsuccessfuly analyzed repos, respectively.

In the repo there is an `example` directory, with input examples for the repos and frameworks files. Below is an example for running the CLI.

`python main.py -r "example/repos.json" -f "example/frameworks.json" -w 2 -s exp1`

Note: Please, as you contribute to the repo, make sure to run `python -m black .` before merging with main, so as to keep consistent formatting within the python files.