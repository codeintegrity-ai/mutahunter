import os
PARSERS = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript", 
    ".go": "go",
    ".c": "c",
    ".cc": "cpp",
    ".cs": "c_sharp",
    ".cpp": "cpp",
    ".gomod": "gomod",
    ".java": "java",
    ".kt": "kotlin",
    ".php": "php",
    ".r": "r",
    ".R": "r",
    ".rb": "ruby",
    ".rs": "rust",
    ".tsx": "typescript",
    ".ts": "typescript",
}

def filename_to_lang(filename: str) -> str:
    basename = os.path.basename(filename)
    if basename in PARSERS:
        return PARSERS[basename]
    file_extension = os.path.splitext(filename)[1]
    if file_extension in PARSERS:
        return PARSERS[file_extension]
    return None

