# ehentaix Agent Notes

## Purpose and layout

`ehentaix` is a small async Python library for searching E-Hentai/ExHentai galleries, fetching thumbnails, and downloading album images. The package is used by the parent QwenBotQ project as a local editable dependency.

- `ehentaix/client.py`: HTTP client, HTML parsing, search result models, album traversal, image downloads, and filename sanitization.
- `ehentaix/__init__.py`: public exports.
- `test_search.py`: live E-Hentai search/thumbnail example.
- `test_exhentai_search.py`: live ExHentai search example requiring cookies.
- `EXPECTED_API.md`, `SEARCH_EXPRECTED_API.md`, and `SEARCH_QUERY.md`: API and response-shape notes; read them before changing parsing behavior.

The top-level `README.md` is stale and describes a different downloader project/layout. Prefer the current package code and the API notes when they disagree.

## Environment and commands

The standalone package targets Python `>=3.8` and uses setuptools. From this directory, install it for local development with:

```bash
python -m pip install -e .
```

When working through the parent project, use its Poetry environment instead:

```bash
poetry install
poetry run python -m compileall ehentaix
```

The scripts are live network checks, not isolated pytest unit tests. Run them explicitly from `ehentaix/` when network access is available:

```bash
python test_search.py
python test_exhentai_search.py  # requires a local cookies.json
```

`test_exhentai_search.py` opens `cookies.json` relative to the current working directory and both scripts execute immediately at import time. Do not run them with ordinary pytest collection unless that behavior has first been refactored. Keep real cookies and other credentials untracked.

## API and implementation boundaries

The public API is exported from `ehentaix/__init__.py`: `EHentaiClient`, `Gallery`, `SearchResult`, and the existing misspelled name `santize_album_name`. Preserve that spelling for compatibility unless adding a deliberate alias and migration path.

`EHentaiClient` is asynchronous and supports `async with`. If a caller supplies an `httpx.AsyncClient`, the library must not close it; only clients created internally are closed by `aclose()`/context-manager exit. Cookies are passed to the underlying HTTP client and are required for ExHentai access.

Search and album methods scrape live HTML from E-Hentai-compatible pages. Treat CSS selectors, URL/query formats, pagination, `nl` image fallback handling, retry behavior, and response parsing as external compatibility contracts. Preserve bounded retries and the existing backoff unless a change is intentional and tested against representative responses.

Album downloads write image files directly into the caller-provided target folder and return the parsed album name. Filename handling must remain platform-aware and must not allow source titles or URLs to create invalid path names. Avoid logging or committing URLs containing authentication cookies.

## Conventions

Keep the existing straightforward async style and type annotations. Use `httpx` for HTTP, BeautifulSoup for HTML parsing, dataclasses for returned models, and `pathlib.Path` for filesystem paths, matching `client.py`. Prefer focused parser/helper changes over broad rewrites, and add or update representative HTML fixtures before changing selectors. Avoid introducing new dependencies without updating `pyproject.toml` and the parent lockfile workflow.
