from .file_import_searcher import FileImportSearcher
import re

"""
Searches for C++ header files in C++ source files.
"""

class CppFileImportSearcher(FileImportSearcher):
    def search_import(self, file_content: str) -> set:
        found_frameworks = set()
        for name, header_name in self.frameworks.items():
            r = re.compile(f"#include *[<\"] *{header_name}.*\.(h|hpp)[>\"]", re.MULTILINE)
            if r.search(file_content):
                found_frameworks.add(name)

        return found_frameworks
