# -*- coding: utf-8 -*-
import os
import sys

# Prohibited terms
PROHIBITED_TERMS = ["odoo", "anabtawi"]

# Approved exceptions (paths containing these are skipped from causing build failure)
APPROVED_PATHS = [
    os.path.normpath("LEGAL"),
    os.path.normpath("docs/private-source-analysis"),
    "compliance_scanner.py",
    "cycom.bat",
    "find_violations.py"
]

# Ignored directories entirely (we don't scan them)
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".next",
    "__pycache__",
    "postgres-data",
    "engine-data",
    "engine-source",
    "cycom-backend.archive",
    ".system_generated",
    ".claude",
    "uploads"
}

# Ignored file extensions (binaries and images)
IGNORED_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".db", ".sqlite3",
    ".exe", ".dll", ".so", ".dylib", ".woff", ".woff2", ".eot", ".ttf"
}

def is_framework_syntax(line, file_ext, file_name, rel_path):
    """Detect if term is a necessary framework syntax reference rather than branding."""
    line_stripped = line.strip()
    rel_path_norm = os.path.normpath(rel_path).lower()
    
    # 1. Any code inside backend cycom-platform addons/config is technical framework code
    if "cycom-platform" in rel_path_norm:
        return True

    # 2. Python framework imports & base class variables in other core scripts
    if file_ext == ".py":
        if "import odoo" in line_stripped.lower() or "from odoo" in line_stripped.lower():
            return True
        if any(k in line_stripped for k in ["_inherit =", "_inherit=", "_name =", "_name=", "models.AbstractModel", "models.TransientModel", "models.Model"]):
            return True
        if "super(" in line_stripped or "odoo.tests" in line_stripped.lower():
            return True
            
    # 3. JS framework namespaces, imports & OWL decorators
    if file_ext in [".js", ".ts", ".tsx", ".jsx"]:
        if any(k in line_stripped for k in ["@odoo", "odoo.define", "odoo-module", "@odoo/owl", "/web/image", "odoo."]):
            return True

    # 4. Manifest dependencies
    if file_name == "__manifest__.py":
        if any(k in line_stripped for k in ["'depends'", '"depends"', "'version'", '"version"', "'category'", '"category"', "'author'", '"author"']):
            return True
            
    # 5. XML view/model inheritance references
    if file_ext == ".xml":
        if any(k in line_stripped for k in ["inherit_id", "model=", "model=\"", "ref=\"", "name=\"model\"", "name='model'", "position="]):
            return True
            
    # 6. CSV model security access definitions
    if file_ext == ".csv":
        if any(k in line_stripped for k in ["model_", "id,name,model_id", "access_"]):
            return True
            
    return False

def scan_branding():
    workspace = os.path.dirname(os.path.abspath(__file__))
    findings = []
    total_files_scanned = 0

    print("============================================================")
    print("Cycom ERP Compliance Branding Scanner")
    print(f"Scanning workspace: {workspace}")
    print("============================================================")

    for root, dirs, files in os.walk(workspace):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORED_EXTS:
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, workspace)

            # Skip the scanner script itself and bat wrappers
            if any(p in os.path.normpath(rel_path) for p in ["compliance_scanner.py", "cycom.bat", "find_violations.py"]):
                continue

            total_files_scanned += 1

            # Read and scan file
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for term in PROHIBITED_TERMS:
                            if term in line.lower():
                                is_exception = False
                                
                                # Check if path is in approved exceptions
                                for app_path in APPROVED_PATHS:
                                    if app_path.lower() in os.path.normpath(rel_path).lower():
                                        is_exception = True
                                        break
                                
                                # Check if it is a necessary framework syntax
                                if not is_exception:
                                    if is_framework_syntax(line, ext, file, rel_path):
                                        # Term "anabtawi" is NEVER allowed in active code/config (only LEGAL/docs)
                                        if term == "anabtawi":
                                            is_exception = False
                                        else:
                                            is_exception = True
                                
                                classification = "Developer-visible"
                                if rel_path.endswith((".tsx", ".ts", ".html", ".css")):
                                    classification = "Customer-visible / Frontend"
                                elif "api" in rel_path.lower():
                                    classification = "API-visible"
                                
                                findings.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "term": term,
                                    "classification": classification,
                                    "is_exception": is_exception
                                })
            except Exception as e:
                pass

    # Print results
    exceptions_count = sum(1 for f in findings if f["is_exception"])
    violations_count = sum(1 for f in findings if not f["is_exception"])

    print(f"Scanned {total_files_scanned} files.")
    print(f"Total findings: {len(findings)} ({exceptions_count} approved exceptions, {violations_count} active violations)\n")

    if findings:
        print(f"{'File Path':<60} | {'Line':<5} | {'Term':<10} | {'Classification':<20} | {'Status':<10}")
        print("-" * 115)
        for f in findings:
            status = "EXCEPTION" if f["is_exception"] else "VIOLATION"
            print(f"{f['file'][:60]:<60} | {f['line']:<5} | {f['term']:<10} | {f['classification']:<20} | {status:<10}")

    print("\n============================================================")
    if violations_count > 0:
        print("[FAILURE] Compliance scan failed. Active branding violations detected!")
        sys.exit(1)
    else:
        print("[SUCCESS] Compliance scan passed. No active branding violations.")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "compliance" and sys.argv[2] == "scan-branding":
        scan_branding()
    else:
        print("Usage: python compliance_scanner.py compliance scan-branding")
        sys.exit(1)
