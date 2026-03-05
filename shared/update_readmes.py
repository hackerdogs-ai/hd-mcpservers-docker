#!/usr/bin/env python3
"""Update README.md files for all 57 MCP tools to document URL-based file ingestion.

Adds:
1. source_url parameter row to generic-argument tools' parameter tables
2. download_file and cleanup_downloads tool documentation
3. URL-based example prompts (appended to existing prompts)
4. HD_MAX_DOWNLOAD_MB and HD_FETCH_TIMEOUT env vars
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Tool metadata: each entry has:
#   "type": "generic" | "explicit-path" | "download-only"
#   "url_prompts": list of URL-based example prompts to append
#   "run_fn": the run function name (for generic tools)
# ---------------------------------------------------------------------------

TOOLS = {
    # ── Source Code Scanners ──
    "semgrep-mcp": {
        "type": "generic",
        "run_fn": "run_semgrep",
        "url_prompts": [
            '"Scan the source code at https://github.com/juice-shop/juice-shop for security vulnerabilities using source_url and --config auto."',
            '"Download the repo from https://github.com/org/api-server and run semgrep against it to find injection flaws."',
            '"Use download_file to fetch https://example.com/source.tar.gz, then scan it with semgrep for hardcoded secrets."',
        ],
    },
    "trufflehog-mcp": {
        "type": "generic",
        "run_fn": "run_trufflehog",
        "url_prompts": [
            '"Scan https://github.com/org/repo for leaked credentials and secrets using source_url."',
            '"Download and scan https://example.com/source-archive.tar.gz for hardcoded API keys with trufflehog."',
        ],
    },
    "checkov-mcp": {
        "type": "generic",
        "run_fn": "run_checkov",
        "url_prompts": [
            '"Scan the Terraform configs at https://github.com/org/terraform-infra for IaC misconfigurations using source_url."',
            '"Download https://github.com/org/k8s-manifests and check for Kubernetes security misconfigurations with checkov."',
        ],
    },
    "terrascan-mcp": {
        "type": "generic",
        "run_fn": "run_terrascan",
        "url_prompts": [
            '"Scan https://github.com/org/terraform-configs for policy violations using terrascan with source_url."',
            '"Download the IaC files from https://example.com/infra.tar.gz and run terrascan against them."',
        ],
    },
    "gitleaks-mcp": {
        "type": "generic",
        "run_fn": "run_gitleaks",
        "url_prompts": [
            '"Scan https://github.com/org/repo for leaked secrets in the git history using source_url."',
            '"Download the repo at https://github.com/org/backend and check it for API key leaks with gitleaks."',
        ],
    },
    "horusec-mcp": {
        "type": "generic",
        "run_fn": "run_horusec",
        "url_prompts": [
            '"Scan https://github.com/org/webapp for security vulnerabilities using horusec with source_url."',
            '"Download the source code from https://example.com/project.zip and analyze it with horusec."',
        ],
    },
    "bearer-mcp": {
        "type": "generic",
        "run_fn": "run_bearer",
        "url_prompts": [
            '"Scan https://github.com/org/api-server for data flow issues and sensitive data leaks using source_url."',
            '"Download https://example.com/project.tar.gz and scan it with bearer for privacy and security risks."',
        ],
    },
    "dependency-check-mcp": {
        "type": "generic",
        "run_fn": "run_dependency_check",
        "url_prompts": [
            '"Scan https://github.com/org/java-app for known vulnerable dependencies using source_url."',
            '"Download the project from https://example.com/app.tar.gz and check its dependencies for CVEs."',
        ],
    },
    "kubescape-mcp": {
        "type": "generic",
        "run_fn": "run_kubescape",
        "url_prompts": [
            '"Scan the Kubernetes manifests at https://github.com/org/k8s-manifests for security issues using source_url."',
            '"Download https://example.com/helm-chart.tar.gz and audit it with kubescape."',
        ],
    },
    "ggshield-mcp": {
        "type": "generic",
        "run_fn": "run_ggshield",
        "url_prompts": [
            '"Scan https://github.com/org/repo for leaked credentials using ggshield with source_url."',
            '"Download and scan https://example.com/source.zip for secrets with ggshield."',
        ],
    },
    "retire-js-mcp": {
        "type": "generic",
        "run_fn": "run_retire_js",
        "url_prompts": [
            '"Scan https://github.com/org/frontend-app for known vulnerable JavaScript libraries using source_url."',
            '"Download the Node.js project from https://example.com/webapp.tar.gz and check for vulnerable JS dependencies."',
        ],
    },
    # ── Binary Analysis ──
    "binwalk-mcp": {
        "type": "generic",
        "run_fn": "run_binwalk",
        "url_prompts": [
            '"Download the firmware from https://example.com/router-firmware.bin using source_url and analyze it with binwalk."',
            '"Use download_file to fetch https://example.com/firmware.bin, then run binwalk extraction on it."',
        ],
    },
    "radare2-mcp": {
        "type": "generic",
        "run_fn": "run_radare2",
        "url_prompts": [
            '"Download the binary from https://example.com/sample.elf using source_url and analyze it with radare2."',
            '"Fetch https://example.com/malware.bin and disassemble the main function with radare2."',
        ],
    },
    "ghidra-mcp": {
        "type": "generic",
        "run_fn": "run_ghidra",
        "url_prompts": [
            '"Download https://example.com/sample.exe using source_url and decompile it with Ghidra."',
            '"Fetch the binary at https://example.com/firmware.bin and analyze its functions with Ghidra."',
        ],
    },
    "checksec-mcp": {
        "type": "generic",
        "run_fn": "run_checksec",
        "url_prompts": [
            '"Download https://example.com/binary using source_url and check its security properties (RELRO, stack canary, NX, PIE)."',
            '"Fetch https://example.com/vuln-app and run checksec to see what exploit mitigations are enabled."',
        ],
    },
    "upx-mcp": {
        "type": "generic",
        "run_fn": "run_upx",
        "url_prompts": [
            '"Download https://example.com/packed-binary.exe using source_url and try to unpack it with UPX."',
            '"Fetch the packed executable from https://example.com/sample.bin and decompress it with UPX."',
        ],
    },
    "cutter-mcp": {
        "type": "generic",
        "run_fn": "run_cutter",
        "url_prompts": [
            '"Download https://example.com/sample.bin using source_url and analyze it with Cutter."',
            '"Fetch the binary from https://example.com/malware.elf and reverse-engineer it with Cutter."',
        ],
    },
    "capa-mcp": {
        "type": "generic",
        "run_fn": "run_capa",
        "url_prompts": [
            '"Download https://example.com/malware.exe using source_url and identify its capabilities with capa."',
            '"Fetch the sample from https://example.com/suspicious.bin and run capa to detect behaviors."',
        ],
    },
    # ── Exploit Development ──
    "peda-mcp": {
        "type": "generic",
        "run_fn": "run_peda",
        "url_prompts": [
            '"Download https://example.com/vuln-binary using source_url and debug it with PEDA."',
            '"Fetch the challenge binary from https://example.com/pwn-challenge and analyze it with PEDA."',
        ],
    },
    "gef-mcp": {
        "type": "generic",
        "run_fn": "run_gef",
        "url_prompts": [
            '"Download https://example.com/challenge-binary using source_url and analyze it with GEF."',
            '"Fetch the CTF binary from https://example.com/heap-challenge and debug it with GEF."',
        ],
    },
    "ropgadget-mcp": {
        "type": "generic",
        "run_fn": "run_ropgadget",
        "url_prompts": [
            '"Download https://example.com/vuln-binary using source_url and find ROP gadgets in it."',
            '"Fetch the binary from https://example.com/target.elf and search for useful gadgets with ROPgadget."',
        ],
    },
    "ropper-mcp": {
        "type": "generic",
        "run_fn": "run_ropper",
        "url_prompts": [
            '"Download https://example.com/vuln-binary using source_url and search for ROP/JOP gadgets with Ropper."',
            '"Fetch https://example.com/libc.so.6 and find useful gadgets for exploit development."',
        ],
    },
    "pwntools-mcp": {
        "type": "generic",
        "run_fn": "run_pwntools",
        "url_prompts": [
            '"Download https://example.com/ctf-binary using source_url and analyze it with pwntools."',
            '"Fetch the challenge from https://example.com/pwn.zip and use pwntools to inspect the binary."',
        ],
    },
    "angr-mcp": {
        "type": "generic",
        "run_fn": "run_angr",
        "url_prompts": [
            '"Download https://example.com/binary using source_url and perform symbolic execution with angr."',
            '"Fetch the CTF challenge from https://example.com/crackme and solve it with angr."',
        ],
    },
    "one-gadget-mcp": {
        "type": "generic",
        "run_fn": "run_one_gadget",
        "url_prompts": [
            '"Download https://example.com/libc.so.6 using source_url and find one-gadget RCE offsets."',
            '"Fetch the libc from https://example.com/libc-2.31.so and find execve gadgets with one_gadget."',
        ],
    },
    "libc-database-mcp": {
        "type": "generic",
        "run_fn": "run_libc_database",
        "url_prompts": [
            '"Download https://example.com/libc.so.6 using source_url and identify its version with libc-database."',
            '"Fetch the libc binary from https://example.com/target-libc.so and look up known offsets."',
        ],
    },
    "pwninit-mcp": {
        "type": "generic",
        "run_fn": "run_pwninit",
        "url_prompts": [
            '"Download the challenge files from https://example.com/challenge.tar.gz using source_url and set up the environment with pwninit."',
            '"Fetch the CTF bundle from https://example.com/pwn-files.zip and initialize the exploit workspace."',
        ],
    },
    # ── Memory Forensics ──
    "volatility3-mcp": {
        "type": "generic",
        "run_fn": "run_volatility3",
        "url_prompts": [
            '"Download the memory dump from https://example.com/memdump.raw using source_url and list running processes with volatility3."',
            '"Fetch https://example.com/memory.dmp and analyze it for malware artifacts using volatility3."',
        ],
    },
    "volatility-mcp": {
        "type": "generic",
        "run_fn": "run_volatility",
        "url_prompts": [
            '"Download the memory image from https://example.com/memory.raw using source_url and analyze it with Volatility."',
            '"Fetch https://example.com/memdump.dmp and extract process listings with Volatility."',
        ],
    },
    # ── Forensics & Recovery ──
    "foremost-mcp": {
        "type": "generic",
        "run_fn": "run_foremost",
        "url_prompts": [
            '"Download the disk image from https://example.com/disk.dd using source_url and carve deleted files with foremost."',
            '"Fetch https://example.com/evidence.img and recover files from it using foremost."',
        ],
    },
    "steghide-mcp": {
        "type": "generic",
        "run_fn": "run_steghide",
        "url_prompts": [
            '"Download https://example.com/suspicious-image.jpg using source_url and check for hidden data with steghide."',
            '"Fetch https://example.com/stego.bmp and try to extract embedded payloads with steghide."',
        ],
    },
    "testdisk-mcp": {
        "type": "generic",
        "run_fn": "run_testdisk",
        "url_prompts": [
            '"Download the corrupted disk image from https://example.com/disk.img using source_url and attempt recovery with TestDisk."',
            '"Fetch https://example.com/partition.dd and analyze the partition table with TestDisk."',
        ],
    },
    # ── Vulnerability Scanning ──
    "trivy-mcp": {
        "type": "generic",
        "run_fn": "run_trivy",
        "url_prompts": [
            '"Scan the project at https://github.com/org/docker-app for vulnerabilities using trivy with source_url."',
            '"Download https://example.com/project.tar.gz and scan it for CVEs with trivy."',
        ],
    },
    "trivy-neutr0n-mcp": {
        "type": "generic",
        "run_fn": "run_trivy_neutr0n",
        "url_prompts": [
            '"Scan https://github.com/org/app for vulnerabilities using trivy-neutr0n with source_url."',
            '"Download the project from https://example.com/repo.tar.gz and check for known CVEs."',
        ],
    },
    "grype-mcp": {
        "type": "generic",
        "run_fn": "run_grype",
        "url_prompts": [
            '"Scan https://github.com/org/app for known vulnerabilities in its dependencies using grype with source_url."',
            '"Download https://example.com/sbom.json and check it for vulnerabilities with grype."',
        ],
    },
    "syft-mcp": {
        "type": "generic",
        "run_fn": "run_syft",
        "url_prompts": [
            '"Generate an SBOM for the project at https://github.com/org/app using syft with source_url."',
            '"Download https://example.com/container-image.tar and generate a software bill of materials with syft."',
        ],
    },
    "clair-mcp": {
        "type": "generic",
        "run_fn": "run_clair",
        "url_prompts": [
            '"Download the container image layers from https://example.com/image-layers.tar.gz using source_url and scan with Clair."',
            '"Fetch the image manifest from https://example.com/manifest.json and analyze it for CVEs with Clair."',
        ],
    },
    "aibom-mcp": {
        "type": "generic",
        "run_fn": "run_aibom",
        "url_prompts": [
            '"Generate an AI bill of materials for the ML project at https://github.com/org/ml-project using source_url."',
            '"Download https://example.com/model-repo.tar.gz and create an AIBOM for it."',
        ],
    },
    # ── YARA / Malware ──
    "yara-mcp": {
        "type": "generic",
        "run_fn": "run_yara",
        "url_prompts": [
            '"Download YARA rules from https://example.com/rules.yar using source_url and use them to scan a suspect file."',
            '"Fetch the malware sample from https://example.com/sample.bin and scan it with YARA rules."',
        ],
    },
    "yaraflux-mcp": {
        "type": "generic",
        "run_fn": "run_yaraflux",
        "url_prompts": [
            '"Download https://example.com/suspect-file.bin using source_url and scan it with YaraFlux rules."',
            '"Fetch the sample from https://example.com/malware.zip and analyze it with YaraFlux."',
        ],
    },
    # ── Password Cracking ──
    "john-mcp": {
        "type": "generic",
        "run_fn": "run_john",
        "url_prompts": [
            '"Download the hash file from https://example.com/hashes.txt using source_url and crack them with John the Ripper."',
            '"Fetch https://example.com/shadow.txt and attempt to crack the password hashes with john."',
        ],
    },
    "hashcat-mcp": {
        "type": "generic",
        "run_fn": "run_hashcat",
        "url_prompts": [
            '"Download https://example.com/ntlm-hashes.txt using source_url and crack them with hashcat."',
            '"Fetch the hash dump from https://example.com/hashes.zip and run hashcat with a wordlist attack."',
        ],
    },
    "hashpump-mcp": {
        "type": "generic",
        "run_fn": "run_hashpump",
        "url_prompts": [
            '"Download https://example.com/signed-data.bin using source_url and perform a hash length extension attack with hashpump."',
            '"Fetch the signed payload from https://example.com/message.dat and extend the hash with hashpump."',
        ],
    },
    # ── Network ──
    "wireshark-mcp": {
        "type": "generic",
        "run_fn": "run_wireshark",
        "url_prompts": [
            '"Download the pcap file from https://example.com/capture.pcap using source_url and analyze the network traffic."',
            '"Fetch https://example.com/traffic.pcapng and look for suspicious connections with Wireshark/tshark."',
        ],
    },
    # ── Compliance / Audit ──
    "docker-bench-security-mcp": {
        "type": "generic",
        "run_fn": "run_docker_bench_security",
        "url_prompts": [
            '"Download the Docker configuration from https://example.com/docker-config.tar.gz using source_url and audit it against CIS benchmarks."',
            '"Fetch https://example.com/docker-compose.yml and check it for security best practices with docker-bench-security."',
        ],
    },
    "lynis-mcp": {
        "type": "generic",
        "run_fn": "run_lynis",
        "url_prompts": [
            '"Download the audit profile from https://example.com/custom-profile.prf using source_url and run a Lynis security audit."',
            '"Fetch custom audit tests from https://example.com/lynis-tests.tar.gz and run Lynis with them."',
        ],
    },
    "kube-bench-mcp": {
        "type": "generic",
        "run_fn": "run_kube_bench",
        "url_prompts": [
            '"Download the CIS benchmark config from https://example.com/benchmark.yaml using source_url and run kube-bench."',
            '"Fetch custom configuration from https://example.com/kube-config.tar.gz and audit Kubernetes security with kube-bench."',
        ],
    },
    # ── Directory Brute-forcing ──
    "gobuster-mcp": {
        "type": "generic",
        "run_fn": "run_gobuster",
        "url_prompts": [
            '"Download the wordlist from https://example.com/custom-wordlist.txt using source_url and use gobuster to brute-force directories on the target."',
            '"Fetch https://example.com/large-wordlist.txt and enumerate directories on example.com with gobuster dir mode."',
        ],
    },
    "dirb-mcp": {
        "type": "generic",
        "run_fn": "run_dirb",
        "url_prompts": [
            '"Download the wordlist from https://example.com/wordlist.txt using source_url and use dirb to enumerate directories on the target."',
            '"Fetch https://example.com/custom-paths.txt and brute-force hidden paths with dirb."',
        ],
    },
    "dirsearch-mcp": {
        "type": "generic",
        "run_fn": "run_dirsearch",
        "url_prompts": [
            '"Download https://example.com/custom-wordlist.txt using source_url and use dirsearch to enumerate paths on the target."',
            '"Fetch a wordlist from https://example.com/extensions.txt and scan for hidden files with dirsearch."',
        ],
    },
    "feroxbuster-mcp": {
        "type": "generic",
        "run_fn": "run_feroxbuster",
        "url_prompts": [
            '"Download https://example.com/large-wordlist.txt using source_url and use feroxbuster for recursive directory enumeration on the target."',
            '"Fetch the wordlist from https://example.com/dirlist.txt and brute-force directories with feroxbuster."',
        ],
    },
    # ── Web Scanning ──
    "jaeles-mcp": {
        "type": "generic",
        "run_fn": "run_jaeles",
        "url_prompts": [
            '"Download custom signatures from https://example.com/signatures.yaml using source_url and scan the target with Jaeles."',
            '"Fetch the signature pack from https://example.com/jaeles-sigs.tar.gz and run Jaeles against the target."',
        ],
    },
    # ── IDS/IPS ──
    "falco-mcp": {
        "type": "generic",
        "run_fn": "run_falco",
        "url_prompts": [
            '"Download custom Falco rules from https://example.com/custom-rules.yaml using source_url and use them for runtime security monitoring."',
            '"Fetch the rule set from https://example.com/falco-rules.tar.gz and load them into Falco."',
        ],
    },
    "suricata-mcp": {
        "type": "generic",
        "run_fn": "run_suricata",
        "url_prompts": [
            '"Download the pcap file from https://example.com/capture.pcap using source_url and analyze it with Suricata IDS rules."',
            '"Fetch custom Suricata rules from https://example.com/rules.tar.gz and run them against the provided capture."',
        ],
    },
    # ── Explicit-path tools ──
    "titus-mcp": {
        "type": "explicit-path",
        "url_prompts": [
            '"Scan the repo at https://github.com/org/backend for leaked API keys, tokens, or secrets."',
            '"Check https://github.com/org/repo git history for any secrets that were committed and later removed."',
            '"Use download_file to fetch https://example.com/source.tar.gz, then scan the downloaded path for secrets."',
        ],
    },
    "julius-mcp": {
        "type": "explicit-path",
        "url_prompts": [
            '"Download custom probe definitions from https://example.com/custom-probes.yaml using download_file and validate them."',
            '"Fetch the probe file from https://example.com/probes.json and validate it with julius."',
        ],
    },
    # ── Download-only (cloudlist) ──
    "cloudlist-mcp": {
        "type": "download-only",
        "url_prompts": [
            '"Download the provider config from https://example.com/cloud-config.yaml using download_file and use it to list cloud assets."',
            '"Fetch my cloud provider configuration from https://example.com/providers.yaml and list all AWS assets."',
        ],
    },
}

# ---------------------------------------------------------------------------
# Shared Markdown blocks
# ---------------------------------------------------------------------------

DOWNLOAD_FILE_DOC = """### `download_file`

Download a file or repository from a URL into the container workspace. Use this to pre-download content before running multiple analyses on the same data.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | HTTP(S) URL, GitHub/GitLab repo URL, or `data:` URI |
| `extract` | boolean | No | `true` | Auto-extract archives (`.zip`, `.tar.gz`, etc.) |

Returns JSON with `path` (local file path to use in other tools) and `job_id` (for cleanup).

### `cleanup_downloads`

Remove downloaded files from the container workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `job_id` | string | No | `""` | Specific job ID to clean up. If empty, removes all downloads |

"""

ENV_VARS_ROWS = """| `HD_MAX_DOWNLOAD_MB` | `500` | Max file download size in MB (URL fetch) |
| `HD_FETCH_TIMEOUT` | `120` | Download timeout in seconds (URL fetch) |"""


def _add_source_url_param(content: str) -> str:
    """Add source_url row to the run_* parameter table."""
    pattern = (
        r'(\| `arguments` \| string \| Yes \| — \| Command-line arguments \(e\.g\. `"--help"`\) \|)'
    )
    replacement = (
        r'\1\n'
        r'| `source_url` | string | No | `""` | URL to download files into the container before running. '
        r'Supports HTTP(S) files, archives (auto-extracted), and GitHub/GitLab repo URLs. '
        r'Use `{source}` in arguments as a placeholder for the downloaded path. |'
    )
    return re.sub(pattern, replacement, content, count=1)


def _update_titus_path_desc(content: str) -> str:
    """Update path parameter description in titus scan_path and scan_git tables."""
    content = content.replace(
        "| `path` | string | Yes | — | File or directory path to scan |",
        "| `path` | string | Yes | — | Local path **or URL** to scan. Accepts a file/directory path, HTTP(S) URL, archive URL, or a GitHub/GitLab repo URL. URLs are downloaded into the container automatically |",
    )
    content = content.replace(
        "| `path` | string | Yes | — | Path to a git repository |",
        "| `path` | string | Yes | — | Local path **or URL** to a git repo. Accepts a directory path or a GitHub/GitLab repo URL (e.g. `https://github.com/org/repo`). URLs are cloned into the container automatically |",
    )
    return content


def _update_julius_path_desc(content: str) -> str:
    """Update path parameter description in julius validate_probes table."""
    content = content.replace(
        "| `path` | string | Yes | — | File path to the probe definition file to validate |",
        "| `path` | string | Yes | — | Local path **or URL** to the probe definition file to validate. HTTP(S) URLs are downloaded into the container automatically |",
    )
    return content


def _insert_download_tools(content: str) -> str:
    """Insert download_file and cleanup_downloads docs before ## Example Prompts."""
    marker = "## Example Prompts"
    if marker not in content:
        return content
    return content.replace(marker, DOWNLOAD_FILE_DOC + marker, 1)


def _append_url_prompts(content: str, prompts: list[str]) -> str:
    """Append URL-based example prompts to the Example Prompts section."""
    marker = "## Example Prompts"
    if marker not in content:
        return content

    idx = content.index(marker)
    rest = content[idx:]

    next_section = re.search(r'\n## (?!Example Prompts)', rest)
    if not next_section:
        return content

    insert_pos = idx + next_section.start()

    url_block = "\n**URL-based ingestion (no volume mounts needed):**\n\n"
    for p in prompts:
        url_block += f"- {p}\n"
    url_block += "\n"

    return content[:insert_pos] + url_block + content[insert_pos:]


def _add_env_vars(content: str) -> str:
    """Add HD_MAX_DOWNLOAD_MB and HD_FETCH_TIMEOUT to Environment Variables table."""
    if "HD_MAX_DOWNLOAD_MB" in content:
        return content

    pattern = r'(\| `MCP_PORT` \| [^\n]+)'
    match = re.search(pattern, content)
    if match:
        return content[:match.end()] + "\n" + ENV_VARS_ROWS + content[match.end():]
    return content


def update_readme(tool_name: str, meta: dict) -> bool:
    readme_path = BASE / tool_name / "README.md"
    if not readme_path.exists():
        print(f"  SKIP (no README): {tool_name}")
        return False

    content = readme_path.read_text()
    original = content

    if "download_file" in content and "source_url" in content:
        print(f"  SKIP (already updated): {tool_name}")
        return False

    tool_type = meta["type"]

    if tool_type == "generic":
        content = _add_source_url_param(content)
    elif tool_type == "explicit-path" and tool_name == "titus-mcp":
        content = _update_titus_path_desc(content)
    elif tool_type == "explicit-path" and tool_name == "julius-mcp":
        content = _update_julius_path_desc(content)

    content = _insert_download_tools(content)
    content = _append_url_prompts(content, meta["url_prompts"])
    content = _add_env_vars(content)

    if content == original:
        print(f"  UNCHANGED: {tool_name}")
        return False

    readme_path.write_text(content)
    print(f"  UPDATED: {tool_name}")
    return True


def main():
    print(f"Updating {len(TOOLS)} README.md files...\n")
    updated = 0
    for tool_name, meta in TOOLS.items():
        if update_readme(tool_name, meta):
            updated += 1
    print(f"\nDone: {updated}/{len(TOOLS)} files updated.")


if __name__ == "__main__":
    main()
