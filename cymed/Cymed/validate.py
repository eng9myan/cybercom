import ast
import glob
import os
import sys

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-validation-only")
os.environ.setdefault("DJANGO_DEBUG", "True")

# Validate settings import
sys.path.insert(0, r'D:\cybercom\cymed')
import core.settings
print("SETTINGS_IMPORT_OK")

# Validate all new Python files
files = (
    glob.glob(r'D:\cybercom\cymed\platform\**\*.py', recursive=True)
    + glob.glob(r'D:\cybercom\cymed\products\cymed\integrations\**\*.py', recursive=True)
    + glob.glob(r'D:\cybercom\cymed\products\cymed\patient_portal\**\*.py', recursive=True)
    + glob.glob(r'D:\cybercom\cymed\products\cymed\provider_portal\**\*.py', recursive=True)
)

for f in files:
    try:
        ast.parse(open(f, encoding='utf-8').read())
    except SyntaxError as e:
        print(f"SYNTAX_ERROR: {f}: {e}")
        sys.exit(1)

print(f"ALL_PYTHON_VALID: {len(files)} files")
