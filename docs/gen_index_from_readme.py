from pathlib import Path

import mkdocs_gen_files


def write_index_from_readme() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"
    output_path = Path("index.md")

    if not readme_path.exists():
        return

    content = readme_path.read_text(encoding="utf-8")

    with mkdocs_gen_files.open(output_path, "w") as f:
        f.write(content)

    mkdocs_gen_files.set_edit_path(output_path, str(readme_path.relative_to(repo_root)))


if __name__ == "__main__":
    write_index_from_readme()
