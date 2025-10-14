"""
===============================================================================
AutoDocGPT - File Tools
===============================================================================

A collection of file-related tools registered for use by the AutoDocGPT agent.

Tools provided:
- read_project_file(name) -> str
- list_project_files(extension=".py", recursive=True) -> List[str]
- write_project_file(name, content, overwrite=False) -> dict
- find_todos(path=".", recursive=True, max_results=500) -> List[dict]
- analyze_imports(name) -> dict

These functions are registered with the central registry via the
`@register_tool` decorator so the agent can call them through function-calling.

Note: Paths are resolved relative to the current working directory where the
agent is executed.
===============================================================================
"""
import os
import io
import ast
from typing import List, Dict, Any, Optional
from agent_core.registry import register_tool


@register_tool(tags=["file_operations", "read"])
def read_project_file(name: str) -> str:
    """
    Read and return the content of a file.

    Args:
        name: Path to the file (relative or absolute).

    Returns:
        The full file content as a string.

    Raises:
        FileNotFoundError if the file does not exist.
    """
    path = os.path.expanduser(name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    # Read with utf-8 fallback
    for enc in ("utf-8", "latin-1"):
        try:
            with io.open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # If all decodings fail, raise
    raise UnicodeDecodeError("Unable to decode file with utf-8 or latin-1.")


@register_tool(tags=["file_operations", "list"])
def list_project_files(extension: str = ".py", recursive: bool = True) -> List[str]:
    """
    List files in the current project directory filtered by extension.

    Args:
        extension: File extension to filter by (e.g., ".py", ".md").
        recursive: If True, walk directories recursively.

    Returns:
        Sorted list of file paths (relative) matching the extension.
    """
    root = os.getcwd()
    matched: List[str] = []

    if recursive:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.lower().endswith(extension.lower()):
                    full = os.path.join(dirpath, fn)
                    matched.append(os.path.relpath(full, root))
    else:
        for fn in os.listdir(root):
            if fn.lower().endswith(extension.lower()) and os.path.isfile(fn):
                matched.append(fn)

    matched.sort()
    return matched


@register_tool(tags=["file_operations", "write"])
def write_project_file(name: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Write content to a file. By_default prevents overwriting existing files.

    Args:
        name: Path to the file to write (relative or absolute).
        content: Text content to write.
        overwrite: If True, overwrite existing file.

    Returns:
        Dict with status and path information.

    Raises:
        FileExistsError if file exists and overwrite is False.
    """
    path = os.path.expanduser(name)
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"File already exists: {path}. Set overwrite=True to replace.")

    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "ok", "path": os.path.relpath(path, os.getcwd())}


@register_tool(tags=["file_operations", "search"])
def find_todos(path: str = ".", recursive: bool = True, max_results: int = 500) -> List[Dict[str, Any]]:
    """
    Search for TODO/FIXME annotations across project files.

    Args:
        path: Root directory or file to search.
        recursive: If True and path is a directory, walk recursively.
        max_results: Maximum number of matches to return.

    Returns:
        List of dicts: {"file": "rel/path", "line_no": int, "line": "..."}

    Notes:
        - Only scans text files (attempts utf-8 then latin-1).
    """
    root = os.path.abspath(path)
    results: List[Dict[str, Any]] = []
    checked = 0

    def scan_file(file_path: str):
        nonlocal checked
        if len(results) >= max_results:
            return
        try:
            with io.open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            try:
                with io.open(file_path, "r", encoding="latin-1") as f:
                    lines = f.readlines()
            except Exception:
                return

        for i, line in enumerate(lines, start=1):
            if "TODO" in line or "FIXME" in line:
                results.append({
                    "file": os.path.relpath(file_path, os.getcwd()),
                    "line_no": i,
                    "line": line.strip()
                })
                if len(results) >= max_results:
                    return
        checked += 1

    if os.path.isfile(root):
        scan_file(root)
    else:
        if recursive:
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    scan_file(full)
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break
        else:
            for fn in os.listdir(root):
                full = os.path.join(root, fn)
                if os.path.isfile(full):
                    scan_file(full)
                    if len(results) >= max_results:
                        break

    return results


@register_tool(tags=["file_operations", "analyze"])
def analyze_imports(name: str) -> Dict[str, List[str]]:
    """
    Parse a Python file and return its import statements.

    Args:
        name: Path to a Python file.

    Returns:
        Dict with keys "imports" (module names) and "from_imports" (tuples as 'module: names').
    """
    path = os.path.expanduser(name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with io.open(path, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception:
        with io.open(path, "r", encoding="latin-1") as f:
            src = f.read()

    tree = ast.parse(src, filename=path)
    imports: List[str] = []
    from_imports: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join([alias.name for alias in node.names])
            from_imports.append(f"{module}: {names}")

    return {"imports": sorted(set(imports)), "from_imports": sorted(set(from_imports))}


# -------------------------
# Quick demo (run this file directly to exercise tools)
# -------------------------
# if __name__ == "__main__":
#     print("Listing .py files (top-10):")
#     print(list_project_files(".py", recursive=False)[:10])
#
#     test_file = "sample_demo.txt"
#     print("\nWriting test file...")
#     print(write_project_file(test_file, "Hello AutoDocGPT!\n# TODO: add more", overwrite=True))
#
#     print("\nReading test file:")
#     print(read_project_file(test_file))
#
#     print("\nSearching TODOs:")
#     print(find_todos(".", recursive=False))
#
#     # Create a small Python file for import analysis demo
#     demo_py = "demo_imports.py"
#     write_project_file(demo_py, "import os\nfrom typing import List\n# TODO\n")
#     print("\nAnalyze imports:", analyze_imports(demo_py))
