Hello, all! Refer back to this resource for guidance. To add support for a specific language follow these two steps:

1. Create a class that inherits `FileImportSearcher` at `import_searcher/file_import_searcher.py` and override the method `search_import(self, file_content: str) -> Iterable[str]`. The method should return a list of unique frameworks used in the file whose content is passed.

2. Also, in the `RepoSearchConfig` class in the `repo_searcher.py` file add the appropriate entry to the dictionary `IMPORT_SEARCHERS`.

To run the CLI you need to pass the list of repos and the search configuration. Among the configuration entries you will find options for:

- Exclude certain directories from the search, both globally and extension-specific. For example, for the `.py` files, one would usually exclude the `venv` directory, meaning that any `.py` inside a `venv` directory will be ignored.
- For each extension, set the frameworks that are being looked for in the search.
- Set the max number of workers. This is the number of CPUs engaged in parallel for running the repository search. IMPORTANT: Take into account that there is an extra thread requested by the program to write to the output file. This is: this script is going to use max_workers + 1 threads, potentially.

In this repo, there is an `example` directory, with input examples for the `repos.json` and `config.json` files. 

Finally, you need to pass to the script the path to a csv file to store the results. Importantly, if the file you pass already exists, the program will interpret it as if it needs to resume from a previously failed/interrupted execution. In this case, it will ignore all the records in the existing from the start until the last successful record.

Below is an example for running the CLI.

`python main.py -r "example/repos.json" -c "example/config.json" -o example/output.csv`

Note: Please, as you contribute to the repo, make sure to run `python -m black .` before merging with main, so as to keep consistent formatting within the python files.