import React, { useState, useEffect } from 'react';
import { Upload, FileText, Zap, Brain, Trash2, Download, Eye } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { DiffEditor } from 'react-diff-view';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [analysisOptions, setAnalysisOptions] = useState({
    openai_key: '',
    track_energy: false,
    show_diff: false,
    safe_remove: false,
    rewrite_inefficient: false
  });

  // fetch uploaded files on component mount
  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files`);
      setFiles(response.data.files);
    } catch (error) {
      console.error('error fetching files:', error);
    }
  };

  const onDrop = async (acceptedFiles) => {
    setLoading(true);
    try {
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        console.log('file uploaded:', response.data);
        await fetchFiles();
      }
    } catch (error) {
      console.error('upload error:', error);
      alert('upload failed: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/x-python': ['.py']
    },
    multiple: true
  });

  const analyzeFile = async (fileId) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze/${fileId}`, null, {
        params: analysisOptions
      });
      
      setAnalysis(response.data);
      setSelectedFile(files.find(f => f.id === fileId));
    } catch (error) {
      console.error('analysis error:', error);
      alert('analysis failed: ' + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteFile = async (fileId) => {
    try {
      await axios.delete(`${API_BASE_URL}/files/${fileId}`);
      await fetchFiles();
      if (selectedFile?.id === fileId) {
        setSelectedFile(null);
        setAnalysis(null);
      }
    } catch (error) {
      console.error('delete error:', error);
      alert('delete failed: ' + error.response?.data?.detail || error.message);
    }
  };

  const downloadCleanedFile = async () => {
    if (!analysis?.cleaned_file_path) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/download/${analysis.file_id}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedFile.filename}.cleaned.py`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('download error:', error);
      alert('download failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            enhanced code analyzer
          </h1>
          <p className="text-gray-600">
            analyze python codebases for dead code, energy impact, and ai-powered insights
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* left sidebar - file upload and list */}
          <div className="lg:col-span-1">
            {/* file upload */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                upload files
              </h2>
              
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                {isDragActive ? (
                  <p className="text-blue-600">drop the files here...</p>
                ) : (
                  <div>
                    <p className="text-gray-600 mb-2">drag & drop python files here</p>
                    <p className="text-sm text-gray-500">or click to select files</p>
                  </div>
                )}
              </div>
            </div>

            {/* uploaded files */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                uploaded files
              </h2>
              
              {files.length === 0 ? (
                <p className="text-gray-500 text-center py-4">no files uploaded yet</p>
              ) : (
                <div className="space-y-3">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedFile?.id === file.id
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedFile(file)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {file.filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024).toFixed(1)} kb
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteFile(file.id);
                          }}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* main content - analysis options and results */}
          <div className="lg:col-span-2">
            {selectedFile && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">
                  analyze: {selectedFile.filename}
                </h2>
                
                {/* analysis options */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      openai api key (for ai analysis)
                    </label>
                    <input
                      type="password"
                      value={analysisOptions.openai_key}
                      onChange={(e) => setAnalysisOptions({
                        ...analysisOptions,
                        openai_key: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="sk-..."
                    />
                  </div>
                  
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={analysisOptions.track_energy}
                        onChange={(e) => setAnalysisOptions({
                          ...analysisOptions,
                          track_energy: e.target.checked
                        })}
                        className="mr-2"
                      />
                      <Zap className="w-4 h-4 mr-2" />
                      track energy consumption
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={analysisOptions.show_diff}
                        onChange={(e) => setAnalysisOptions({
                          ...analysisOptions,
                          show_diff: e.target.checked
                        })}
                        className="mr-2"
                      />
                      <Eye className="w-4 h-4 mr-2" />
                      show code diff
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={analysisOptions.safe_remove}
                        onChange={(e) => setAnalysisOptions({
                          ...analysisOptions,
                          safe_remove: e.target.checked
                        })}
                        className="mr-2"
                      />
                      <Download className="w-4 h-4 mr-2" />
                      safe remove dead code
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={analysisOptions.rewrite_inefficient}
                        onChange={(e) => setAnalysisOptions({
                          ...analysisOptions,
                          rewrite_inefficient: e.target.checked
                        })}
                        className="mr-2"
                      />
                      <Brain className="w-4 h-4 mr-2" />
                      rewrite inefficient code
                    </label>
                  </div>
                </div>
                
                <button
                  onClick={() => analyzeFile(selectedFile.id)}
                  disabled={loading}
                  className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'analyzing...' : 'analyze file'}
                </button>
              </div>
            )}

            {/* analysis results */}
            {analysis && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">analysis results</h2>
                
                {/* summary stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">
                      {analysis.analyses.length}
                    </div>
                    <div className="text-sm text-gray-600">total functions</div>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {analysis.analyses.filter(a => a.is_unused).length}
                    </div>
                    <div className="text-sm text-red-600">unused functions</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {analysis.analyses.filter(a => a.is_async).length}
                    </div>
                    <div className="text-sm text-blue-600">async functions</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {analysis.total_energy ? `${analysis.total_energy.toFixed(4)}` : 'n/a'}
                    </div>
                    <div className="text-sm text-green-600">kg co2</div>
                  </div>
                </div>

                {/* function details */}
                <div className="space-y-4">
                  {analysis.analyses.map((func, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border ${
                        func.is_unused ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">{func.name}</h3>
                        <div className="flex space-x-2">
                          {func.is_unused && (
                            <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                              unused
                            </span>
                          )}
                          {func.is_async && (
                            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                              async
                            </span>
                          )}
                          {func.is_threaded && (
                            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                              threaded
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-600">
                        <div>lines: {func.line_count}</div>
                        <div>flops: {func.estimated_flops}</div>
                        <div>energy: {func.energy_impact?.toFixed(2) || 'n/a'} j</div>
                      </div>
                      
                      {func.ai_explanation && (
                        <div className="mt-3 p-3 bg-yellow-50 rounded border-l-4 border-yellow-400">
                          <p className="text-sm text-yellow-800">
                            <strong>ai explanation:</strong> {func.ai_explanation}
                          </p>
                          {func.ai_suggestion && (
                            <p className="text-sm text-yellow-700 mt-1">
                              <strong>suggestion:</strong> {func.ai_suggestion}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* code diff */}
                {analysis.diff && (
                  <div className="mt-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold">code diff (suggested deletions)</h3>
                      <button
                        onClick={() => setShowDiff(!showDiff)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        {showDiff ? 'hide diff' : 'show diff'}
                      </button>
                    </div>
                    
                    {showDiff && (
                      <div className="border rounded-lg overflow-hidden">
                        <pre className="bg-gray-900 text-green-400 p-4 text-sm overflow-x-auto">
                          {analysis.diff}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {/* rewritten functions */}
                {analysis.rewritten_functions && analysis.rewritten_functions.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">rewritten functions</h3>
                    <div className="space-y-4">
                      {analysis.rewritten_functions.map((rewrite, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <h4 className="font-semibold mb-2">{rewrite.name}</h4>
                          {rewrite.error ? (
                            <p className="text-red-600">{rewrite.error}</p>
                          ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h5 className="text-sm font-medium text-gray-700 mb-2">original</h5>
                                <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                                  {rewrite.original}
                                </pre>
                              </div>
                              <div>
                                <h5 className="text-sm font-medium text-gray-700 mb-2">improved</h5>
                                <pre className="bg-green-100 p-3 rounded text-sm overflow-x-auto">
                                  {rewrite.improved}
                                </pre>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* download cleaned file */}
                {analysis.cleaned_file_path && (
                  <div className="mt-6">
                    <button
                      onClick={downloadCleanedFile}
                      className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                    >
                      <Download className="w-4 h-4 inline mr-2" />
                      download cleaned file
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 