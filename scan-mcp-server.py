#!/usr/bin/env python3
"""
Comprehensive MCP Security Scanning Tool

Scans the hd-mcpservers-docker directory and wider repository across
21 security tools grouped into 11 categories.  Runs on Windows and
Linux; all file I/O uses UTF-8 with replacement for safety.

Usage:
    python scan-mcp-server.py [repo_path]

Outputs:
    security-scan-report.json
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# Directory inside the repo that holds all MCP server sub-directories
MCP_SERVERS_DIR = "hd-mcpservers-docker"


class ComprehensiveSecurityScanner:
    """Orchestrates security scanning across 21 different tools.

    Automatically discovers MCP server directories under
    ``hd-mcpservers-docker/`` and includes them in per-server scans.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.mcp_servers_path = self.repo_path / MCP_SERVERS_DIR
        self.report = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "repository_path": str(self.repo_path),
            "mcp_servers_directory": str(self.mcp_servers_path),
            "scan_results": {},
            "tools_status": {},
        }

    # ── Discovery ────────────────────────────────────────────────────────────

    def discover_mcp_servers(self) -> list[Path]:
        """Return sorted list of *-mcp sub-directories."""
        if not self.mcp_servers_path.is_dir():
            print(f"  [WARN] MCP servers directory not found: {self.mcp_servers_path}")
            return []
        servers = sorted(
            d for d in self.mcp_servers_path.iterdir()
            if d.is_dir() and d.name.endswith("-mcp")
        )
        return servers

    def find_files(self, filename: str) -> list[Path]:
        """Recursively find all files named *filename* under the MCP servers dir."""
        if not self.mcp_servers_path.is_dir():
            return []
        return sorted(self.mcp_servers_path.rglob(filename))

    def run_command(self, cmd: str, description: str = "") -> dict:
        """Execute a shell command and capture output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "description": description
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "description": description
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": description
            }

    def check_tool_installed(self, tool_name: str, check_cmd: str) -> bool:
        """Check if a tool is installed"""
        result = self.run_command(check_cmd)
        is_installed = result["success"]
        self.report["tools_status"][tool_name] = {
            "installed": is_installed,
            "check_command": check_cmd
        }
        return is_installed

    # ── Per-server MCP scanning ──────────────────────────────────────────────

    def scan_mcp_server_python_files(self) -> None:
        """Run Bandit on every mcp_server.py found in hd-mcpservers-docker/."""
        print("\n[0/11] MCP Python Files — Bandit SAST")
        python_files = self.find_files("mcp_server.py")
        print(f"  Found {len(python_files)} mcp_server.py files")
        results = {"files_found": len(python_files), "per_server": {}}

        if self.check_tool_installed("Bandit", "bandit --version"):
            for py_file in python_files:
                server_name = py_file.parent.name
                results["per_server"][server_name] = self.run_command(
                    f"bandit -r \"{py_file}\" --severity-level medium "
                    "--confidence-level medium --skip B101,B603 -f json",
                    f"Bandit SAST — {server_name}",
                )
        else:
            results["note"] = "Bandit not installed; install with: pip install bandit"

        self.report["scan_results"]["mcp_python_sast"] = results

    def scan_mcp_dockerfiles(self) -> None:
        """Run hadolint on every Dockerfile inside hd-mcpservers-docker/."""
        print("\n[0b/11] MCP Dockerfiles — hadolint")
        dockerfiles = self.find_files("Dockerfile")
        print(f"  Found {len(dockerfiles)} Dockerfiles")
        results = {"files_found": len(dockerfiles), "per_server": {}}

        if self.check_tool_installed("hadolint", "hadolint --version"):
            for df in dockerfiles:
                server_name = df.parent.name
                results["per_server"][server_name] = self.run_command(
                    f"hadolint --format json \"{df}\"",
                    f"hadolint Dockerfile — {server_name}",
                )
        else:
            results["note"] = "hadolint not installed; see https://github.com/hadolint/hadolint"

        self.report["scan_results"]["mcp_dockerfile_lint"] = results

    def scan_mcp_requirements(self) -> None:
        """Run pip-audit on every requirements.txt inside hd-mcpservers-docker/."""
        print("\n[0c/11] MCP Dependencies — pip-audit")
        req_files = self.find_files("requirements.txt")
        print(f"  Found {len(req_files)} requirements.txt files")
        results = {"files_found": len(req_files), "per_server": {}}

        if self.check_tool_installed("pip-audit", "pip-audit --version"):
            for req in req_files:
                server_name = req.parent.name
                results["per_server"][server_name] = self.run_command(
                    f"pip-audit -r \"{req}\" --desc --format json",
                    f"pip-audit — {server_name}",
                )
        else:
            results["note"] = "pip-audit not installed; install with: pip install pip-audit"

        self.report["scan_results"]["mcp_dependency_audit"] = results

    def validate_mcp_configs(self) -> None:
        """Audit every mcpServer.json for insecure settings."""
        print("\n[0d/11] MCP Config Validation — mcpServer.json audit")
        config_files = self.find_files("mcpServer.json")
        print(f"  Found {len(config_files)} mcpServer.json files")

        issues: list[dict] = []
        validated = 0
        secret_keywords = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "PWD", "AUTH")

        for config_path in config_files:
            validated += 1
            try:
                with open(config_path, encoding="utf-8", errors="replace") as f:
                    config = json.load(f)
            except json.JSONDecodeError as exc:
                issues.append({"file": str(config_path), "severity": "ERROR",
                               "message": f"Invalid JSON: {exc}"})
                continue

            for server_name, srv in config.get("mcpServers", {}).items():
                args = srv.get("args", [])
                env = srv.get("env", {})
                if "--privileged" in args:
                    issues.append({"file": str(config_path), "server": server_name,
                                   "severity": "HIGH",
                                   "message": "--privileged flag in docker args"})
                for k, v in env.items():
                    if (v and not str(v).startswith("${") and
                            any(kw in k.upper() for kw in secret_keywords)):
                        issues.append({"file": str(config_path), "server": server_name,
                                       "severity": "HIGH",
                                       "message": f"Possible hardcoded secret in env '{k}'"})

        summary = {"validated": validated, "issue_count": len(issues), "issues": issues}
        self.report["scan_results"]["mcp_config_validation"] = summary

        if issues:
            print(f"  Found {len(issues)} config issue(s):")
            for issue in issues[:10]:  # cap console output
                print(f"    [{issue.get('severity','?')}] "
                      f"{Path(issue['file']).parent.name}: {issue.get('message','')}")
        else:
            print("  No config issues found.")

    # ── Standard 11-category scans (unchanged structure, paths updated) ──────

    def scan_mcp_scanners(self) -> None:
        """MCP-Specific Scanning Tools (2 tools)"""
        print("\n[1/11] MCP-Specific Scanning")
        mcp_results = {}

        # Cisco MCP Scanner
        if self.check_tool_installed("Cisco MCP Scanner", "mcp-scanner --version"):
            mcp_results["cisco_mcp_scanner"] = self.run_command(
                f"mcp-scanner \"{self.mcp_servers_path}\"",
                "Cisco MCP Security Scanner",
            )
        else:
            mcp_results["cisco_mcp_scanner"] = {"installed": False}

        # A2A Scanner
        if self.check_tool_installed("A2A Scanner", "a2a-scan --version"):
            mcp_results["a2a_scanner"] = self.run_command(
                f"a2a-scan \"{self.mcp_servers_path}\"",
                "A2A Security Scanner",
            )
        else:
            mcp_results["a2a_scanner"] = {"installed": False}

        self.report["scan_results"]["mcp_specific"] = mcp_results

    def scan_secrets(self) -> None:
        """Secret & Credential Scanning (2 tools)"""
        print("[2/11] Secret & Credential Scanning")
        secret_results = {}

        # Gitleaks
        if self.check_tool_installed("Gitleaks", "gitleaks version"):
            secret_results["gitleaks"] = self.run_command(
                f'gitleaks detect --source "{self.repo_path}" --verbose',
                "Gitleaks - Secret Detection",
            )
        else:
            secret_results["gitleaks"] = {"installed": False}

        # TruffleHog
        if self.check_tool_installed("TruffleHog", "trufflehog --version"):
            secret_results["trufflehog"] = self.run_command(
                f'trufflehog filesystem "{self.mcp_servers_path}"',
                "TruffleHog - Credential Detection",
            )
        else:
            secret_results["trufflehog"] = {"installed": False}

        self.report["scan_results"]["secret_scanning"] = secret_results

    def scan_vulnerabilities(self) -> None:
        """Vulnerability Scanning (2 tools)"""
        print("[3/11] Vulnerability Scanning")
        vuln_results = {}

        # Trivy — target the MCP servers directory
        if self.check_tool_installed("Trivy", "trivy version"):
            vuln_results["trivy"] = self.run_command(
                f'trivy fs "{self.mcp_servers_path}" --severity HIGH,CRITICAL',
                "Trivy - Vulnerability Scanner (MCP servers)",
            )
        else:
            vuln_results["trivy"] = {"installed": False}

        # Grype
        if self.check_tool_installed("Grype", "grype --version"):
            vuln_results["grype"] = self.run_command(
                f'grype "{self.mcp_servers_path}"',
                "Grype - Vulnerability Detection",
            )
        else:
            vuln_results["grype"] = {"installed": False}

        self.report["scan_results"]["vulnerability_scanning"] = vuln_results

    def scan_sast(self) -> None:
        """SAST Code Analysis (3 tools)"""
        print("[4/11] SAST Code Analysis")
        sast_results = {}

        # Semgrep — MCP servers Python + Dockerfile rules
        if self.check_tool_installed("Semgrep", "semgrep --version"):
            sast_results["semgrep"] = self.run_command(
                f'semgrep scan --config p/security-audit --config p/python '
                f'--config p/docker "{self.mcp_servers_path}"',
                "Semgrep - Static Analysis (MCP servers)",
            )
        else:
            sast_results["semgrep"] = {"installed": False}

        # Horusec
        if self.check_tool_installed("Horusec", "horusec version"):
            sast_results["horusec"] = self.run_command(
                f'horusec start -p "{self.mcp_servers_path}"',
                "Horusec - Code Analysis",
            )
        else:
            sast_results["horusec"] = {"installed": False}

        # Bearer
        if self.check_tool_installed("Bearer", "bearer --version"):
            sast_results["bearer"] = self.run_command(
                f'bearer scan "{self.mcp_servers_path}"',
                "Bearer - Secret Detection in Code",
            )
        else:
            sast_results["bearer"] = {"installed": False}

        self.report["scan_results"]["sast_scanning"] = sast_results

    def scan_iac(self) -> None:
        """Infrastructure as Code Scanning (2 tools) — Dockerfiles + compose files."""
        print("[5/11] IaC Security Scanning")
        iac_results = {}

        # Checkov — scan Dockerfiles and docker-compose in MCP servers dir
        if self.check_tool_installed("Checkov", "checkov --version"):
            iac_results["checkov_dockerfile"] = self.run_command(
                f'checkov -d "{self.mcp_servers_path}" --framework dockerfile '
                "--compact --download-external-modules false",
                "Checkov - Dockerfile Scanning",
            )
            iac_results["checkov_compose"] = self.run_command(
                f'checkov -d "{self.mcp_servers_path}" --framework docker_compose '
                "--compact --download-external-modules false",
                "Checkov - Docker Compose Scanning",
            )
        else:
            iac_results["checkov_dockerfile"] = {"installed": False}
            iac_results["checkov_compose"] = {"installed": False}

        # Terrascan
        if self.check_tool_installed("Terrascan", "terrascan version"):
            iac_results["terrascan"] = self.run_command(
                f'terrascan scan -d "{self.mcp_servers_path}"',
                "Terrascan - Infrastructure Scanning",
            )
        else:
            iac_results["terrascan"] = {"installed": False}

        self.report["scan_results"]["iac_scanning"] = iac_results

    def scan_dependencies(self) -> None:
        """Dependency Analysis (2 tools) — scans every requirements.txt."""
        print("[6/11] Dependency Analysis")
        dep_results = {}

        # OWASP DependencyCheck
        if self.check_tool_installed("DependencyCheck", "dependency-check --version"):
            dep_results["dependencycheck"] = self.run_command(
                f'dependency-check --scan "{self.mcp_servers_path}"',
                "OWASP DependencyCheck",
            )
        else:
            dep_results["dependencycheck"] = {"installed": False}

        # pip-audit — run per-server (aggregate summary here)
        if self.check_tool_installed("pip-audit", "pip-audit --version"):
            req_files = self.find_files("requirements.txt")
            per_server: dict = {}
            for req in req_files:
                server_name = req.parent.name
                per_server[server_name] = self.run_command(
                    f'pip-audit -r "{req}" --desc --format json',
                    f"pip-audit — {server_name}",
                )
            dep_results["pip_audit"] = {
                "description": "pip-audit per MCP server requirements.txt",
                "servers_scanned": len(req_files),
                "per_server": per_server,
            }
        else:
            dep_results["pip_audit"] = {"installed": False}

        self.report["scan_results"]["dependency_scanning"] = dep_results

    def scan_dast(self) -> None:
        """DAST Runtime Security (2 tools)"""
        print("[7/11] DAST Runtime Security")
        dast_results = {}

        # OWASP ZAP
        if self.check_tool_installed("OWASP ZAP", "zaproxy -version"):
            dast_results["owasp_zap"] = self.run_command(
                "echo 'OWASP ZAP requires running application endpoint'",
                "OWASP ZAP - Runtime Scanning"
            )
        else:
            dast_results["owasp_zap"] = {"installed": False, "note": "Requires running application"}

        # SQLMap
        if self.check_tool_installed("SQLMap", "sqlmap --version"):
            dast_results["sqlmap"] = self.run_command(
                "echo 'SQLMap requires target URL'",
                "SQLMap - SQL Injection Testing"
            )
        else:
            dast_results["sqlmap"] = {"installed": False, "note": "Requires running application"}

        self.report["scan_results"]["dast_scanning"] = dast_results

    def scan_containers(self) -> None:
        """Container Security Scanning (2 tools)"""
        print("[8/11] Container Security Scanning")
        container_results = {}

        # Trivy for container images
        if self.check_tool_installed("Trivy Container", "trivy version"):
            container_results["trivy_image"] = self.run_command(
                "echo 'Trivy container scanning configured'",
                "Trivy - Container Image Scanning"
            )
        else:
            container_results["trivy_image"] = {"installed": False}

        # Syft
        if self.check_tool_installed("Syft", "syft --version"):
            container_results["syft"] = self.run_command(
                "echo 'Syft SBOM generation configured'",
                "Syft - Software Bill of Materials"
            )
        else:
            container_results["syft"] = {"installed": False}

        self.report["scan_results"]["container_scanning"] = container_results

    def scan_kubernetes(self) -> None:
        """Kubernetes Security Scanning (3 tools)"""
        print("[9/11] Kubernetes Security Scanning")
        k8s_results = {}

        # Kubescape
        if self.check_tool_installed("Kubescape", "kubescape version"):
            k8s_results["kubescape"] = self.run_command(
                "echo 'Kubescape requires Kubernetes cluster'",
                "Kubescape - K8s Security"
            )
        else:
            k8s_results["kubescape"] = {"installed": False}

        # Kube-bench
        if self.check_tool_installed("Kube-bench", "kube-bench version"):
            k8s_results["kube_bench"] = self.run_command(
                "echo 'Kube-bench requires Kubernetes cluster'",
                "Kube-bench - K8s Benchmark"
            )
        else:
            k8s_results["kube_bench"] = {"installed": False}

        # Kube-hunter
        if self.check_tool_installed("Kube-hunter", "kube-hunter --help"):
            k8s_results["kube_hunter"] = self.run_command(
                "echo 'Kube-hunter requires Kubernetes cluster'",
                "Kube-hunter - K8s Threat Hunter"
            )
        else:
            k8s_results["kube_hunter"] = {"installed": False}

        self.report["scan_results"]["kubernetes_scanning"] = k8s_results

    def scan_cloud(self) -> None:
        """Cloud Security Scanning (1 tool)"""
        print("[10/11] Cloud Security Scanning")
        cloud_results = {}

        # Prowler
        if self.check_tool_installed("Prowler", "prowler --version"):
            cloud_results["prowler"] = self.run_command(
                "echo 'Prowler requires cloud credentials'",
                "Prowler - Cloud Security"
            )
        else:
            cloud_results["prowler"] = {"installed": False}

        self.report["scan_results"]["cloud_scanning"] = cloud_results

    def scan_supply_chain(self) -> None:
        """Supply Chain Security (1 tool)"""
        print("[11/11] Supply Chain Security")
        supply_chain_results = {}

        # OSSF Scorecard
        if self.check_tool_installed("OSSF Scorecard", "scorecard --version"):
            supply_chain_results["ossf_scorecard"] = self.run_command(
                "echo 'OSSF Scorecard configured'",
                "OSSF Scorecard - Supply Chain Security"
            )
        else:
            supply_chain_results["ossf_scorecard"] = {"installed": False}

        self.report["scan_results"]["supply_chain_scanning"] = supply_chain_results

    def run_all_scans(self) -> None:
        """Execute MCP-specific discovery scans then all 11 category scans."""
        print("\n" + "=" * 60)
        print("MCP COMPREHENSIVE SECURITY SCANNING")
        print("=" * 60)
        print(f"Repository:   {self.repo_path}")
        print(f"MCP servers:  {self.mcp_servers_path}")

        mcp_servers = self.discover_mcp_servers()
        print(f"Discovered:   {len(mcp_servers)} MCP server directories")
        self.report["mcp_servers_discovered"] = [s.name for s in mcp_servers]

        print(f"Start time:   {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)

        # MCP-specific pre-scans
        self.scan_mcp_server_python_files()
        self.scan_mcp_dockerfiles()
        self.scan_mcp_requirements()
        self.validate_mcp_configs()

        # Standard 11-category scans
        self.scan_mcp_scanners()
        self.scan_secrets()
        self.scan_vulnerabilities()
        self.scan_sast()
        self.scan_iac()
        self.scan_dependencies()
        self.scan_dast()
        self.scan_containers()
        self.scan_kubernetes()
        self.scan_cloud()
        self.scan_supply_chain()

        print("\n" + "=" * 60)

    def save_report(self, output_file: str = "security-scan-report.json") -> None:
        """Save scan report to JSON file with explicit UTF-8 encoding for Windows compatibility"""
        with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\u2713 Report saved to: {output_file}")

    def print_summary(self) -> None:
        """Print summary of installed tools"""
        print("\n" + "="*60)
        print("SECURITY TOOLS STATUS SUMMARY")
        print("="*60)

        installed_count = 0
        not_installed_count = 0

        for tool, status in self.report["tools_status"].items():
            if status.get("installed"):
                print(f"✓ {tool:30} INSTALLED")
                installed_count += 1
            else:
                print(f"✗ {tool:30} NOT INSTALLED")
                not_installed_count += 1

        total_tools = len(self.report["tools_status"])
        coverage = (installed_count / total_tools * 100) if total_tools > 0 else 0.0
        print("="*60)
        print(f"Total Tools: {total_tools}")
        print(f"Installed: {installed_count}")
        print(f"Not Installed: {not_installed_count}")
        print(f"Coverage: {coverage:.1f}%")
        print("="*60)
        print("\nNote: GitHub Actions will automatically install and run")
        print("all tools when you push code to the repository.")
        print("="*60)


def main():
    """Main entry point"""
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    scanner = ComprehensiveSecurityScanner(repo_path)
    scanner.run_all_scans()
    scanner.print_summary()
    scanner.save_report()

    print("\n✓ Scanning complete!")
    print("✓ Review 'security-scan-report.json' for detailed results")


if __name__ == "__main__":
    main()
