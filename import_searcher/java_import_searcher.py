from .file_import_searcher import FileImportSearcher
import re

"""
Searches for imports in Java files.
"""


class JavaFileImportSearcher(FileImportSearcher):
    def search_import(self, file_content: str) -> set:
        found_frameworks = set()
        for name, import_name in self.frameworks.items():
            r = re.compile(f"import {import_name}.*")
            if r.search(file_content):
                found_frameworks.add(name)

        return found_frameworks
