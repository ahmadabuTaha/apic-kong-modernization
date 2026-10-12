from pathlib import Path

from .skeleton_mapping import build_skeleton_mapping


if __name__ == "__main__":
    print(build_skeleton_mapping(Path.cwd())["manifest"]["summary"])
