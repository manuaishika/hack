"""
main.py
fastapi backend for the enhanced code analyzer web application
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import shutil
from typing import List, Dict, Any
import json
import sys
import ast

# add project root to path to import our analyzer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from hack.enhanced_analyzer import (
    analyze_file_enhanced, 
    EnergyTracker, 
    LLMAnalyzer,
    generate_diff,
    remove_dead_code_from_source,
    rewrite_inefficient_code
)

app = FastAPI(title="enhanced code analyzer api", version="1.0.0")

# configure cors for react frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# global storage for uploaded files (in production, use proper database)
uploaded_files = {}

@app.get("/")
async def root():
    """health check endpoint"""
    return {"message": "enhanced code analyzer api is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    upload a python file for analysis
    """
    if not file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="only python files (.py) are supported")
    
    # create temporary file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # store file info
        file_id = len(uploaded_files) + 1
        uploaded_files[file_id] = {
            "filename": file.filename,
            "path": temp_path,
            "size": os.path.getsize(temp_path)
        }
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "message": "file uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"upload failed: {str(e)}")

@app.post("/analyze/{file_id}")
async def analyze_file(
    file_id: int,
    openai_key: str = None,
    track_energy: bool = False,
    show_diff: bool = False,
    safe_remove: bool = False,
    rewrite_inefficient: bool = False
):
    """
    analyze uploaded file with specified options
    """
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="file not found")
    
    file_info = uploaded_files[file_id]
    filepath = file_info["path"]
    
    try:
        # initialize components
        energy_tracker = EnergyTracker()
        llm_analyzer = LLMAnalyzer(openai_key)
        
        if track_energy:
            energy_tracker.start_tracking()
        
        # analyze file
        analyses = analyze_file_enhanced(filepath, energy_tracker, llm_analyzer)
        
        # prepare response data
        result = {
            "file_id": file_id,
            "filename": file_info["filename"],
            "analyses": []
        }
        
        # convert analyses to serializable format
        for analysis in analyses:
            analysis_dict = {
                "name": analysis.name,
                "is_unused": analysis.is_unused,
                "is_async": analysis.is_async,
                "is_threaded": analysis.is_threaded,
                "line_count": analysis.line_count,
                "estimated_flops": analysis.estimated_flops,
                "energy_impact": analysis.energy_impact,
                "ai_explanation": analysis.ai_explanation,
                "ai_suggestion": analysis.ai_suggestion
            }
            result["analyses"].append(analysis_dict)
        
        # generate diff if requested
        if show_diff:
            unused_funcs = [a.name for a in analyses if a.is_unused]
            if unused_funcs:
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_code = f.read()
                cleaned_code = remove_dead_code_from_source(original_code, unused_funcs)
                diff = generate_diff(original_code, cleaned_code, file_info["filename"])
                result["diff"] = diff
        
        # safe remove if requested
        if safe_remove:
            unused_funcs = [a.name for a in analyses if a.is_unused]
            if unused_funcs:
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_code = f.read()
                cleaned_code = remove_dead_code_from_source(original_code, unused_funcs)
                cleaned_path = filepath + ".cleaned.py"
                with open(cleaned_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_code)
                result["cleaned_file_path"] = cleaned_path
        
        # rewrite inefficient code if requested
        if rewrite_inefficient and openai_key:
            result["rewritten_functions"] = []
            with open(filepath, 'r', encoding='utf-8') as f:
                original_code = f.read()
            for analysis in analyses:
                if analysis.estimated_flops > 50:  # threshold for inefficiency
                    try:
                        # extract function code
                        tree = ast.parse(original_code)
                        for node in tree.body:
                            if isinstance(node, ast.FunctionDef) and node.name == analysis.name:
                                function_code = ast.unparse(node)
                                improved_code = rewrite_inefficient_code(function_code, openai_key)
                                result["rewritten_functions"].append({
                                    "name": analysis.name,
                                    "original": function_code,
                                    "improved": improved_code
                                })
                                break
                    except Exception as e:
                        result["rewritten_functions"].append({
                            "name": analysis.name,
                            "error": str(e)
                        })
        
        # energy summary
        if track_energy:
            total_energy = energy_tracker.stop_tracking()
            result["total_energy"] = total_energy
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"analysis failed: {str(e)}")

@app.get("/files")
async def list_files():
    """list all uploaded files"""
    return {
        "files": [
            {
                "id": file_id,
                "filename": info["filename"],
                "size": info["size"]
            }
            for file_id, info in uploaded_files.items()
        ]
    }

@app.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """delete uploaded file"""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="file not found")
    
    file_info = uploaded_files[file_id]
    try:
        # remove file and its directory
        temp_dir = os.path.dirname(file_info["path"])
        shutil.rmtree(temp_dir)
        del uploaded_files[file_id]
        return {"message": "file deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"deletion failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 