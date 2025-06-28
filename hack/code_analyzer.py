"""
code_analyzer.py
a tool to analyze python codebases for dead code, estimate compute cost, and suggest removals.
"""

import ast
import os
from typing import List, Dict, Tuple

# --- section 1: ast parsing utilities ---
def parse_python_file(filepath: str) -> ast.AST:
    """
    parse a python file into an ast.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    return ast.parse(source, filename=filepath)

# --- section 2: dead code detection ---
def find_function_defs(tree: ast.AST) -> Dict[str, ast.FunctionDef]:
    """
    find all function definitions in the ast.
    returns a dict mapping function names to their ast nodes.
    """
    return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

def find_function_calls(tree: ast.AST) -> List[str]:
    """
    find all function calls in the ast.
    returns a list of function names that are called.
    """
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    return calls

def find_unused_functions(tree: ast.AST) -> List[str]:
    """
    find functions that are defined but never called (dead code).
    """
    defs = find_function_defs(tree)
    calls = find_function_calls(tree)
    unused = [name for name in defs if name not in calls and not name.startswith('__')]
    return unused

# --- section 3: compute cost estimation ---
def estimate_function_cost(node: ast.FunctionDef) -> int:
    """
    estimate compute cost of a function by counting lines of code.
    (for a more advanced version, analyze flops or operations.)
    """
    return len(node.body)

def estimate_codebase_cost(tree: ast.AST) -> Dict[str, int]:
    """
    estimate compute cost for each function in the codebase.
    returns a dict mapping function names to their estimated cost.
    """
    defs = find_function_defs(tree)
    return {name: estimate_function_cost(node) for name, node in defs.items()}

# --- section 4: reporting and suggestions ---
def analyze_file(filepath: str) -> None:
    """
    analyze a python file for dead code and compute cost.
    print a report with suggestions.
    """
    print(f"\nanalyzing: {filepath}")
    tree = parse_python_file(filepath)
    unused = find_unused_functions(tree)
    costs = estimate_codebase_cost(tree)
    if unused:
        print("\nunused/dead functions detected:")
        for name in unused:
            print(f"  - {name} (estimated cost: {costs.get(name, 0)} lines)")
        print("\nsuggested fix: remove the above functions to reduce code size and compute cost.")
    else:
        print("no unused functions detected.")
    print("\nfunction compute cost estimates:")
    for name, cost in costs.items():
        print(f"  - {name}: {cost} lines")

# --- section 5: directory traversal ---
def analyze_directory(directory: str) -> None:
    """
    recursively analyze all python files in a directory.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                analyze_file(os.path.join(root, file))

# --- section 6: main entrypoint ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="analyze python codebase for dead code and compute cost.")
    parser.add_argument('path', type=str, help='path to python file or directory')
    args = parser.parse_args()
    if os.path.isdir(args.path):
        analyze_directory(args.path)
    else:
        analyze_file(args.path) 