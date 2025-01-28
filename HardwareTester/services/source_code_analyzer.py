import os
from tree_sitter import  Parser
from HardwareTester.utils.custom_logger import CustomLogger
from tree_sitter_languages import get_language

CSHARP_LANGUAGE = get_language("c_sharp")
CPP_LANGUAGE = get_language("cpp")
JAVASCRIPT_LANGUAGE = get_language("javascript")

logger = CustomLogger.get_logger("SourceCodeAnalyzer")


class SourceCodeAnalyzer:    
    """
    A utility for analyzing C# source code to extract class and method metadata.
    """
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

    def _extract_methods(self, node, parent_class=None):
        """
        Recursively extract methods and their parameters from the AST.
        """
        methods = []
        for child in node.children:
            if child.type == "class_declaration":
                class_name = child.child_by_field_name("name").text.decode()
                methods.extend(self._extract_methods(child, parent_class=class_name))
            elif child.type == "method_declaration":
                method_name = child.child_by_field_name("name").text.decode()
                parameters = []
                parameter_node = child.child_by_field_name("parameter_list")
                if parameter_node:
                    for param in parameter_node.children:
                        if param.type == "parameter":
                            param_type = param.child_by_field_name("type").text.decode()
                            param_name = param.child_by_field_name("name").text.decode()
                            parameters.append({"type": param_type, "name": param_name})
                methods.append({
                    "class": parent_class,
                    "method": method_name,
                    "parameters": parameters
                })
        return methods

    def _extract_methods_cpp(self, node):
        # Extract classes, methods, and parameters from C++
        pass

    def _extract_ui_elements(self, node):
        # Extract JavaScript UI components (e.g., menus, buttons)
        pass

    def _extract_methods(self, node, parent_class=None):
        """
        Recursively extract methods and their parameters from the AST.
        """
        methods = []
        for child in node.children:
            if child.type == "class_declaration":
                class_name = child.child_by_field_name("name").text.decode()
                methods.extend(self._extract_methods(child, parent_class=class_name))
            elif child.type == "method_declaration":
                method_name = child.child_by_field_name("name").text.decode()
                parameters = []
                parameter_node = child.child_by_field_name("parameter_list")
                if parameter_node:
                    for param in parameter_node.children:
                        if param.type == "parameter":
                            param_type = param.child_by_field_name("type").text.decode()
                            param_name = param.child_by_field_name("name").text.decode()
                            parameters.append({"type": param_type, "name": param_name})
                methods.append({
                    "class": parent_class,
                    "method": method_name,
                    "parameters": parameters
                })
        return methods

    def analyze_repo(self, repo_path):
        """
        Analyze all C# files in a repository.
        """
        all_methods = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".cs"):
                    file_path = os.path.join(root, file)
                    methods = self.parse_file(file_path)
                    all_methods.extend(methods)
        return all_methods
