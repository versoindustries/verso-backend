#!/usr/bin/env python3
"""
Dependency Audit Script

Analyzes project dependencies for:
- Security vulnerabilities
- License compatibility
- Unused dependencies
- Outdated packages

Usage:
    python scripts/audit/dependency_audit.py [--output report.json]
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

PROJECT_ROOT = Path(__file__).parent.parent.parent


class DependencyAuditor:
    """Analyzes project dependencies."""
    
    # License compatibility matrix
    COMPATIBLE_LICENSES = {
        'MIT', 'BSD', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'Apache 2.0',
        'ISC', 'PSF', 'Python-2.0', 'LGPL', 'LGPL-2.1', 'LGPL-3.0',
        'MPL-2.0', 'Unlicense', 'CC0-1.0', 'WTFPL', 'Zlib'
    }
    
    COPYLEFT_LICENSES = {
        'GPL', 'GPL-2.0', 'GPL-3.0', 'AGPL', 'AGPL-3.0'
    }
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.requirements_file = root_path / 'requirements.txt'
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'dependencies': [],
            'security_issues': [],
            'license_issues': [],
            'unused_candidates': [],
            'summary': {}
        }
    
    def audit(self) -> Dict[str, Any]:
        """Run full dependency audit."""
        print("Parsing requirements.txt...")
        deps = self._parse_requirements()
        
        print("Checking for security vulnerabilities...")
        self._check_vulnerabilities()
        
        print("Analyzing licenses...")
        self._analyze_licenses(deps)
        
        print("Identifying potentially unused dependencies...")
        self._find_unused(deps)
        
        # Summary
        self.results['summary'] = {
            'total_dependencies': len(deps),
            'security_issues': len(self.results['security_issues']),
            'license_issues': len(self.results['license_issues']),
            'unused_candidates': len(self.results['unused_candidates'])
        }
        
        return self.results
    
    def _parse_requirements(self) -> List[Dict[str, str]]:
        """Parse requirements.txt file."""
        deps = []
        
        if not self.requirements_file.exists():
            print(f"Warning: {self.requirements_file} not found")
            return deps
        
        with open(self.requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse package name and version
                match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!~]+.*)?$', line)
                if match:
                    name = match.group(1)
                    version = match.group(2) or ''
                    deps.append({
                        'name': name,
                        'version_spec': version.strip(),
                        'line': line
                    })
        
        self.results['dependencies'] = deps
        return deps
    
    def _check_vulnerabilities(self):
        """Check for known vulnerabilities using pip-audit."""
        try:
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True,
                cwd=self.root_path
            )
            
            if result.stdout:
                try:
                    vuln_data = json.loads(result.stdout)
                    for vuln in vuln_data.get('dependencies', []):
                        if vuln.get('vulns'):
                            for v in vuln['vulns']:
                                self.results['security_issues'].append({
                                    'package': vuln['name'],
                                    'version': vuln['version'],
                                    'vulnerability': v.get('id', 'Unknown'),
                                    'description': v.get('description', ''),
                                    'fix_versions': v.get('fix_versions', [])
                                })
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            print("  pip-audit not installed, skipping vulnerability check")
    
    def _analyze_licenses(self, deps: List[Dict[str, str]]):
        """Analyze licenses of dependencies."""
        try:
            result = subprocess.run(
                ['pip', 'show'] + [d['name'] for d in deps[:50]],  # Limit for performance
                capture_output=True,
                text=True
            )
            
            # Parse pip show output
            current_pkg = None
            for line in result.stdout.split('\n'):
                if line.startswith('Name:'):
                    current_pkg = line.split(':', 1)[1].strip()
                elif line.startswith('License:') and current_pkg:
                    license_name = line.split(':', 1)[1].strip()
                    
                    # Update dependency info
                    for dep in self.results['dependencies']:
                        if dep['name'].lower() == current_pkg.lower():
                            dep['license'] = license_name
                            
                            # Check license compatibility
                            if license_name and license_name != 'UNKNOWN':
                                is_compatible = any(
                                    lic in license_name 
                                    for lic in self.COMPATIBLE_LICENSES
                                )
                                is_copyleft = any(
                                    lic in license_name 
                                    for lic in self.COPYLEFT_LICENSES
                                )
                                
                                if is_copyleft:
                                    self.results['license_issues'].append({
                                        'package': current_pkg,
                                        'license': license_name,
                                        'issue': 'Copyleft license - may require open-sourcing derived works'
                                    })
                                elif not is_compatible and license_name != 'UNKNOWN':
                                    self.results['license_issues'].append({
                                        'package': current_pkg,
                                        'license': license_name,
                                        'issue': 'Unknown license compatibility - review required'
                                    })
                            break
        except Exception as e:
            print(f"  License analysis error: {e}")
    
    def _find_unused(self, deps: List[Dict[str, str]]):
        """Find potentially unused dependencies by checking imports."""
        # Get all Python imports in the codebase
        app_path = self.root_path / 'app'
        imports = set()
        
        for py_file in app_path.glob('**/*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find import statements
                import_patterns = [
                    r'^import\s+(\w+)',
                    r'^from\s+(\w+)',
                ]
                
                for pattern in import_patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        imports.add(match.group(1).lower())
            except Exception:
                continue
        
        # Map package names to import names (common mappings)
        package_to_import = {
            'flask-login': 'flask_login',
            'flask-mail': 'flask_mail',
            'flask-migrate': 'flask_migrate',
            'flask-wtf': 'flask_wtf',
            'flask-babel': 'flask_babel',
            'flask-caching': 'flask_caching',
            'sqlalchemy': 'sqlalchemy',
            'pillow': 'pil',
            'python-dotenv': 'dotenv',
            'pyjwt': 'jwt',
            'beautifulsoup4': 'bs4',
            'pyotp': 'pyotp',
        }
        
        for dep in deps:
            pkg_name = dep['name'].lower()
            import_name = package_to_import.get(pkg_name, pkg_name.replace('-', '_'))
            
            if import_name not in imports and pkg_name not in imports:
                # Additional check for packages that might be used indirectly
                if pkg_name not in ['gunicorn', 'psycopg2-binary', 'redis', 'celery']:
                    self.results['unused_candidates'].append({
                        'package': dep['name'],
                        'note': 'Not directly imported - may be used as dependency of another package'
                    })


def main():
    parser = argparse.ArgumentParser(description='Audit project dependencies')
    parser.add_argument('--output', '-o', help='Output file (JSON format)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("VERSO-BACKEND DEPENDENCY AUDIT")
    print("=" * 60)
    print()
    
    auditor = DependencyAuditor(PROJECT_ROOT)
    results = auditor.audit()
    
    print()
    
    # Print summary
    summary = results['summary']
    print(f"📦 Total Dependencies:     {summary['total_dependencies']}")
    print(f"🔒 Security Issues:        {summary['security_issues']}")
    print(f"📜 License Issues:         {summary['license_issues']}")
    print(f"❓ Unused Candidates:      {summary['unused_candidates']}")
    print()
    
    # Print security issues
    if results['security_issues']:
        print("🔒 SECURITY VULNERABILITIES:")
        for issue in results['security_issues']:
            print(f"   [{issue['vulnerability']}] {issue['package']} {issue['version']}")
            if issue.get('fix_versions'):
                print(f"      Fix: upgrade to {', '.join(issue['fix_versions'])}")
        print()
    
    # Print license issues
    if results['license_issues']:
        print("📜 LICENSE CONCERNS:")
        for issue in results['license_issues']:
            print(f"   {issue['package']}: {issue['license']}")
            print(f"      {issue['issue']}")
        print()
    
    # Print unused candidates
    if results['unused_candidates']:
        print("❓ POTENTIALLY UNUSED (review before removing):")
        for dep in results['unused_candidates'][:10]:
            print(f"   {dep['package']}")
        if len(results['unused_candidates']) > 10:
            print(f"   ... and {len(results['unused_candidates']) - 10} more")
        print()
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Report saved to: {args.output}")
    
    print()
    print("=" * 60)
    print("Dependency audit complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
