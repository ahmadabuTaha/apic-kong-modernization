from pathlib import Path

from .domain_validation import build_domain_validation


if __name__ == "__main__":
    print(build_domain_validation(Path.cwd())["manifest"]["summary"])
