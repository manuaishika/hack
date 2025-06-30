import ast
from typing import List, Dict

class DeadCodeDetector:
    @staticmethod
    def analyze_file(filepath: str) -> List[Dict]:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Placeholder logic: mark as unused if name starts with 'unused_'
                is_dead = node.name.startswith('unused_')
                reason = 'Unused (name heuristic)' if is_dead else ''
                if is_dead:
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'reason': reason,
                        'lines': len(node.body),
                        'energy_impact': None  # Placeholder
                    })
        return functions 