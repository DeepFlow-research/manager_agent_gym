## Building the docs locally (uv)

```bash
uv sync --group dev
uv run mkdocs serve -a 127.0.0.1:8001
# or
uvx mkdocs serve -a 127.0.0.1:8001
```

If port 8000 is busy, the `-a` flag changes the port.

