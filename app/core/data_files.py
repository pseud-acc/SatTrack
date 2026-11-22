"""Serve the browser datasets (docs/app-data-contract.md; decisions D-010 and D-012).

GET /data/<name>.json returns a dataset the pipeline published (e.g. objects), exactly as the pipeline compressed it:
Brotli when the browser accepts it, else gzip, else (rare) decompressed, and 406 Not Acceptable when the request
rules out all three (RFC 9110 12.5.3). The app holds only the compressed bytes, loaded at start-up with the CSVs and
from the same run (app/core/state.py).

- ETag: the SHA-256 of the bytes sent, so a browser that already has this run's file gets 304 Not Modified.
  If-None-Match uses weak comparison and accepts '*' (RFC 9110 13.1.2), via werkzeug's parser.
- Cache-Control no-cache: the browser always revalidates (a cheap 304), so new data shows up after a run.
- Vary: Accept-Encoding, because the body depends on it.
gunicorn runs threaded workers (Procfile): the file is larger than Heroku's 1 MB router buffer, so a slow download
occupies one thread, not a whole worker.
"""
import gzip

from flask import Response, abort, request
from werkzeug.http import parse_etags

from app.core.state import get_app_data


def _qualities(accept_encoding):
    """{coding: q} from an Accept-Encoding value (lower-cased; a malformed q counts as 0)."""
    accepted = {}
    for part in accept_encoding.split(","):
        token, _, params = part.strip().partition(";")
        q = 1.0
        for param in params.split(";"):
            key, _, value = param.strip().partition("=")
            if key.strip() == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        if token.strip():
            accepted[token.strip().lower()] = q
    return accepted


def choose_encoding(accept_encoding, available):
    """The representation to send: whichever of 'br', 'gzip' and 'identity' (uncompressed) the client rates highest,
    or None when the client rules out every option (send 406). On a tie: Brotli, then gzip, then identity.

    RFC 9110 12.5.3: no header, or an empty one, means identity; a coding not listed takes the '*' rating if there is
    one; identity is acceptable unless the client says 'identity;q=0', or '*;q=0' without listing identity. Identity
    competes on its rating only when the client lists it (e.g. 'identity;q=1, gzip;q=0.1' gets identity); unlisted, it
    is the fallback when no compressed coding is acceptable."""
    if accept_encoding is None or not accept_encoding.strip():
        return "identity"
    accepted = _qualities(accept_encoding)
    star = accepted.get("*")
    rank = {"br": 2, "gzip": 1, "identity": 0}
    rated = [(accepted.get(enc, star if star is not None else 0.0), rank[enc], enc)
             for enc in ("br", "gzip") if enc in available]
    if "identity" in accepted:
        rated.append((accepted["identity"], rank["identity"], "identity"))
    rated = [r for r in rated if r[0] > 0]
    if rated:
        return max(rated)[2]
    identity_q = accepted.get("identity", star if star is not None else 1.0)
    return "identity" if identity_q > 0 else None


def dataset_response(name, accept_encoding, if_none_match):
    """The Response for one dataset request, or None if the dataset isn't loaded."""
    dataset = get_app_data()["data"].get("datasets", {}).get(name)
    if not dataset:
        return None
    enc = choose_encoding(accept_encoding, dataset)
    if enc is None:   # the client refused br, gzip and identity
        return Response("Not Acceptable: this dataset is available as br, gzip or uncompressed\n", status=406,
                        mimetype="text/plain", headers={"Vary": "Accept-Encoding"})
    source = dataset.get("gzip" if enc == "identity" else enc)
    if source is None:
        return None
    etag = source["sha256"] + ("-identity" if enc == "identity" else "")
    headers = {"ETag": f'"{etag}"', "Cache-Control": "no-cache", "Vary": "Accept-Encoding"}
    if if_none_match and parse_etags(if_none_match).contains_weak(etag):
        return Response(status=304, headers=headers)   # before any decompression: a 304 costs nothing
    # identity: decompress the gzip copy for this request only (rare; browsers accept br or gzip)
    body = gzip.decompress(source["body"]) if enc == "identity" else source["body"]
    if enc != "identity":
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
