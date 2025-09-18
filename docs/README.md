## Building the docs locally

Install dev dependencies with uv and serve the docs:

```bash
uv sync --group dev
uv run mkdocs serve
```

Alternatively, run mkdocs in an ephemeral tool environment:

```bash
uvx mkdocs serve
```

The API reference uses mkdocstrings to render docstrings directly from the code.

