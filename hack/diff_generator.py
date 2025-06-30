import difflib
from typing import List, Dict

def generate_dead_code_diff(filepath: str, dead_functions: List[Dict]) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # Find line numbers to remove (1-based in AST, 0-based in list)
    remove_lines = set()
    for func in dead_functions:
        start = func['line'] - 1
        # Remove until next function/class or end of file
        end = start + func['lines']
        for i in range(start, min(end, len(original_lines))):
            remove_lines.add(i)

    # Build new file lines
    new_lines = [line for idx, line in enumerate(original_lines) if idx not in remove_lines]

    diff = difflib.unified_diff(
        original_lines, new_lines,
        fromfile=filepath, tofile=filepath + '.cleaned',
        lineterm=''  # no extra newlines
    )
    return '\n'.join(diff) 