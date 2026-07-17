#!/usr/bin/env python3
"""Set each hackerdogs/<server> Docker Hub repo's README (full_description) from
the server's local README.md.

Auth: Docker Hub API JWT obtained from username + Personal Access Token.
Env:  DOCKERHUB_USER (default 'hackerdogs'), DOCKERHUB_PAT (required).
Usage: set-dockerhub-readme.py whois-mcp nmap-mcp ...
"""
import json, os, sys, urllib.request, urllib.error

NS = os.environ.get("DOCKERHUB_NAMESPACE", "hackerdogs")
USER = os.environ.get("DOCKERHUB_USER", "hackerdogs")
PAT = os.environ.get("DOCKERHUB_PAT", "")
MAX_FULL = 25000  # Docker Hub full_description limit


def api(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "JWT " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, (r.read().decode() or "")


def login():
    _, body = api("POST", "https://hub.docker.com/v2/users/login/",
                  body={"username": USER, "password": PAT})
    return json.loads(body)["token"]


def short_desc(server, readme):
    for raw in readme.splitlines():
        line = raw.strip().lstrip("#").strip()
        if not line:
            continue
        # skip HTML, images, badges, links-only, and divider lines
        if line[0] in "<![|>-=" or line.startswith("!["):
            continue
        if "img.shields.io" in line or line.startswith("http"):
            continue
        # require some alphabetic prose
        if sum(c.isalpha() for c in line) >= 8:
            return line[:100]
    return f"{server} — Hackerdogs MCP server"[:100]


def main():
    if not PAT:
        sys.exit("DOCKERHUB_PAT not set")
    servers = sys.argv[1:]
    if not servers:
        sys.exit("usage: set-dockerhub-readme.py <server> [server...]")
    token = login()
    ok = fail = 0
    for s in servers:
        rp = os.path.join(s, "README.md")
        if not os.path.isfile(rp):
            print(f"  SKIP {s}: no README.md"); fail += 1; continue
        readme = open(rp, encoding="utf-8", errors="replace").read()[:MAX_FULL]
        url = f"https://hub.docker.com/v2/repositories/{NS}/{s}/"
        try:
            st, _ = api("PATCH", url, token=token,
                        body={"full_description": readme,
                              "description": short_desc(s, readme)})
            print(f"  OK   {s} (HTTP {st})"); ok += 1
        except urllib.error.HTTPError as e:
            print(f"  FAIL {s}: HTTP {e.code} {e.read().decode()[:80]}"); fail += 1
        except Exception as e:
            print(f"  FAIL {s}: {e}"); fail += 1
    print(f"\nREADME set: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
