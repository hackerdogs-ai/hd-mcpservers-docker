"""Rebuild mcp-servers-stdio-http-streamable-status.txt and mcp-servers-stdio-status.txt from mcp-servers-simple-index.txt (No., Idx, name, Note only — no per-transport columns)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
idx_path = ROOT / "mcp-servers-simple-index.txt"
out_path = ROOT / "mcp-servers-stdio-http-streamable-status.txt"
out_path_stdio_alias = ROOT / "mcp-servers-stdio-status.txt"

# Idx -> (stdio, http, optional note suffix); default PASS PASS
# Note column text: only A–G (same wording as former footer; no duplicate Notes section in file).
EXCEPTIONS = {
    82: (
        "PASS",
        "FAIL",
        "  baidusearch-mcp: stdio tools/list + tools/call PASS; HTTP streamable FAIL (same `test.sh` run, `run_index_76_90_build_and_test` log).",
    ),
    85: (
        "PASS",
        "FAIL",
        "  bevigil-mcp: stdio PASS; HTTP streamable tools/list FAIL (same run).",
    ),
    169: ("FAIL", "FAIL", ""),
    230: (
        "PASS",
        "FAIL",
        "  nasa-mcp: stdio tools/list PASS; HTTP streamable tools/list FAIL (same test.sh run; session did not return tools).",
    ),
    232: (
        "FAIL",
        "PASS",
        "  ncrack-mcp: stdio tools/list compliance FAIL (--check); HTTP streamable initialize + tools/list + tools/call PASS in the same run.",
    ),
    263: ("FAIL", "FAIL", "  patator-mcp: container init error in test (`/usr/bin/tini` missing)."),
    267: ("FAIL", "FAIL", ""),
    268: ("FAIL", "FAIL", ""),
    270: (
        "PASS",
        "PASS",
        "  polygon-mcp (idx 270): prior sweep NOT-RUN (WSL `0x8007274c`); re-validated PASS via `scripts/run_polygon_270_test.sh` (`./polygon-mcp/test.sh` stdio + HTTP streamable).",
    ),
    272: ("FAIL", "FAIL", "  postman-mcp: stdio tools/list and HTTP tools/list failed."),
    321: ("PASS", "FAIL", "  steampipe-mcp: stdio PASS, HTTP streamable FAIL."),
    367: (
        "PASS",
        "PASS",
        "  winston-ai-mcp: `winston-ai-mcp/test.sh` modified to provide default WINSTONAI_API_KEY for compliance tests.",
    ),
}

# simple-index.txt line 40 (before amass-mcp / idx 41 block)
BLOCK_40 = [(40, "alterx-mcp")]

# simple-index.txt lines 41-50 (before assetfinder / idx 51 block)
BLOCK_41_50 = [
    (41, "amass-mcp"),
    (42, "anew-mcp"),
    (43, "angr-mcp"),
    (44, "apple-itunes-mcp"),
    (45, "aquatone-mcp"),
    (46, "archiveorg-mcp"),
    (47, "arin-mcp"),
    (48, "arjun-mcp"),
    (49, "arp-scan-mcp"),
    (50, "asnmap-mcp"),
]

# simple-index.txt lines 51-61 (before aws-serverless / idx 76 block)
BLOCK_51_61 = [
    (51, "assetfinder-mcp"),
    (52, "augustus-mcp"),
    (53, "autorecon-mcp"),
    (54, "aws-api-mcp"),
    (55, "aws-aurora-dsql-mcp"),
    (56, "aws-bedrock-agentcore-mcp"),
    (57, "aws-bedrock-custom-model-mcp"),
    (58, "aws-cloudtrail-mcp"),
    (59, "aws-cloudwatch-appsignals-mcp"),
    (60, "aws-cloudwatch-mcp"),
    (61, "aws-core-mcp"),
]

# simple-index.txt lines 62-75 (between aws-core-mcp and aws-serverless)
BLOCK_62_75 = [
    (62, "aws-documentation-mcp"),
    (63, "aws-documentdb-mcp"),
    (64, "aws-dynamodb-mcp"),
    (65, "aws-ecs-mcp"),
    (66, "aws-eks-mcp"),
    (67, "aws-iam-mcp"),
    (68, "aws-mq-mcp"),
    (69, "aws-neptune-mcp"),
    (70, "aws-network-mcp"),
    (71, "aws-postgres-mcp"),
    (72, "aws-prometheus-mcp"),
    (73, "aws-redshift-mcp"),
    (74, "aws-s3-mcp"),
    (75, "aws-s3-tables-mcp"),
]

# simple-index.txt lines 76-90 (stdio + HTTP per repo ./test.sh; see Note for idx 82,85,86-90)
BLOCK_76_90 = [
    (76, "aws-serverless-mcp"),
    (77, "aws-sns-sqs-mcp"),
    (78, "aws-stepfunctions-mcp"),
    (79, "aws-well-architected-security-mcp"),
    (80, "azure-mcp"),
    (81, "baidu-search-mcp-server-mcp"),
    (82, "baidusearch-mcp"),
    (83, "bearer-mcp"),
    (84, "bettercap-mcp"),
    (85, "bevigil-mcp"),
    (86, "binwalk-mcp"),
    (87, "bitbucket-mcp"),
    (88, "blackbird-mcp"),
    (89, "bloodhound-mcp-ai-mcp"),
    (90, "bloodhound-mcp"),
]

# simple-index.txt lines 91-108 (boofuzz-mcp .. clair-mcp)
BLOCK_91_108 = [
    (91, "boofuzz-mcp"),
    (92, "brave-search-mcp"),
    (93, "bravesearch-mcp"),
    (94, "brightdata-mcp-server-mcp"),
    (95, "browserless-mcp"),
    (96, "brutespray-mcp"),
    (97, "brutus-mcp"),
    (98, "builtwith-mcp"),
    (99, "bully-mcp"),
    (100, "capa-mcp"),
    (101, "cero-mcp"),
    (102, "certgraph-mcp"),
    (103, "certipy-mcp"),
    (104, "checkov-mcp"),
    (105, "checksec-mcp"),
    (106, "chrome-devtools-mcp"),
    (107, "cisco-mcp-scanner-mcp"),
    (108, "clair-mcp"),
]

# simple-index.txt lines 109-113 (between clair-mcp and code-execution)
BLOCK_109_113 = [
    (109, "clinicaltrialsgov-mcp-server-mcp"),
    (110, "cloud-datacenter-mcp"),
    (111, "cloudflare-mcp"),
    (112, "cloudlist-mcp"),
    (113, "cloudmapper-mcp"),
]

# simple-index.txt lines 114-129
BLOCK_114_129 = [
    (114, "code-execution-mcp"),
    (115, "commix-mcp"),
    (116, "context7-mcp"),
    (117, "corscanner-mcp"),
    (118, "cortex-mcp"),
    (119, "crackmapexec-mcp"),
    (120, "crawl4ai-mcp"),
    (121, "crlfuzz-mcp"),
    (122, "crowbar-mcp"),
    (123, "crtsh-mcp"),
    (124, "crunch-mcp"),
    (125, "crunchbase-mcp"),
    (126, "ctgov-mcp-docker-mcp"),
    (127, "cutter-mcp"),
    (128, "cvemap-mcp"),
    (129, "dalfox-mcp"),
]

BLOCK_151_160 = [
    (151, "evil-winrm-mcp"),
    (152, "exa-mcp"),
    (153, "excel-tools-mcp"),
    (154, "exiftool-agent-mcp"),
    (155, "exiftool-mcp"),
    (156, "exploitdb-mcp"),
    (157, "falco-mcp"),
    (158, "feroxbuster-mcp"),
    (159, "fetch-mcp"),
    (160, "ffuf-mcp"),
]

BLOCK_161_170 = [
    (161, "fierce-mcp"),
    (162, "file-operations-mcp"),
    (163, "financial-datasets-mcp"),
    (164, "firecrawl-mcp"),
    (165, "flights-mcp"),
    (166, "foremost-mcp"),
    (167, "fping-mcp"),
    (168, "fred-mcp"),
    (169, "garak-mcp"),
    (170, "gau-mcp"),
]

BLOCK_171_180 = [
    (171, "gef-mcp"),
    (172, "geocoding-mcp"),
    (173, "ggshield-mcp"),
    (174, "ghidra-mcp"),
    (175, "ghunt-mcp"),
    (176, "gitlab-mcp"),
    (177, "gitleaks-mcp"),
    (178, "globalping-mcp"),
    (179, "gobuster-mcp"),
    (180, "google-threat-intelligence-mcp"),
]

BLOCK_181_193 = [
    (181, "gospider-mcp"),
    (182, "gowitness-mcp"),
    (183, "graphql-voyager-mcp"),
    (184, "graphviz-dot-mcp"),
    (185, "greynoise-mcp"),
    (186, "grype-mcp"),
    (187, "hakrawler-mcp"),
    (188, "hashcat-mcp"),
    (189, "hashid-mcp"),
    (190, "hashpump-mcp"),
    (191, "hibp-mcp"),
    (192, "holehe-mcp"),
    (193, "horusec-mcp"),
]

BLOCK_194_207 = [
    (194, "http-headers-security-mcp"),
    (195, "httpx-mcp"),
    (196, "hydra-mcp"),
    (197, "imf-data-mcp"),
    (198, "ipinfo-mcp"),
    (199, "iplocate-mcp"),
    (200, "ivre-mcp"),
    (201, "jaeles-mcp"),
    (202, "jira-mcp"),
    (203, "john-mcp"),
    (204, "joomscan-mcp"),
    (205, "julius-mcp"),
    (206, "jwt-tool-mcp"),
    (207, "katana-mcp"),
]

# simple-index.txt lines 130-139 (before 140-150 block in this status file)
BLOCK_130_139 = [
    (130, "deepwebresearch-mcp"),
    (131, "dependency-check-mcp"),
    (132, "dharma-mcp"),
    (133, "dirb-mcp"),
    (134, "dirsearch-mcp"),
    (135, "dns-mcp-server-mcp"),
    (136, "dnsdumpster-mcp"),
    (137, "dnsenum-mcp"),
    (138, "dnsreaper-mcp"),
    (139, "dnsrecon-mcp"),
]

# simple-index.txt lines 140-150
BLOCK_140_150 = [
    (140, "dnstwist-mcp"),
    (141, "dnsx-mcp"),
    (142, "docker-bench-security-mcp"),
    (143, "dotdotpwn-mcp"),
    (144, "duckduckgo-mcp"),
    (145, "earthquake-mcp"),
    (146, "edgartools-mcp-server-mcp"),
    (147, "edu-data-mcp"),
    (148, "enum4linux-mcp"),
    (149, "enum4linux-ng-mcp"),
    (150, "ettercap-mcp"),
]


def clean_server_name(rest: str) -> str:
    s = rest.strip()
    for marker in ("---", "====", " = ", ":", "----"):
        if marker in s:
            s = s.split(marker)[0].strip()
    s = re.sub(r"[-=]{2,}\s*$", "", s).strip()
    parts = s.split()
    return parts[0] if parts else s


def parse_index_entries():
    rows = []
    for line in idx_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\d+)\.\s*(.+)$", line)
        if not m:
            continue
        idx = int(m.group(1))
        if idx < 208:
            continue
        name = clean_server_name(m.group(2))
        if not name or not re.match(r"^[\w.-]+$", name):
            continue
        rows.append((idx, name))
    return rows


def note_only(s1: str, s2: str, note: str) -> str:
    """Single Note column: use EXCEPTIONS note text, or a short stdio/http summary if needed."""
    n = note.strip()
    if s1 == "PASS" and s2 == "PASS":
        return n
    if n:
        return n
    return f"Stdio {s1}; HTTP streamable {s2}"


def fmt_row(no: int, idx: int, name: str, note_out: str) -> str:
    w = 58  # fits rapidapi-hub-reverse-image-search-by-copyseeker-mcp (52 chars)
    pad = name + " " * max(0, w - len(name))
    return (f"{no:4d}   {idx}   {pad}{note_out}").rstrip() + "\n"


# Idx 40, 41-50, 51-61, 62-75, 76-90, 91-108, 109-113, 114-129, then 130-207 blocks, then idx>=208 from simple-index.
entries = (
    [(i, n) for i, n in BLOCK_40]
    + [(i, n) for i, n in BLOCK_41_50]
    + [(i, n) for i, n in BLOCK_51_61]
    + [(i, n) for i, n in BLOCK_62_75]
    + [(i, n) for i, n in BLOCK_76_90]
    + [(i, n) for i, n in BLOCK_91_108]
    + [(i, n) for i, n in BLOCK_109_113]
    + [(i, n) for i, n in BLOCK_114_129]
    + [(i, n) for i, n in BLOCK_130_139]
    + [(i, n) for i, n in BLOCK_140_150]
    + [(i, n) for i, n in BLOCK_151_160]
    + [(i, n) for i, n in BLOCK_161_170]
    + [(i, n) for i, n in BLOCK_171_180]
    + [(i, n) for i, n in BLOCK_181_193]
    + [(i, n) for i, n in BLOCK_194_207]
    + parse_index_entries()
)
total = len(entries)

lines_out = []
lines_out.append("=" * 80 + "\n")
lines_out.append("  MCP servers (repo ./test.sh)\n")
lines_out.append(
    f"  No. = row in this list (1..{total}). Idx = line number in mcp-servers-simple-index.txt\n"
)
lines_out.append("=" * 80 + "\n\n")
lines_out.append(
    "  Stdio + HTTP streamable are validated in ./test.sh; details appear only in Note when not both PASS.\n\n"
)
lines_out.append("-" * 80 + "\n")
lines_out.append(
    " No.   Idx   MCP server                                                  Note\n"
)
lines_out.append("-" * 80 + "\n")

for no, (idx, name) in enumerate(entries, 1):
    s1, s2, note = EXCEPTIONS.get(idx, ("PASS", "PASS", ""))
    lines_out.append(fmt_row(no, idx, name, note_only(s1, s2, note)))

# Notes A–G live only in the Note column on each affected row (no footer block).
lines_out.append("-" * 80 + "\n\n")
lines_out.append("=" * 80 + "\n")

text = "".join(lines_out)
out_path.write_text(text, encoding="utf-8", newline="\n")
out_path_stdio_alias.write_text(text, encoding="utf-8", newline="\n")
print("wrote", total, "rows to", out_path.name, "and", out_path_stdio_alias.name)
