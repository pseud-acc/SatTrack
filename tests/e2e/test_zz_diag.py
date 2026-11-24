"""TEMPORARY diagnostic (removed before merge): per-visit start-up phases in visit order, to find the bias in
test_startup_against_baseline. Runs after it, so both servers and the browser are warm here."""
import json
import os

from test_viewer import job_summary, startup_profile


def test_diag(browser, budget_url, baseline_url):
    if baseline_url is None:
        return
    rounds = int(os.environ.get("DIAG_ROUNDS", "6"))
    seq = []
    for i in range(rounds):
        pair = [("branch", budget_url), ("baseline", baseline_url)]
        for pos, (who, url) in enumerate(pair if i % 2 == 0 else pair[::-1]):
            p = startup_profile(browser, url)
            seq.append({"i": i, "pos": pos, "who": who, **{k: round(v) for k, v in p["phases"].items()}})
    if os.environ.get("DIAG_OUT"):
        with open(os.environ["DIAG_OUT"], "w") as f:
            json.dump(seq, f)
    rows = "\n".join(f"| {r['i']} | {r['pos']} | {r['who']} | {r['data']} | {r['cesium']} | {r['viewer']} | "
                     f"{r['ready']} | {r['firstPositions']} |" for r in seq)
    job_summary("### DIAG: warm visits in order (temporary)\n\n| round | pos | who | data | cesium | viewer | ready | "
                "first |\n|---|---|---|---|---|---|---|---|\n" + rows)
