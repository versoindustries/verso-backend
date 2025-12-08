#!/usr/bin/env python3
"""
React Migration Template Auditor

This script analyzes all Jinja2 templates and generates a migration plan
for converting them to use React components within the Islands Architecture.

Usage:
    python scripts/react_migration/audit_templates.py

Output:
    - scripts/react_migration/template_audit.json - Full audit data
    - scripts/react_migration/migration_plan.md - Human-readable plan
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from collections import defaultdict

# Configuration
TEMPLATES_DIR = Path("app/templates")
OUTPUT_DIR = Path("scripts/react_migration")

# Pattern detection for complexity analysis
PATTERNS = {
    "jquery": [
        r"\$\(", r"jQuery\(", r"\.ajax\(", r"\.on\(", r"\.click\(",
        r"\.submit\(", r"\.ready\(", r"\.each\("
    ],
    "chart_js": [r"new Chart\(", r"Chart\.", r"chartjs"],
    "datatable": [r"\.DataTable\(", r"DataTable", r"datatables"],
    "fullcalendar": [r"FullCalendar", r"\.fullCalendar\("],
    "inline_script": [r"<script>", r"<script\s"],
    "fetch_api": [r"fetch\(", r"\.then\("],
    "form_elements": [
        r"<form", r"<input", r"<select", r"<textarea", r"<button"
    ],
    "dynamic_content": [
        r"onclick=", r"onsubmit=", r"onchange=", r"addEventListener"
    ],
    "react_component": [r"data-react-component"],
    "modal_dialog": [r"modal", r"dialog", r"lightbox"],
    "tabs_accordion": [r"tab-", r"accordion", r"collapsible"],
    "drag_drop": [r"draggable", r"sortable", r"drag"],
    "infinite_scroll": [r"load-more", r"infinite", r"pagination"]
}

# Priority categories
CATEGORY_PRIORITY = {
    "admin": 2,
    "shop": 1,
    "UserDashboard": 1,
    "blog": 3,
    "employee": 2,
    "booking": 1,
    "forms": 2,
    "messaging": 2,
    "onboarding": 2,
    "notifications": 2,
    "surveys": 3,
    "email": 4,
    "account": 3,
    "root": 2,  # Top-level templates
}

# Component suggestions based on patterns
COMPONENT_SUGGESTIONS = {
    "chart_js": ["RevenueChart", "LeadsChart", "AnalyticsChart", "FunnelChart"],
    "datatable": ["DataTable", "SortableTable", "PaginatedList"],
    "fullcalendar": ["Calendar", "ScheduleView", "AvailabilityCalendar"],
    "form_elements": ["Form", "FormField", "FormWizard", "DynamicForm"],
    "modal_dialog": ["Modal", "ConfirmDialog", "Drawer", "Sheet"],
    "tabs_accordion": ["Tabs", "TabPanel", "Accordion", "Collapsible"],
    "drag_drop": ["DragDropList", "KanbanBoard", "Sortable"],
    "infinite_scroll": ["InfiniteList", "LoadMoreButton", "Pagination"],
}


@dataclass
class TemplateAnalysis:
    """Analysis result for a single template."""
    path: str
    relative_path: str
    category: str
    line_count: int
    size_bytes: int
    extends_base: bool
    has_jquery: bool
    has_charts: bool
    has_datatables: bool
    has_calendar: bool
    has_inline_scripts: bool
    has_forms: bool
    has_dynamic_content: bool
    has_react_already: bool
    complexity_score: int
    migration_priority: int
    suggested_components: List[str] = field(default_factory=list)
    detected_patterns: Dict[str, int] = field(default_factory=dict)
    blocks_used: List[str] = field(default_factory=list)
    jinja_variables: List[str] = field(default_factory=list)


def count_pattern_matches(content: str, patterns: List[str]) -> int:
    """Count total matches for a list of regex patterns."""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return count


def extract_jinja_variables(content: str) -> List[str]:
    """Extract Jinja2 variable names from template."""
    # Match {{ variable }} and {{ variable.property }}
    matches = re.findall(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)", content)
    # Get unique root variables
    roots = set()
    for match in matches:
        root = match.split(".")[0]
        if root not in ("url_for", "csrf_token", "get_flashed_messages", 
                       "current_user", "config", "request", "session"):
            roots.add(root)
    return sorted(list(roots))


def extract_blocks(content: str) -> List[str]:
    """Extract Jinja2 block names from template."""
    matches = re.findall(r"\{%\s*block\s+([a-zA-Z_]+)", content)
    return list(set(matches))


def calculate_complexity(analysis: TemplateAnalysis) -> int:
    """Calculate a complexity score (1-10) for migration difficulty."""
    score = 1
    
    if analysis.line_count > 500:
        score += 3
    elif analysis.line_count > 200:
        score += 2
    elif analysis.line_count > 100:
        score += 1
    
    if analysis.has_jquery:
        score += 2
    if analysis.has_charts:
        score += 2
    if analysis.has_datatables:
        score += 2
    if analysis.has_calendar:
        score += 3
    if analysis.has_dynamic_content:
        score += 1
    if analysis.has_inline_scripts:
        score += 1
    
    # Cap at 10
    return min(score, 10)


def calculate_priority(analysis: TemplateAnalysis) -> int:
    """Calculate migration priority (1=highest, 5=lowest)."""
    # Start with category priority
    priority = CATEGORY_PRIORITY.get(analysis.category, 3)
    
    # Adjust based on user-facing importance
    if "dashboard" in analysis.path.lower():
        priority = min(priority, 1)
    if "checkout" in analysis.path.lower() or "cart" in analysis.path.lower():
        priority = min(priority, 1)
    if "index" in analysis.path.lower() and analysis.category == "root":
        priority = min(priority, 1)
    
    # Already has React - lower priority (already started)
    if analysis.has_react_already:
        priority = max(priority - 1, 1)
    
    return priority


def suggest_components(analysis: TemplateAnalysis) -> List[str]:
    """Suggest React components based on detected patterns."""
    suggestions = set()
    
    for pattern_key, patterns in analysis.detected_patterns.items():
        if patterns > 0 and pattern_key in COMPONENT_SUGGESTIONS:
            suggestions.update(COMPONENT_SUGGESTIONS[pattern_key][:2])
    
    # Add general suggestions based on template type
    if "form" in analysis.path.lower() or analysis.has_forms:
        suggestions.add("ReactForm")
    if "list" in analysis.path.lower():
        suggestions.add("DataTable")
    if "dashboard" in analysis.path.lower():
        suggestions.update(["KPICard", "Chart"])
    
    return sorted(list(suggestions))


def analyze_template(template_path: Path) -> TemplateAnalysis:
    """Analyze a single template file."""
    relative = str(template_path.relative_to(TEMPLATES_DIR))
    
    # Determine category
    parts = relative.split(os.sep)
    if len(parts) > 1:
        category = parts[0]
    else:
        category = "root"
    
    # Read file
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    size_bytes = template_path.stat().st_size
    line_count = content.count("\n") + 1
    
    # Detect patterns
    detected_patterns = {}
    for name, patterns in PATTERNS.items():
        detected_patterns[name] = count_pattern_matches(content, patterns)
    
    # Check for extends
    extends_base = bool(re.search(r'\{%\s*extends\s+["\']base\.html', content))
    
    # Create analysis
    analysis = TemplateAnalysis(
        path=str(template_path),
        relative_path=relative,
        category=category,
        line_count=line_count,
        size_bytes=size_bytes,
        extends_base=extends_base,
        has_jquery=detected_patterns.get("jquery", 0) > 0,
        has_charts=detected_patterns.get("chart_js", 0) > 0,
        has_datatables=detected_patterns.get("datatable", 0) > 0,
        has_calendar=detected_patterns.get("fullcalendar", 0) > 0,
        has_inline_scripts=detected_patterns.get("inline_script", 0) > 0,
        has_forms=detected_patterns.get("form_elements", 0) > 0,
        has_dynamic_content=detected_patterns.get("dynamic_content", 0) > 0,
        has_react_already=detected_patterns.get("react_component", 0) > 0,
        complexity_score=0,  # Will be calculated
        migration_priority=0,  # Will be calculated
        detected_patterns=detected_patterns,
        blocks_used=extract_blocks(content),
        jinja_variables=extract_jinja_variables(content),
    )
    
    analysis.complexity_score = calculate_complexity(analysis)
    analysis.migration_priority = calculate_priority(analysis)
    analysis.suggested_components = suggest_components(analysis)
    
    return analysis


def generate_migration_plan(analyses: List[TemplateAnalysis]) -> str:
    """Generate a human-readable migration plan."""
    
    # Group by priority
    by_priority = defaultdict(list)
    for a in analyses:
        by_priority[a.migration_priority].append(a)
    
    # Group by category
    by_category = defaultdict(list)
    for a in analyses:
        by_category[a.category].append(a)
    
    # Statistics
    total = len(analyses)
    with_jquery = sum(1 for a in analyses if a.has_jquery)
    with_charts = sum(1 for a in analyses if a.has_charts)
    with_datatables = sum(1 for a in analyses if a.has_datatables)
    with_calendar = sum(1 for a in analyses if a.has_calendar)
    with_react = sum(1 for a in analyses if a.has_react_already)
    
    # Collect all suggested components
    all_components = set()
    for a in analyses:
        all_components.update(a.suggested_components)
    
    # Build markdown report
    md = []
    md.append("# React Migration Plan - Template Audit Report")
    md.append("")
    md.append(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}")
    md.append(f"**Total Templates:** {total}")
    md.append("")
    
    md.append("## Summary Statistics")
    md.append("")
    md.append("| Metric | Count | Percentage |")
    md.append("|--------|-------|------------|")
    md.append(f"| Templates with jQuery | {with_jquery} | {with_jquery*100//total}% |")
    md.append(f"| Templates with Chart.js | {with_charts} | {with_charts*100//total}% |")
    md.append(f"| Templates with DataTables | {with_datatables} | {with_datatables*100//total}% |")
    md.append(f"| Templates with FullCalendar | {with_calendar} | {with_calendar*100//total}% |")
    md.append(f"| Templates already using React | {with_react} | {with_react*100//total}% |")
    md.append("")
    
    md.append("## Suggested React Components")
    md.append("")
    md.append("Based on pattern analysis, the following React components should be created:")
    md.append("")
    for comp in sorted(all_components):
        md.append(f"- `{comp}`")
    md.append("")
    
    md.append("## Migration Phases by Priority")
    md.append("")
    
    priority_names = {
        1: "Phase 1: Critical (High-Traffic/Revenue Impact)",
        2: "Phase 2: Important (Admin/Employee Tools)",
        3: "Phase 3: Standard (Content/Utilities)",
        4: "Phase 4: Low (Email/Background)",
        5: "Phase 5: Minimal (Static Content)",
    }
    
    for priority in sorted(by_priority.keys()):
        templates = by_priority[priority]
        md.append(f"### {priority_names.get(priority, f'Priority {priority}')}")
        md.append("")
        md.append(f"**{len(templates)} templates**")
        md.append("")
        md.append("| Template | Lines | Complexity | Components Needed |")
        md.append("|----------|-------|------------|-------------------|")
        
        for t in sorted(templates, key=lambda x: -x.complexity_score):
            comps = ", ".join(t.suggested_components[:3]) if t.suggested_components else "-"
            md.append(f"| `{t.relative_path}` | {t.line_count} | {t.complexity_score}/10 | {comps} |")
        md.append("")
    
    md.append("## Templates by Category")
    md.append("")
    
    for category in sorted(by_category.keys()):
        templates = by_category[category]
        md.append(f"### {category.title()} ({len(templates)} templates)")
        md.append("")
        for t in sorted(templates, key=lambda x: x.relative_path):
            flags = []
            if t.has_jquery:
                flags.append("jQuery")
            if t.has_charts:
                flags.append("Charts")
            if t.has_datatables:
                flags.append("DataTables")
            if t.has_calendar:
                flags.append("Calendar")
            if t.has_react_already:
                flags.append("✓ React")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            md.append(f"- `{t.relative_path}` (P{t.migration_priority}, C{t.complexity_score}){flag_str}")
        md.append("")
    
    md.append("## High Complexity Templates (Complexity >= 7)")
    md.append("")
    high_complexity = [a for a in analyses if a.complexity_score >= 7]
    if high_complexity:
        md.append("These templates require special attention during migration:")
        md.append("")
        for t in sorted(high_complexity, key=lambda x: -x.complexity_score):
            md.append(f"### `{t.relative_path}`")
            md.append(f"- **Complexity:** {t.complexity_score}/10")
            md.append(f"- **Lines:** {t.line_count}")
            md.append(f"- **Patterns:** jQuery: {t.has_jquery}, Charts: {t.has_charts}, "
                     f"DataTables: {t.has_datatables}, Calendar: {t.has_calendar}")
            md.append(f"- **Suggested Components:** {', '.join(t.suggested_components)}")
            md.append(f"- **Jinja Variables:** {', '.join(t.jinja_variables[:10])}")
            md.append("")
    else:
        md.append("No high-complexity templates found.")
    
    return "\n".join(md)


def main():
    """Main entry point."""
    print("🔍 Scanning templates...")
    
    # Find all templates
    templates = list(TEMPLATES_DIR.rglob("*.html"))
    print(f"   Found {len(templates)} templates")
    
    # Analyze each template
    print("📊 Analyzing templates...")
    analyses = []
    for template in templates:
        analysis = analyze_template(template)
        analyses.append(analysis)
    
    # Sort by priority, then complexity
    analyses.sort(key=lambda x: (x.migration_priority, -x.complexity_score))
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write JSON audit
    json_path = OUTPUT_DIR / "template_audit.json"
    with open(json_path, "w") as f:
        json.dump([asdict(a) for a in analyses], f, indent=2)
    print(f"✅ Wrote JSON audit to {json_path}")
    
    # Write markdown plan
    md_path = OUTPUT_DIR / "migration_plan.md"
    md_content = generate_migration_plan(analyses)
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"✅ Wrote migration plan to {md_path}")
    
    # Print summary
    print("")
    print("📋 Quick Summary:")
    print(f"   Total templates: {len(analyses)}")
    print(f"   P1 (Critical): {sum(1 for a in analyses if a.migration_priority == 1)}")
    print(f"   P2 (Important): {sum(1 for a in analyses if a.migration_priority == 2)}")
    print(f"   P3 (Standard): {sum(1 for a in analyses if a.migration_priority == 3)}")
    print(f"   High complexity (>=7): {sum(1 for a in analyses if a.complexity_score >= 7)}")
    print(f"   Already using React: {sum(1 for a in analyses if a.has_react_already)}")
    

if __name__ == "__main__":
    main()
