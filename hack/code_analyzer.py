"""
code_analyzer.py
a tool to analyze python codebases for dead code, estimate compute cost, and suggest removals.
"""

import argparse
from dead_code_detector import DeadCodeDetector
from output_formatter import print_dead_code_table
from report_generator import generate_html_report
from diff_generator import generate_dead_code_diff
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Detect dead/unreachable/unused functions in Python files.")
    parser.add_argument('path', help='Path to Python file or directory')
    parser.add_argument('--html', action='store_true', help='Generate an HTML report (dead_code_report.html)')
    parser.add_argument('--diff', action='store_true', help='Show unified diff for dead code removal')
    args = parser.parse_args()

    if os.path.isfile(args.path):
        files = [args.path]
    elif os.path.isdir(args.path):
        files = [
            os.path.join(root, f)
            for root, _, files in os.walk(args.path)
            for f in files if f.endswith('.py')
        ]
    else:
        print(f"Error: {args.path} is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

    all_results = []
    file_results = {}
    for file in files:
        results = DeadCodeDetector.analyze_file(file)
        file_results[file] = results
        if results:
            print(f"\n[bold underline]File:[/bold underline] {file}")
            print_dead_code_table(results)
            all_results.extend(results)
        else:
            print(f"\nFile: {file} - No dead code detected.")

    if args.html:
        if all_results:
            generate_html_report(all_results)
        else:
            print("[HTML] No dead code found, no report generated.")

    if args.diff:
        for file, results in file_results.items():
            if results:
                print(f"\n[DIFF] Unified diff for {file}:")
                diff = generate_dead_code_diff(file, results)
                print(diff or '[No changes]')

if __name__ == "__main__":
    main() 