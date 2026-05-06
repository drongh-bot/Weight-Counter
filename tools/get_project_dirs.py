import os

EXCLUDE = {".venv", ".idea", "__pycache__", "build", "dist", ".git", ".ruff_cache", ".gitignore", ".python-version",
           "log", "README.md", "tools", "uv.lock"}


def print_tree(path, prefix=""):
    files = sorted(os.listdir(path))
    for i, name in enumerate(files):
        if name in EXCLUDE:
            continue
        full = os.path.join(path, name)
        connector = "└── " if i == len(files) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(full):
            extension = "    " if i == len(files) - 1 else "│   "
            print_tree(full, prefix + extension)


print_tree("../")
