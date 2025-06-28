"""
enhanced_analyzer.py
phase 1.5: enhanced code analyzer with energy metrics, llm integration, and async detection
"""

import ast
import os
import asyncio
import threading
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import difflib
import shutil

# energy tracking imports
try:
    from codecarbon import EmissionsTracker
    from codecarbon.output import EmissionsData
    CARBON_AVAILABLE = True
except ImportError:
    CARBON_AVAILABLE = False
    print("warning: codecarbon not available, energy tracking disabled")

# llm integration imports
try:
    import openai
    from transformers import pipeline
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("warning: llm libraries not available, ai analysis disabled")

@dataclass
class FunctionAnalysis:
    """data class to store function analysis results"""
    name: str
    is_unused: bool
    is_async: bool
    is_threaded: bool
    line_count: int
    estimated_flops: int
    energy_impact: Optional[float] = None
    ai_explanation: Optional[str] = None
    ai_suggestion: Optional[str] = None

# --- section 1: enhanced ast parsing with async/threading detection ---
def detect_async_patterns(tree: ast.AST) -> List[str]:
    """
    detect async functions and await patterns in the ast.
    returns list of async function names.
    """
    async_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            async_funcs.append(node.name)
        elif isinstance(node, ast.Await):
            # find parent async function
            for parent in ast.walk(tree):
                if isinstance(parent, ast.AsyncFunctionDef):
                    if any(await_node in ast.walk(parent) for await_node in [node]):
                        async_funcs.append(parent.name)
                        break
    return list(set(async_funcs))

def detect_threading_patterns(tree: ast.AST) -> List[str]:
    """
    detect threading patterns like thread.start(), threading.Thread usage.
    returns list of functions that use threading.
    """
    threaded_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ['start', 'run', 'join']:
                    # find parent function
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.FunctionDef):
                            if any(call_node in ast.walk(parent) for call_node in [node]):
                                threaded_funcs.append(parent.name)
                                break
    return list(set(threaded_funcs))

# --- section 2: energy impact estimation using codecarbon ---
class EnergyTracker:
    """wrapper for codecarbon energy tracking"""
    
    def __init__(self):
        self.tracker = None
        self.emissions_data = None
    
    def start_tracking(self, project_name: str = "code_analysis"):
        """start energy tracking for the analysis"""
        if CARBON_AVAILABLE:
            self.tracker = EmissionsTracker(
                project_name=project_name,
                output_dir="./emissions_data"
            )
            self.tracker.start()
    
    def stop_tracking(self) -> Optional[float]:
        """stop tracking and return total emissions in kg co2"""
        if self.tracker:
            self.emissions_data = self.tracker.stop()
            return self.emissions_data.emissions
        return None
    
    def estimate_function_energy(self, function_node: ast.FunctionDef) -> float:
        """
        estimate energy impact of a function based on complexity.
        returns estimated energy consumption in joules.
        """
        # simple heuristic: more complex functions use more energy
        complexity_score = len(function_node.body) * 2
        
        # count loops and conditionals (higher energy impact)
        for node in ast.walk(function_node):
            if isinstance(node, (ast.For, ast.While, ast.If, ast.Try)):
                complexity_score += 5
        
        # convert to estimated joules (rough approximation)
        return complexity_score * 0.1

# --- section 3: llm integration for intelligent analysis ---
class LLMAnalyzer:
    """ai-powered code analysis using openai or local models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if LLM_AVAILABLE and api_key:
            openai.api_key = api_key
            self.client = openai.OpenAI()
    
    def analyze_function_usefulness(self, function_code: str, function_name: str) -> Tuple[str, str]:
        """
        use llm to explain why a function might be useless and suggest fixes.
        returns (explanation, suggestion) tuple.
        """
        if not self.client:
            return "llm analysis not available", "enable openai api key for ai suggestions"
        
        prompt = f"""
        analyze this python function and determine if it's likely useless or dead code:
        
        function name: {function_name}
        code:
        {function_code}
        
        provide:
        1. explanation of why this function might be useless
        2. suggestion for safe removal or refactoring
        
        format as json with 'explanation' and 'suggestion' keys.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            # try to parse json response
            try:
                parsed = json.loads(result)
                return parsed.get('explanation', 'no explanation'), parsed.get('suggestion', 'no suggestion')
            except:
                return result, "see explanation above"
                
        except Exception as e:
            return f"llm analysis failed: {str(e)}", "check api configuration"

# --- section 4: enhanced function analysis ---
def analyze_function_complexity(node: ast.FunctionDef) -> int:
    """
    estimate computational complexity (flops) of a function.
    returns estimated floating point operations.
    """
    flops = 0
    
    for ast_node in ast.walk(node):
        if isinstance(ast_node, ast.BinOp):
            flops += 1  # basic arithmetic operation
        elif isinstance(ast_node, ast.Compare):
            flops += 1  # comparison operation
        elif isinstance(ast_node, (ast.For, ast.While)):
            # estimate loop iterations (conservative)
            flops += 10
        elif isinstance(ast_node, ast.Call):
            flops += 5  # function call overhead
    
    return flops

def create_function_analysis(
    function_name: str,
    function_node: ast.FunctionDef,
    is_unused: bool,
    async_funcs: List[str],
    threaded_funcs: List[str],
    energy_tracker: EnergyTracker,
    llm_analyzer: LLMAnalyzer
) -> FunctionAnalysis:
    """
    create comprehensive analysis for a single function.
    """
    is_async = function_name in async_funcs
    is_threaded = function_name in threaded_funcs
    line_count = len(function_node.body)
    estimated_flops = analyze_function_complexity(function_node)
    
    # get energy impact
    energy_impact = energy_tracker.estimate_function_energy(function_node)
    
    # get ai analysis for unused functions
    ai_explanation = None
    ai_suggestion = None
    if is_unused and llm_analyzer:
        function_code = ast.unparse(function_node)
        ai_explanation, ai_suggestion = llm_analyzer.analyze_function_usefulness(
            function_code, function_name
        )
    
    return FunctionAnalysis(
        name=function_name,
        is_unused=is_unused,
        is_async=is_async,
        is_threaded=is_threaded,
        line_count=line_count,
        estimated_flops=estimated_flops,
        energy_impact=energy_impact,
        ai_explanation=ai_explanation,
        ai_suggestion=ai_suggestion
    )

# --- section 5: enhanced file analysis ---
def analyze_file_enhanced(
    filepath: str,
    energy_tracker: EnergyTracker,
    llm_analyzer: LLMAnalyzer
) -> List[FunctionAnalysis]:
    """
    enhanced analysis of a python file with energy and ai insights.
    """
    print(f"\nanalyzing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source, filename=filepath)
    
    # get all function definitions
    function_defs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    
    # find function calls
    function_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                function_calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                function_calls.append(node.func.attr)
    
    # detect patterns
    async_funcs = detect_async_patterns(tree)
    threaded_funcs = detect_threading_patterns(tree)
    
    # analyze each function
    analyses = []
    for name, node in function_defs.items():
        if name.startswith('__'):  # skip magic methods
            continue
            
        is_unused = name not in function_calls
        analysis = create_function_analysis(
            name, node, is_unused, async_funcs, threaded_funcs,
            energy_tracker, llm_analyzer
        )
        analyses.append(analysis)
    
    return analyses

# --- section 6: reporting and visualization ---
def print_enhanced_report(analyses: List[FunctionAnalysis], total_energy: Optional[float] = None):
    """
    print comprehensive analysis report with energy metrics and ai insights.
    """
    print("\n" + "="*60)
    print("enhanced code analysis report")
    print("="*60)
    
    # unused functions
    unused = [a for a in analyses if a.is_unused]
    if unused:
        print(f"\n🚨 unused/dead functions detected: {len(unused)}")
        print("-" * 40)
        for analysis in unused:
            print(f"\nfunction: {analysis.name}")
            print(f"  lines: {analysis.line_count}")
            print(f"  estimated flops: {analysis.estimated_flops}")
            print(f"  energy impact: {analysis.energy_impact:.2f} joules")
            if analysis.is_async:
                print("  ⚡ async function")
            if analysis.is_threaded:
                print("  🔄 threaded function")
            if analysis.ai_explanation:
                print(f"  ai explanation: {analysis.ai_explanation}")
            if analysis.ai_suggestion:
                print(f"  ai suggestion: {analysis.ai_suggestion}")
    else:
        print("\n✅ no unused functions detected")
    
    # energy summary
    if total_energy:
        print(f"\n⚡ total analysis energy: {total_energy:.4f} kg co2")
    
    # complexity summary
    total_flops = sum(a.estimated_flops for a in analyses)
    print(f"\n🧮 total estimated flops: {total_flops}")
    
    # async/threading summary
    async_count = sum(1 for a in analyses if a.is_async)
    threaded_count = sum(1 for a in analyses if a.is_threaded)
    if async_count > 0 or threaded_count > 0:
        print(f"\n🔄 concurrent code detected:")
        print(f"  async functions: {async_count}")
        print(f"  threaded functions: {threaded_count}")

# --- section: code cleaning and safe removal ---
def remove_dead_code_from_source(source: str, unused_funcs: list) -> str:
    """
    remove unused function definitions from the source code.
    """
    tree = ast.parse(source)
    new_body = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in unused_funcs:
            continue  # skip dead code
        new_body.append(node)
    tree.body = new_body
    return ast.unparse(tree)

# --- section: gpt-powered code rewriting ---
def rewrite_inefficient_code(function_code: str, api_key: str) -> str:
    """
    use gpt api to rewrite inefficient code sections (loops, branches).
    """
    if not LLM_AVAILABLE or not api_key:
        return function_code
    prompt = f"rewrite this python function to be more efficient, especially optimizing loops and branches. only return the improved function code.\n\n{function_code}"
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return function_code

def generate_diff(original_code: str, cleaned_code: str, filename: str) -> str:
    """
    generate a unified diff showing suggested deletions.
    """
    original_lines = original_code.splitlines(keepends=True)
    cleaned_lines = cleaned_code.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines, cleaned_lines,
        fromfile=filename, tofile=filename + ".cleaned",
        lineterm=''
    )
    return ''.join(diff)

# --- update main to support new flags and features ---
def main():
    """main function for enhanced code analysis with phase 2 features"""
    import argparse
    
    parser = argparse.ArgumentParser(description="enhanced code analyzer with energy metrics, ai insights, and refactoring features")
    parser.add_argument('path', type=str, help='path to python file or directory')
    parser.add_argument('--openai-key', type=str, help='openai api key for ai analysis and rewriting')
    parser.add_argument('--track-energy', action='store_true', help='enable energy tracking')
    parser.add_argument('--safe-remove', action='store_true', help='copy and strip dead code automatically')
    parser.add_argument('--show-diff', action='store_true', help='show code diff for suggested deletions')
    parser.add_argument('--rewrite-inefficient', action='store_true', help='use gpt to rewrite inefficient code sections')
    
    args = parser.parse_args()
    
    energy_tracker = EnergyTracker()
    llm_analyzer = LLMAnalyzer(args.openai_key)
    
    if args.track_energy:
        energy_tracker.start_tracking()
    
    all_analyses = []
    filepaths = []
    if os.path.isdir(args.path):
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith('.py'):
                    filepaths.append(os.path.join(root, file))
    else:
        filepaths.append(args.path)
    
    for filepath in filepaths:
        analyses = analyze_file_enhanced(filepath, energy_tracker, llm_analyzer)
        all_analyses.extend(analyses)
        unused_funcs = [a.name for a in analyses if a.is_unused]
        if unused_funcs:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_code = f.read()
            cleaned_code = remove_dead_code_from_source(original_code, unused_funcs)
            # show diff if requested
            if args.show_diff:
                diff = generate_diff(original_code, cleaned_code, filepath)
                print(f"\ncode diff for {filepath} (suggested deletions):\n")
                print(diff)
            # safe-remove: write cleaned file
            if args.safe_remove:
                cleaned_path = filepath + ".cleaned.py"
                with open(cleaned_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_code)
                print(f"\nsafe-removed file written to: {cleaned_path}")
        # rewrite inefficient code
        if args.rewrite_inefficient and args.openai_key:
            for a in analyses:
                if a.estimated_flops > 50:  # threshold for inefficiency
                    function_code = ast.unparse([node for node in ast.parse(original_code).body if isinstance(node, ast.FunctionDef) and node.name == a.name][0])
                    improved_code = rewrite_inefficient_code(function_code, args.openai_key)
                    print(f"\nrewritten code for inefficient function {a.name}:\n{improved_code}\n")
    
    total_energy = None
    if args.track_energy:
        total_energy = energy_tracker.stop_tracking()
    print_enhanced_report(all_analyses, total_energy)

if __name__ == "__main__":
    main() 