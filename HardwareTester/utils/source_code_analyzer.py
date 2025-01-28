from tree_sitter import Language, Parser
from HardwareTester.utils.custom_logger import CustomLogger

logger = CustomLogger.get_logger("SourceCodeAnalyzer")

# Build Tree-sitter for C#, C++, and JavaScript
Language.build_library(
    'build/my-languages.so',
    [
        'tree-sitter/tree-sitter-c-sharp',
        'tree-sitter/tree-sitter-cpp',
        'tree-sitter/tree-sitter-javascript'
    ]
)

CSHARP_LANGUAGE = Language('build/my-languages.so', 'c_sharp')
CPP_LANGUAGE = Language('build/my-languages.so', 'cpp')
JAVASCRIPT_LANGUAGE = Language('build/my-languages.so', 'javascript')


class SourceCodeAnalyzer:
    def __init__(self):
        self.parsers = {
            "csharp": Parser(),
            "cpp": Parser(),
            "javascript": Parser()
        }
        self.parsers["csharp"].set_language(CSHARP_LANGUAGE)
        self.parsers["cpp"].set_language(CPP_LANGUAGE)
        self.parsers["javascript"].set_language(JAVASCRIPT_LANGUAGE)

    def parse_file(self, file_path, language):
        """
        Parse a source file based on its language.
        """
        try:
            with open(file_path, 'r') as file:
                code = file.read()

            parser = self.parsers.get(language)
            if not parser:
                raise ValueError(f"Unsupported language: {language}")

            tree = parser.parse(bytes(code, "utf8"))
            root_node = tree.root_node

            if language == "csharp":
                return self._extract_methods_csharp(root_node)
            elif language == "cpp":
                return self._extract_methods_cpp(root_node)
            elif language == "javascript":
                return self._extract_ui_elements(root_node)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def _extract_methods_csharp(self, node):
        # Implementation for C# (similar to earlier)
        pass

    def _extract_methods_cpp(self, node):
        # Extract classes, methods, and parameters from C++
        pass

    def _extract_ui_elements(self, node):
        # Extract JavaScript UI components (e.g., menus, buttons)
        pass

