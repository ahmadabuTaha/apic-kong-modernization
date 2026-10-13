from pathlib import Path

from .qiwa_mapping import build_qiwa_mapping


if __name__ == "__main__":
    result = build_qiwa_mapping(Path.cwd())
    print(result["manifest"]["summary"])
