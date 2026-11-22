"""Serve the browser datasets (docs/app-data-contract.md; decisions D-010 and D-012).

GET /data/<name>.json returns a dataset the pipeline published (e.g. objects), exactly as the pipeline compressed it:
Brotli when the browser accepts it, else gzip, else (rare) decompressed. The app holds only the compressed bytes,
loaded at start-up with the CSVs and from the same run (app/core/state.py).

- ETag: the SHA-256 of the bytes sent, so a browser that already has this run's file gets 304 Not Modified.
- Cache-Control no-cache: the browser always revalidates (a cheap 304), so new data shows up after a run.
- Vary: Accept-Encoding, because the body depends on it.
gunicorn runs threaded workers (Procfile): the file is larger than Heroku's 1 MB router buffer, so a slow download
occupies one thread, not a whole worker.
"""
import gzip

from flask import Response, abort, request

from app.core.state import get_app_data


def choose_encoding(accept_encoding, available):
    """'br' if the client accepts Brotli, else 'gzip' if it accepts gzip, else None (send it uncompressed).
    Honours q=0 ("not acceptable") and '*'."""
    accepted = {}
    for part in (accept_encoding or "").split(","):
        token, _, params = part.strip().partition(";")
        q = 1.0
        for param in params.split(";"):
            key, _, value = param.strip().partition("=")
            if key == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        if token:
            accepted[token.strip().lower()] = q
    for enc in ("br", "gzip"):
        q = accepted.get(enc, accepted.get("*", 0.0))
        if enc in available and q > 0:
            return enc
    return None


def dataset_response(name, accept_encoding, if_none_match):
    """The Response for one dataset request, or None if the dataset isn't loaded."""
    dataset = get_app_data()["data"].get("datasets", {}).get(name)
    if not dataset:
        return None
    enc = choose_encoding(accept_encoding, dataset)
    if enc is None:   # no compression accepted: decompress the gzip copy for this request
        source = dataset.get("gzip")
        if source is None:
            return None
        body, etag = gzip.decompress(source["body"]), source["sha256"] + "-identity"
    else:
        body, etag = dataset[enc]["body"], dataset[enc]["sha256"]
    headers = {"ETag": f'"{etag}"', "Cache-Control": "no-cache", "Vary": "Accept-Encoding"}
    if if_none_match and f'"{etag}"' in [t.strip() for t in if_none_match.split(",")]:
        return Response(status=304, headers=headers)
    if enc:
        headers["Content-Encoding"] = enc   # also tells flask-compress to leave the body alone
    return Response(body, status=200, mimetype="application/json", headers=headers)


def register_data_routes(server):
    """Add GET /data/<name>.json to the Flask server behind the Dash app."""

    @server.route("/data/<name>.json")
    def serve_dataset(name):
        response = dataset_response(name, request.headers.get("Accept-Encoding"),
                                    request.headers.get("If-None-Match"))
        if response is None:
            abort(404)
        return response
