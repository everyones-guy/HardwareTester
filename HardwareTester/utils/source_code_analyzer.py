from tree_sitter import Language, Parser
import os

class SourceCodeAnalyzer:
    """
    A utility for analyzing source code using Tree-Sitter (v0.19 syntax).
    """

    def __init__(self):
        self.languages = self.load_tree_sitter_languages()

    def load_tree_sitter_languages(self):
        """
        Loads Tree-Sitter language grammars from individual DLLs.
        """
        #LANGUAGES_PATH = os.path.join(os.getcwd(), "tree-sitter-languages")
        LANGUAGES_PATH = "C:/Users/Gary/source/repos/HardwareTester/tree-sitter-languages"

        language_files = {
            "c_sharp": os.path.join(LANGUAGES_PATH, "tree-sitter-c-sharp.dll"),
            "cpp": os.path.join(LANGUAGES_PATH, "tree-sitter-cpp.dll"),
            "javascript": os.path.join(LANGUAGES_PATH, "tree-sitter-javascript.dll")
        }

        languages = {}
        for lang, dll_path in language_files.items():
            if os.path.exists(dll_path):
                try:
                    languages[lang] = Language(dll_path, lang)  # FIX: Added `name` argument
                    print(f"Successfully loaded Tree-Sitter DLL for {lang}: {dll_path}")
                except Exception as e:
                    print(f"Error loading Tree-Sitter DLL for {lang}: {e}")
            else:
                print(f"Warning: {dll_path} not found, skipping {lang}")

        return languages

    def parse_file(self, file_path, language):
        """
        Parses a source file using Tree-Sitter.
        """
        if language not in self.languages:
            raise ValueError(f"Unsupported language: {language}")

        with open(file_path, "r", encoding="utf-8") as file:
            code = file.read()

        parser = Parser()
        parser.set_language(self.languages[language])
        tree = parser.parse(bytes(code, "utf8"))

        return tree.root_node
