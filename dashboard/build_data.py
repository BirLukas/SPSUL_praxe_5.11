"""Sesbírá studenti/<slozka>/results/summary.json ze všech Pull Requestů a uloží je do data.json pro dashboard.

Spouští GitHub Action (.github/workflows/dashboard.yml). Kód z PR se nikdy nespouští, jen se čte JSON.
Použití: python3 build_data.py dashboard/data.json   |   python3 build_data.py --selftest
"""
import datetime
import json
import os
import re
import sys
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "doudik/SPSUL_praxe_5.11")
TOKEN = os.environ.get("GITHUB_TOKEN")
SUMMARY_RE = re.compile(r"^studenti/([a-z0-9-]+)/results/summary\.json$")


def gh(path, raw=False):
    url = path if path.startswith("https://") else "https://api.github.com" + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "User-Agent": "spsul-evals-dashboard",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return body if raw else json.loads(body)


def paginate(path):
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        batch = gh(f"{path}{sep}per_page=100&page={page}")
        out += batch
        if len(batch) < 100 or page >= 30:
            return out
        page += 1


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _rate(v):
    return _num(v) and 0 <= v <= 1


def validate(s):
    """Vrátí seznam chyb ve formátu summary.json. Prázdný seznam = v pořádku."""
    if not isinstance(s, dict):
        return ["kořen souboru musí být objekt {...}"]
    errs = [f"chybí text '{k}'" for k in ("student", "uloha")
            if not isinstance(s.get(k), str) or not s[k].strip()]
    behy = s.get("behy")
    if not isinstance(behy, list) or not behy:
        return errs + ["chybí neprázdný seznam 'behy'"]
    for i, b in enumerate(behy):
        p = f"behy[{i}]"
        if not isinstance(b, dict):
            errs.append(f"{p} musí být objekt")
            continue
        errs += [f"{p}.{k} chybí" for k in ("model", "poskytovatel", "prompt")
                 if not isinstance(b.get(k), str) or not b[k].strip()]
        if b.get("sada") not in ("dev", "test"):
            errs.append(f"{p}.sada musí být \"dev\" nebo \"test\"")
        errs += [f"{p}.{k} musí být číslo od 0 do 1" for k in ("validni_json", "uplna_shoda")
                 if not _rate(b.get(k))]
        pole = b.get("pole")
        if not isinstance(pole, dict) or not pole or not all(_rate(v) for v in pole.values()):
            errs.append(f"{p}.pole musí být objekt {{\"nazev_pole\": 0 až 1}}")
        errs += [f"{p}.{k} musí být nezáporné číslo"
                 for k in ("pripadu", "latence_s", "tokeny_vstup", "tokeny_vystup")
                 if not _num(b.get(k)) or b[k] < 0]
    return errs


def pr_state(pr):
    if pr.get("merged_at"):
        return "sloučený"
    if pr["state"] == "closed":
        return "zavřený"
    return "rozpracovaný" if pr.get("draft") else "odevzdaný"


def collect(pr):
    entry = {
        "pr": pr["number"], "url": pr["html_url"], "titulek": pr["title"],
        "autor": pr["user"]["login"], "stav": pr_state(pr), "aktualizace": pr["updated_at"],
        "slozka": None, "summary": None, "chyby": [],
    }
    files = paginate(f"/repos/{REPO}/pulls/{pr['number']}/files")
    hits = [f for f in files if SUMMARY_RE.match(f["filename"]) and f["status"] != "removed"]
    if not hits:
        entry["chyby"] = ["soubor studenti/<slozka>/results/summary.json zatím v PR není"]
        return entry
    f = hits[0]
    entry["slozka"] = SUMMARY_RE.match(f["filename"]).group(1)
    try:
        head = pr["head"]["repo"]
        if head:
            raw = gh(f"/repos/{head['full_name']}/contents/{f['filename']}?ref={pr['head']['sha']}", raw=True)
        else:  # fork byl smazán
            raw = gh(f["raw_url"], raw=True)
        summary = json.loads(raw)
    except Exception as e:  # neplatný JSON nebo síť: ukázat studentovi, ne spadnout
        entry["chyby"] = [f"summary.json nejde načíst: {e}"]
        return entry
    entry["chyby"] = validate(summary)
    if not entry["chyby"]:
        entry["summary"] = summary
    return entry


def main(out_path):
    prs = paginate(f"/repos/{REPO}/pulls?state=all")
    data = {
        "vygenerovano": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "repo": REPO,
        "studenti": [collect(pr) for pr in prs],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"{len(prs)} PR -> {out_path}")


def selftest():
    ok = {"student": "Jan Novák", "uloha": "Inzeráty aut", "behy": [{
        "model": "openai/gpt-oss-20b", "poskytovatel": "groq", "prompt": "v1", "sada": "dev",
        "pripadu": 15, "validni_json": 1.0, "uplna_shoda": 0.6, "pole": {"znacka": 0.93},
        "latence_s": 0.42, "tokeny_vstup": 3100, "tokeny_vystup": 900}]}
    assert validate(ok) == [], validate(ok)
    bad = json.loads(json.dumps(ok))
    bad["behy"][0].update(uplna_shoda=60, sada="prod", pole={})
    assert len(validate(bad)) == 3, validate(bad)
    assert validate([]) and validate({"student": "x", "uloha": "y", "behy": []})
    assert SUMMARY_RE.match("studenti/novak-jan/results/summary.json")
    assert not SUMMARY_RE.match("studenti/Novák/results/summary.json")
    print("selftest OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "data.json")
