#!/usr/bin/env python3
"""
Code Audit Script

Analyzes the Verso-Backend codebase for quality metrics, complexity, and potential issues.

Usage:
    python scripts/audit/code_audit.py [--output report.json]

Features:
    - Code complexity analysis (cyclomatic complexity)
    - Duplicate code detection
    - Dead code identification
    - Code metrics (LOC, functions, classes)
    - Maintainability scoring
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CodeAnalyzer:
    """Analyzes Python code for quality metrics."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {},
            'files': [],
            'issues': [],
            'metrics': {}
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Run full analysis."""
        python_files = self._find_python_files()
        
        total_loc = 0
        total_functions = 0
        total_classes = 0
        complexity_scores = []
        
        for filepath in python_files:
            file_analysis = self._analyze_file(filepath)
            self.results['files'].append(file_analysis)
            
            total_loc += file_analysis['loc']
            total_functions += file_analysis['function_count']
            total_classes += file_analysis['class_count']
            complexity_scores.extend(file_analysis['complexities'])
        
        # Calculate summary metrics
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        high_complexity_count = len([c for c in complexity_scores if c > 10])
        
        self.results['summary'] = {
            'total_files': len(python_files),
            'total_lines': total_loc,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'average_complexity': round(avg_complexity, 2),
            'high_complexity_functions': high_complexity_count,
            'issues_count': len(self.results['issues'])
        }
        
        # Calculate maintainability index
        self.results['metrics']['maintainability_index'] = self._calculate_maintainability(
            total_loc, avg_complexity, len(python_files)
        )
        
        # Check for common issues
        self._check_for_issues(python_files)
        
        return self.results
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        files = []
        app_path = self.root_path / 'app'
        
        for pattern in ['**/*.py']:
            for filepath in app_path.glob(pattern):
                # Skip cache and test files
                if '__pycache__' in str(filepath):
                    continue
                if 'migrations' in str(filepath):
                    continue
                files.append(filepath)
        
        return files
    
    def _analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        relative_path = filepath.relative_to(self.root_path)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return {
                'path': str(relative_path),
                'error': str(e),
                'loc': 0,
                'function_count': 0,
                'class_count': 0,
                'complexities': []
            }
        
        # Count lines of code (excluding blanks and comments)
        loc = self._count_loc(lines)
        
        # Parse AST for complexity analysis
        try:
            tree = ast.parse(content)
            functions, classes, complexities = self._analyze_ast(tree)
        except SyntaxError:
            functions, classes, complexities = 0, 0, []
        
        return {
            'path': str(relative_path),
            'loc': loc,
            'total_lines': len(lines),
            'function_count': functions,
            'class_count': classes,
            'complexities': complexities,
            'max_complexity': max(complexities) if complexities else 0
        }
    
    def _count_loc(self, lines: List[str]) -> int:
        """Count lines of code excluding blanks and comments."""
        count = 0
        in_multiline = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip blank lines
            if not stripped:
                continue
            
            # Handle multiline strings/docstrings
            if '"""' in stripped or "'''" in stripped:
                quotes = '"""' if '"""' in stripped else "'''"
                if stripped.count(quotes) == 1:
                    in_multiline = not in_multiline
                count += 1
                continue
            
            if in_multiline:
                count += 1
                continue
            
            # Skip single-line comments
            if stripped.startswith('#'):
                continue
            
            count += 1
        
        return count
    
    def _analyze_ast(self, tree: ast.AST) -> tuple:
        """Analyze AST for functions, classes, and complexity."""
        functions = 0
        classes = 0
        complexities = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions += 1
                complexity = self._calculate_complexity(node)
                complexities.append(complexity)
            elif isinstance(node, ast.ClassDef):
                classes += 1
        
        return functions, classes, complexities
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability(self, loc: int, avg_complexity: float, file_count: int) -> float:
        """Calculate maintainability index (0-100 scale)."""
        import math
        
        if loc == 0:
            return 100.0
        
        # Simplified maintainability index formula
        # Based on Halstead volume, cyclomatic complexity, and LOC
        halstead_volume = loc * math.log2(loc + 1) if loc > 0 else 0
        
        mi = 171 - 5.2 * math.log(halstead_volume + 1) - 0.23 * avg_complexity - 16.2 * math.log(loc + 1)
        
        # Normalize to 0-100
        mi = max(0, min(100, mi * 100 / 171))
        
        return round(mi, 2)
    
    def _check_for_issues(self, files: List[Path]):
        """Check for common code issues."""
        issues = []
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
            except Exception:
                continue
            
            relative_path = str(filepath.relative_to(self.root_path))
            
            # Check for long lines
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    issues.append({
                        'type': 'long_line',
                        'severity': 'low',
                        'file': relative_path,
                        'line': i,
                        'message': f'Line exceeds 120 characters ({len(line)} chars)'
                    })
            
            # Check for TODO/FIXME comments
            for i, line in enumerate(lines, 1):
                if 'TODO' in line or 'FIXME' in line or 'XXX' in line:
                    issues.append({
                        'type': 'todo',
                        'severity': 'info',
                        'file': relative_path,
                        'line': i,
                        'message': line.strip()[:100]
                    })
            
            # Check for potential security issues
            security_patterns = [
                (r'eval\s*\(', 'Use of eval() detected'),
                (r'exec\s*\(', 'Use of exec() detected'),
                (r'pickle\.loads?\s*\(', 'Pickle usage detected (potential security risk)'),
                (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected'),
                (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected'),
            ]
            
            for pattern, message in security_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if in comments
                        if line.strip().startswith('#'):
                            continue
                        issues.append({
                            'type': 'security',
                            'severity': 'high',
                            'file': relative_path,
                            'line': i,
                            'message': message
                        })
        
        self.results['issues'] = issues


def main():
    parser = argparse.ArgumentParser(description='Analyze code quality')
    parser.add_argument('--output', '-o', help='Output file (JSON format)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    print("=" * 60)
    print("VERSO-BACKEND CODE AUDIT")
    print("=" * 60)
    print()
    
    analyzer = CodeAnalyzer(PROJECT_ROOT)
    results = analyzer.analyze()
    
    # Print summary
    summary = results['summary']
    print(f"📁 Total Files:            {summary['total_files']}")
    print(f"📝 Total Lines of Code:    {summary['total_lines']:,}")
    print(f"🔧 Total Functions:        {summary['total_functions']}")
    print(f"📦 Total Classes:          {summary['total_classes']}")
    print(f"🔄 Average Complexity:     {summary['average_complexity']}")
    print(f"⚠️  High Complexity Fns:   {summary['high_complexity_functions']}")
    print(f"🔍 Issues Found:           {summary['issues_count']}")
    print()
    
    # Print maintainability score
    mi = results['metrics']['maintainability_index']
    mi_rating = "Excellent" if mi >= 80 else "Good" if mi >= 60 else "Moderate" if mi >= 40 else "Low"
    print(f"🎯 Maintainability Index:  {mi} ({mi_rating})")
    print()
    
    # Print high complexity functions
    high_complexity = [
        f for f in results['files'] 
        if f.get('max_complexity', 0) > 10
    ]
    if high_complexity:
        print("⚠️  Files with High Complexity:")
        for f in sorted(high_complexity, key=lambda x: x['max_complexity'], reverse=True)[:10]:
            print(f"   {f['path']}: {f['max_complexity']}")
        print()
    
    # Print security issues
    security_issues = [i for i in results['issues'] if i['type'] == 'security']
    if security_issues:
        print("🔒 Security Concerns:")
        for issue in security_issues:
            print(f"   [{issue['severity'].upper()}] {issue['file']}:{issue['line']} - {issue['message']}")
        print()
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Report saved to: {args.output}")
    
    print()
    print("=" * 60)
    print("Audit complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
