from tree_sitter import Language, Parser
import os

class SourceCodeAnalyzer:
    """
    A utility for analyzing source code using Tree-Sitter.
    Supports C#, C++, and JavaScript (can be extended).
    """

    def __init__(self):
        self.languages = self.load_tree_sitter_languages()
        self.parser = Parser()

    def load_tree_sitter_languages(self):
        """
        Loads Tree-Sitter language grammars dynamically.
        """
        LANGUAGES_PATH = os.path.join(os.getcwd(), "tree-sitter-languages")

        language_files = {
            "c_sharp": os.path.join(LANGUAGES_PATH, "tree-sitter-c-sharp.so"),
            "cpp": os.path.join(LANGUAGES_PATH, "tree-sitter-cpp.so"),
            "javascript": os.path.join(LANGUAGES_PATH, "tree-sitter-javascript.so")
        }

        languages = {}
        for lang, dll_path in language_files.items():
            if os.path.exists(dll_path):
                try:
                    languages[lang] = Language(dll_path, lang)
                    print(f"Successfully loaded Tree-Sitter DLL for {lang}: {dll_path}")
                except Exception as e:
                    print(f"Error loading Tree-Sitter DLL for {lang}: {e}")
            else:
                print(f"Warning: {dll_path} not found, skipping {lang}")

        return languages

    def parse_file(self, file_path, language):
        """
        Parses a source file using Tree-Sitter.
        Extracts function definitions for C#, C++, or JavaScript.
        """
        if language not in self.languages:
            raise ValueError(f"Unsupported language: {language}")

        with open(file_path, "r", encoding="utf-8") as file:
            code = file.read()

        self.parser.set_language(self.languages[language])
        tree = self.parser.parse(bytes(code, "utf8"))

        return self.extract_function_signatures(tree.root_node, code, language)

    def extract_function_signatures(self, root_node, code, language):
        """
        Extracts function signatures from the parsed syntax tree.
        Supports C#, C++, and JavaScript.
        """
        function_signatures = []

        for node in root_node.children:
            if language == "c_sharp" and node.type == "method_declaration":
                function_signatures.append(self._extract_csharp_function(node, code))
            elif language == "cpp" and node.type == "function_definition":
                function_signatures.append(self._extract_cpp_function(node, code))
            elif language == "javascript" and node.type in ["function_declaration", "method_definition"]:
                function_signatures.append(self._extract_javascript_function(node, code))

        return [f for f in function_signatures if f]

    def _extract_csharp_function(self, node, code):
        """
        Extracts C# function names, parameters, and return types.
        """
        function_name = None
        parameters = []
        return_type = None

        for child in node.children:
            if child.type == "identifier":
                function_name = code[child.start_byte:child.end_byte]
            elif child.type == "parameter_list":
                params_code = code[child.start_byte:child.end_byte]
                parameters = [p.strip() for p in params_code.strip("()").split(",") if p]
            elif child.type == "type":
                return_type = code[child.start_byte:child.end_byte]

        return {
            "name": function_name,
            "parameters": parameters,
            "return_type": return_type
        } if function_name else None

    def _extract_cpp_function(self, node, code):
        """
        Extracts C++ function definitions.
        """
        function_name = None
        parameters = []
        return_type = None

        for child in node.children:
            if child.type == "identifier":
                function_name = code[child.start_byte:child.end_byte]
            elif child.type == "parameter_list":
                params_code = code[child.start_byte:child.end_byte]
                parameters = [p.strip() for p in params_code.strip("()").split(",") if p]
            elif child.type == "type":
                return_type = code[child.start_byte:child.end_byte]

        return {
            "name": function_name,
            "parameters": parameters,
            "return_type": return_type
        } if function_name else None

    def _extract_javascript_function(self, node, code):
        """
        Extracts JavaScript function names and parameters.
        """
        function_name = None
        parameters = []

        for child in node.children:
            if child.type == "identifier":
                function_name = code[child.start_byte:child.end_byte]
            elif child.type == "formal_parameters":
                params_code = code[child.start_byte:child.end_byte]
                parameters = [p.strip() for p in params_code.strip("()").split(",") if p]

        return {
            "name": function_name,
            "parameters": parameters
        } if function_name else None


# Example Usage
if __name__ == "__main__":
    analyzer = SourceCodeAnalyzer()
    file_path = "example.cs"  # Replace with actual C# file path
    language = "c_sharp"

    try:
        functions = analyzer.parse_file(file_path, language)
        print("Extracted Functions:")
        for func in functions:
            print(func)
    except ValueError as e:
        print(e)
