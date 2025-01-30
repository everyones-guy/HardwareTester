#from tree_sitter import Language

#Language.build_library(
#    'build/my-languages.so',
#    [
#        'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-c-sharp',  # Replace with actual paths
#        'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-cpp',
#        'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-javascript'
#    ]
#)


# run this command to create languages:

#gcc -o build/my-languages.so -shared -fPIC C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-c-sharp/src/parser.c C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-cpp/src/parser.c C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-javascript/src/parser.c C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-c-sharp/src/scanner.c C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-cpp/src/scanner.c C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-javascript/src/scanner.c



from tree_sitter import Language

CSHARP_LANGUAGE = 'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-c-sharp/c_sharp.so'
CPP_LANGUAGE = 'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-cpp/cpp.so'
JAVASCRIPT_LANGUAGE = 'C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/tree-sitter-languages/tree-sitter-javascript/javascript.so'


#lang = Language('build/my-languages.cpp')


#Language.__new__.__defaults__ = (None, "C:/Users/Gary/source/repos/HardwareTester/emulator-dashboard/build/my-languages.so")

#Language.build_library(
#TreeSitterLanguage.build_library(
#    "build/tree-sitter-languages.so",  # Output file
#    [
#        "tree-sitter-cpp",
#        "tree-sitter-c-sharp",
#        "tree-sitter-javascript",
#    ]
#)

print("Tree-Sitter languages compiled successfully!")
