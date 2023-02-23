from typing import Dict, Iterable

"""
Abstraction to find matches of imports in a file.
To add a new language, create a new class that inherits from FileImportSearcher and implements the search_import method.
"""


class FileImportSearcher:
    """
    :param frameworks: A dictionary of frameworks to search for. The key is the name of the framework and the value is the import name.
    """

    def __init__(self, frameworks: Dict[str, str]):
        self.frameworks = frameworks

    """
    :param file_content: The content of the file to search for imports.
    :return: An iterable of unique framework names that were found in the file.
    """

    def search_import(self, file_content: str) -> Iterable[str]:
        raise NotImplementedError()
