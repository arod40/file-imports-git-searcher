from .file_import_searcher import FileImportSearcher
import re

"""
Searches for imports in Python files.
"""


class PythonFileImportSearcher(FileImportSearcher):
    def search_import(self, file_content: str):
        found_frameworks = set()
        for name, import_name in self.frameworks.items():
            r = re.compile(f"from .*{import_name}.* .*import", re.MULTILINE)
            if r.search(file_content):
                found_frameworks.add(name)

            r = re.compile(f"import {import_name}", re.MULTILINE)
            if r.search(file_content):
                found_frameworks.add(name)

        return found_frameworks


if __name__ == "__main__":
    import_searcher = PythonFileImportSearcher({"sklearn": "sklearn"})
    print(
        import_searcher.search_import(
            "from sklearn.linear_model import LinearRegression"
        )
    )
