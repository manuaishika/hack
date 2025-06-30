import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

interface FunctionAnalysis {
  name: string;
  is_unused: boolean;
  is_async: boolean;
  is_threaded: boolean;
  line_count: number;
  estimated_flops: number;
  energy_impact: number;
  ai_explanation?: string;
  ai_suggestion?: string;
}

interface AnalysisResult {
  file_id: number;
  filename: string;
  analyses: FunctionAnalysis[];
  total_energy?: number;
}

class EcosiftCodeCleaner {
  private context: vscode.ExtensionContext;
  private decorationType: vscode.TextEditorDecorationType;
  private diagnosticCollection: vscode.DiagnosticCollection;
  private currentAnalysis: Map<string, AnalysisResult> = new Map();

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    
    // create decoration type for dead code highlighting
    this.decorationType = vscode.window.createTextEditorDecorationType({
      backgroundColor: new vscode.ThemeColor('editorWarning.foreground'),
      border: '1px solid',
      borderColor: new vscode.ThemeColor('editorWarning.foreground'),
      overviewRulerColor: new vscode.ThemeColor('editorWarning.foreground'),
      overviewRulerLane: vscode.OverviewRulerLane.Right,
      after: {
        contentText: ' 🚨 dead code',
        color: new vscode.ThemeColor('editorWarning.foreground'),
        margin: '0 0 0 1em'
      }
    });

    // create diagnostic collection for warnings
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection('ecosift');
  }

  public activate(): void {
    // register commands
    let disposable = vscode.commands.registerCommand('ecosift.runAnalysis', () => {
      this.runAnalysis();
    });

    let summaryDisposable = vscode.commands.registerCommand('ecosift.showDeadCodeSummary', () => {
      this.showDeadCodeSummary();
    });

    // register file save listener
    let saveDisposable = vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId === 'python' && this.getConfig('autoAnalyze')) {
        this.analyzeFile(document.uri.fsPath);
      }
    });

    // register hover provider for tooltips
    let hoverDisposable = vscode.languages.registerHoverProvider('python', {
      provideHover: (document, position, token) => {
        return this.provideHover(document, position);
      }
    });

    this.context.subscriptions.push(
      disposable,
      summaryDisposable,
      saveDisposable,
      hoverDisposable,
      this.decorationType,
      this.diagnosticCollection
    );
  }

  private getConfig(key: string): any {
    return vscode.workspace.getConfiguration('ecosift').get(key);
  }

  private async runAnalysis(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'python') {
      vscode.window.showWarningMessage('please open a python file to analyze');
      return;
    }

    const filePath = editor.document.uri.fsPath;
    await this.analyzeFile(filePath);
  }

  private async analyzeFile(filePath: string): Promise<void> {
    try {
      vscode.window.showInformationMessage('analyzing file for dead code...');
      
      const result = await this.runPythonAnalyzer(filePath);
      if (result) {
        this.currentAnalysis.set(filePath, result);
        this.updateDecorations(filePath, result);
        this.updateDiagnostics(filePath, result);
        
        const deadCodeCount = result.analyses.filter(f => f.is_unused).length;
        if (deadCodeCount > 0) {
          vscode.window.showInformationMessage(
            `found ${deadCodeCount} unused functions in ${path.basename(filePath)}`
          );
        } else {
          vscode.window.showInformationMessage('no dead code found! 🎉');
        }
      }
    } catch (error) {
      vscode.window.showErrorMessage(`analysis failed: ${error}`);
    }
  }

  private async runPythonAnalyzer(filePath: string): Promise<AnalysisResult | null> {
    return new Promise((resolve, reject) => {
      const pythonPath = this.getConfig('pythonPath');
      const analyzerPath = this.getConfig('analyzerPath');
      
      // resolve relative paths
      const resolvedAnalyzerPath = path.isAbsolute(analyzerPath) 
        ? analyzerPath 
        : path.join(this.context.extensionPath, analyzerPath);

      if (!fs.existsSync(resolvedAnalyzerPath)) {
        reject(new Error(`analyzer not found at: ${resolvedAnalyzerPath}`));
        return;
      }

      const args = [resolvedAnalyzerPath, filePath];
      
      const child = child_process.spawn(pythonPath, args, {
        cwd: path.dirname(resolvedAnalyzerPath)
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          try {
            // parse the output - look for json in the output
            const jsonMatch = stdout.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              const result = JSON.parse(jsonMatch[0]);
              resolve(result);
            } else {
              // fallback: parse the text output
              const result = this.parseTextOutput(stdout, filePath);
              resolve(result);
            }
          } catch (error) {
            reject(new Error(`failed to parse output: ${error}`));
          }
        } else {
          reject(new Error(`analyzer failed with code ${code}: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`failed to start analyzer: ${error.message}`));
      });
    });
  }

  private parseTextOutput(output: string, filePath: string): AnalysisResult {
    // parse the text output from the enhanced analyzer
    const lines = output.split('\n');
    const analyses: FunctionAnalysis[] = [];
    
    let inUnusedSection = false;
    let currentFunction: Partial<FunctionAnalysis> = {};

    for (const line of lines) {
      if (line.includes('unused/dead functions detected:')) {
        inUnusedSection = true;
        continue;
      }

      if (inUnusedSection && line.startsWith('function:')) {
        if (currentFunction.name) {
          analyses.push(currentFunction as FunctionAnalysis);
        }
        currentFunction = {
          name: line.split('function:')[1].trim(),
          is_unused: true,
          is_async: false,
          is_threaded: false,
          line_count: 0,
          estimated_flops: 0,
          energy_impact: 0
        };
      }

      if (currentFunction.name) {
        if (line.includes('lines:')) {
          currentFunction.line_count = parseInt(line.split('lines:')[1].trim()) || 0;
        } else if (line.includes('estimated flops:')) {
          currentFunction.estimated_flops = parseInt(line.split('estimated flops:')[1].trim()) || 0;
        } else if (line.includes('energy impact:')) {
          const energyMatch = line.match(/energy impact: ([\d.]+)/);
          if (energyMatch) {
            currentFunction.energy_impact = parseFloat(energyMatch[1]);
          }
        } else if (line.includes('⚡ async function')) {
          currentFunction.is_async = true;
        } else if (line.includes('🔄 threaded function')) {
          currentFunction.is_threaded = true;
        }
      }
    }

    // add the last function
    if (currentFunction.name) {
      analyses.push(currentFunction as FunctionAnalysis);
    }

    return {
      file_id: 1,
      filename: path.basename(filePath),
      analyses: analyses
    };
  }

  private updateDecorations(filePath: string, result: AnalysisResult): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.uri.fsPath !== filePath) {
      return;
    }

    const decorations: vscode.DecorationOptions[] = [];
    const unusedFunctions = result.analyses.filter(f => f.is_unused);

    for (const func of unusedFunctions) {
      const functionRange = this.findFunctionRange(editor.document, func.name);
      if (functionRange) {
        decorations.push({
          range: functionRange,
          hoverMessage: this.createHoverMessage(func)
        });
      }
    }

    editor.setDecorations(this.decorationType, decorations);
  }

  private updateDiagnostics(filePath: string, result: AnalysisResult): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.uri.fsPath !== filePath) {
      return;
    }

    const diagnostics: vscode.Diagnostic[] = [];
    const unusedFunctions = result.analyses.filter(f => f.is_unused);

    for (const func of unusedFunctions) {
      const functionRange = this.findFunctionRange(editor.document, func.name);
      if (functionRange) {
        const diagnostic = new vscode.Diagnostic(
          functionRange,
          `unused function '${func.name}' (${func.line_count} lines, ${func.estimated_flops} flops)`,
          vscode.DiagnosticSeverity.Warning
        );
        diagnostic.source = 'ecosift';
        diagnostics.push(diagnostic);
      }
    }

    this.diagnosticCollection.set(editor.document.uri, diagnostics);
  }

  private findFunctionRange(document: vscode.TextDocument, functionName: string): vscode.Range | null {
    const text = document.getText();
    const functionRegex = new RegExp(`def\\s+${functionName}\\s*\\([^)]*\\)\\s*:`, 'g');
    const match = functionRegex.exec(text);
    
    if (match) {
      const startPos = document.positionAt(match.index);
      const endPos = document.positionAt(match.index + match[0].length);
      return new vscode.Range(startPos, endPos);
    }
    
    return null;
  }

  private createHoverMessage(func: FunctionAnalysis): vscode.MarkdownString {
    const message = new vscode.MarkdownString();
    message.appendMarkdown(`**${func.name}** - Dead Code\n\n`);
    message.appendMarkdown(`- **lines:** ${func.line_count}\n`);
    message.appendMarkdown(`- **estimated flops:** ${func.estimated_flops}\n`);
    message.appendMarkdown(`- **energy impact:** ${func.energy_impact.toFixed(2)} joules\n`);
    
    if (func.is_async) {
      message.appendMarkdown(`- **type:** async function\n`);
    }
    if (func.is_threaded) {
      message.appendMarkdown(`- **type:** threaded function\n`);
    }
    
    if (func.ai_explanation) {
      message.appendMarkdown(`\n**ai explanation:** ${func.ai_explanation}\n`);
    }
    if (func.ai_suggestion) {
      message.appendMarkdown(`\n**suggestion:** ${func.ai_suggestion}\n`);
    }
    
    return message;
  }

  private provideHover(document: vscode.TextDocument, position: vscode.Position): vscode.Hover | null {
    const filePath = document.uri.fsPath;
    const result = this.currentAnalysis.get(filePath);
    
    if (!result) {
      return null;
    }

    // find function at cursor position
    const wordRange = document.getWordRangeAtPosition(position);
    if (!wordRange) {
      return null;
    }

    const word = document.getText(wordRange);
    const func = result.analyses.find(f => f.name === word);
    
    if (func && func.is_unused) {
      return new vscode.Hover(this.createHoverMessage(func));
    }
    
    return null;
  }

  private showDeadCodeSummary(): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'python') {
      vscode.window.showWarningMessage('please open a python file');
      return;
    }

    const filePath = editor.document.uri.fsPath;
    const result = this.currentAnalysis.get(filePath);
    
    if (!result) {
      vscode.window.showInformationMessage('no analysis data available. run analysis first.');
      return;
    }

    const unusedFunctions = result.analyses.filter(f => f.is_unused);
    
    if (unusedFunctions.length === 0) {
      vscode.window.showInformationMessage('no dead code found! 🎉');
      return;
    }

    // create summary message
    let summary = `**dead code summary for ${path.basename(filePath)}**\n\n`;
    summary += `found ${unusedFunctions.length} unused functions:\n\n`;
    
    for (const func of unusedFunctions) {
      summary += `- **${func.name}**: ${func.line_count} lines, ${func.estimated_flops} flops, ${func.energy_impact.toFixed(2)} joules\n`;
    }
    
    const totalLines = unusedFunctions.reduce((sum, f) => sum + f.line_count, 0);
    const totalFlops = unusedFunctions.reduce((sum, f) => sum + f.estimated_flops, 0);
    const totalEnergy = unusedFunctions.reduce((sum, f) => sum + f.energy_impact, 0);
    
    summary += `\n**totals:**\n`;
    summary += `- lines: ${totalLines}\n`;
    summary += `- flops: ${totalFlops}\n`;
    summary += `- energy: ${totalEnergy.toFixed(2)} joules\n`;
    
    // show in information message
    vscode.window.showInformationMessage(summary);
  }

  public dispose(): void {
    this.decorationType.dispose();
    this.diagnosticCollection.dispose();
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const ecosift = new EcosiftCodeCleaner(context);
  ecosift.activate();
  
  context.subscriptions.push(ecosift);
  
  console.log('ecosift code cleaner extension is now active!');
}

export function deactivate(): void {
  console.log('ecosift code cleaner extension is now deactivated');
} 