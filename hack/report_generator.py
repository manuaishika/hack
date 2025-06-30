from typing import List, Dict
import os

def generate_html_report(results: List[Dict], output_file: str = 'dead_code_report.html'):
    try:
        from jinja2 import Template
    except ImportError:
        print("[ERROR] Jinja2 is not installed. Please run: pip install jinja2", flush=True)
        return

    html_template = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <title>Dead Code Report</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f8f9fa; color: #222; }
            h1 { color: #b30059; }
            table { border-collapse: collapse; width: 100%; background: #fff; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background: #f2e6ff; color: #4b006e; }
            tr:nth-child(even) { background: #f9f9f9; }
            .icon { font-size: 1.2em; }
        </style>
    </head>
    <body>
        <h1>Dead/Unused Functions Report</h1>
        <table>
            <tr>
                <th>Function</th>
                <th>Line</th>
                <th>Reason</th>
                <th>Lines Saved</th>
                <th>Energy Impact</th>
            </tr>
            {% for func in results %}
            <tr>
                <td class="icon">🪦 {{ func.name }}</td>
                <td>{{ func.line }}</td>
                <td>{{ func.reason }}</td>
                <td>{{ func.lines }}</td>
                <td>{{ func.energy_impact or '-' }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    template = Template(html_template)
    html = template.render(results=results)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[HTML] Dead code report saved to {os.path.abspath(output_file)}") 