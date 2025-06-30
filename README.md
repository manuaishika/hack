A modular Python CLI tool to detect dead/unreachable/unused functions in Python codebases, estimate code savings, and generate reports.

## Installation
1. Clone the repo
2. Install dependencies:
   ```sh
   pip install rich jinja2
   ```

## Usage
Analyze a file or directory:
```sh
python hack/code_analyzer.py <file_or_directory>
```

Generate an HTML report:
```sh
python hack/code_analyzer.py <file_or_directory> --html
```

Show unified diff for dead code removal:
```sh
python hack/code_analyzer.py <file_or_directory> --diff
```

Combine flags as needed!

---

**Requirements:**
- Python 3.7+
- `rich`, `jinja2` (see above) 