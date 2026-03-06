<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# hd-mcpservers-docker

Registry of **184 containerized MCP servers** for security tools, ready for deployment on [Hackerdogs](https://hackerdogs.ai).

Each tool is wrapped as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server using [FastMCP](https://github.com/jlowin/fastmcp), supporting both **stdio** and **HTTP streamable** transports. All tools are packaged as multi-architecture Docker images (linux/amd64, linux/arm64).

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Tool Registry

### Phase 1 — Core Security Tools (17 tools)

| # | Tool | Source | Description | Port | Image |
|---|------|--------|-------------|------|-------|
| 1 | [julius-mcp](./julius-mcp/) | [praetorian-inc/julius](https://github.com/praetorian-inc/julius) | LLM service fingerprinting | 8100 | `hackerdogs/julius-mcp` |
| 2 | [augustus-mcp](./augustus-mcp/) | [praetorian-inc/augustus](https://github.com/praetorian-inc/augustus) | LLM adversarial vulnerability testing | 8101 | `hackerdogs/augustus-mcp` |
| 3 | [brutus-mcp](./brutus-mcp/) | [praetorian-inc/brutus](https://github.com/praetorian-inc/brutus) | Multi-protocol credential testing | 8102 | `hackerdogs/brutus-mcp` |
| 4 | [titus-mcp](./titus-mcp/) | [praetorian-inc/titus](https://github.com/praetorian-inc/titus) | Secrets scanning (code, files, git) | 8103 | `hackerdogs/titus-mcp` |
| 5 | [nerva-mcp](./nerva-mcp/) | [praetorian-inc/nerva](https://github.com/praetorian-inc/nerva) | Network service fingerprinting | 8104 | `hackerdogs/nerva-mcp` |
| 6 | [naabu-mcp](./naabu-mcp/) | [projectdiscovery/naabu](https://github.com/projectdiscovery/naabu) | Fast port scanning | 8105 | `hackerdogs/naabu-mcp` |
| 7 | [cvemap-mcp](./cvemap-mcp/) | [projectdiscovery/cvemap](https://github.com/projectdiscovery/cvemap) | CVE search and exploration | 8106 | `hackerdogs/cvemap-mcp` |
| 8 | [uncover-mcp](./uncover-mcp/) | [projectdiscovery/uncover](https://github.com/projectdiscovery/uncover) | Exposed host discovery (Shodan, Censys, FOFA) | 8107 | `hackerdogs/uncover-mcp` |
| 9 | [dnsx-mcp](./dnsx-mcp/) | [projectdiscovery/dnsx](https://github.com/projectdiscovery/dnsx) | DNS query toolkit | 8108 | `hackerdogs/dnsx-mcp` |
| 10 | [tlsx-mcp](./tlsx-mcp/) | [projectdiscovery/tlsx](https://github.com/projectdiscovery/tlsx) | TLS certificate scanning | 8109 | `hackerdogs/tlsx-mcp` |
| 11 | [asnmap-mcp](./asnmap-mcp/) | [projectdiscovery/asnmap](https://github.com/projectdiscovery/asnmap) | ASN-to-network mapping | 8110 | `hackerdogs/asnmap-mcp` |
| 12 | [cloudlist-mcp](./cloudlist-mcp/) | [projectdiscovery/cloudlist](https://github.com/projectdiscovery/cloudlist) | Cloud asset discovery | 8111 | `hackerdogs/cloudlist-mcp` |
| 13 | [urlfinder-mcp](./urlfinder-mcp/) | [projectdiscovery/urlfinder](https://github.com/projectdiscovery/urlfinder) | Passive URL discovery | 8112 | `hackerdogs/urlfinder-mcp` |
| 14 | [tldfinder-mcp](./tldfinder-mcp/) | [projectdiscovery/tldfinder](https://github.com/projectdiscovery/tldfinder) | Private TLD discovery | 8113 | `hackerdogs/tldfinder-mcp` |
| 15 | [wappalyzergo-mcp](./wappalyzergo-mcp/) | [projectdiscovery/wappalyzergo](https://github.com/projectdiscovery/wappalyzergo) | Web technology detection | 8114 | `hackerdogs/wappalyzergo-mcp` |
| 16 | [openrisk-mcp](./openrisk-mcp/) | [projectdiscovery/openrisk](https://github.com/projectdiscovery/openrisk) | Risk scoring from Nuclei output | 8115 | `hackerdogs/openrisk-mcp` |
| 17 | [vulnx-mcp](./vulnx-mcp/) | [projectdiscovery/cvemap](https://github.com/projectdiscovery/cvemap) | Vulnerability search and analysis | 8116 | `hackerdogs/vulnx-mcp` |

### Phase 2 — Penetration Testing & Offensive Security (85 tools)

| # | Tool | Source | Description | Port | Image |
|---|------|--------|-------------|------|-------|
| 18 | [rustscan-mcp](./rustscan-mcp/) | [RustScan/RustScan](https://github.com/RustScan/RustScan) | Ultra-fast port scanning | 8200 | `hackerdogs/rustscan-mcp` |
| 19 | [autorecon-mcp](./autorecon-mcp/) | [Tib3rius/AutoRecon](https://github.com/Tib3rius/AutoRecon) | Automated reconnaissance | 8201 | `hackerdogs/autorecon-mcp` |
| 20 | [fierce-mcp](./fierce-mcp/) | [msaffron/fierce](https://github.com/msaffron/fierce) | DNS reconnaissance and zone transfer testing | 8202 | `hackerdogs/fierce-mcp` |
| 21 | [dnsrecon-mcp](./dnsrecon-mcp/) | [darkoperator/dnsrecon](https://github.com/darkoperator/dnsrecon) | DNS information gathering and brute forcing | 8203 | `hackerdogs/dnsrecon-mcp` |
| 22 | [theharvester-mcp](./theharvester-mcp/) | [laramies/theHarvester](https://github.com/laramies/theHarvester) | Email and subdomain harvesting | 8204 | `hackerdogs/theharvester-mcp` |
| 23 | [arp-scan-mcp](./arp-scan-mcp/) | [royhills/arp-scan](https://github.com/royhills/arp-scan) | Network discovery using ARP requests | 8205 | `hackerdogs/arp-scan-mcp` |
| 24 | [nbtscan-mcp](./nbtscan-mcp/) | [residuum/nbtscan](https://github.com/residuum/nbtscan) | NetBIOS name scanning | 8206 | `hackerdogs/nbtscan-mcp` |
| 25 | [responder-mcp](./responder-mcp/) | [lgandx/Responder](https://github.com/lgandx/Responder) | LLMNR/NBT-NS/MDNS poisoner for credential harvesting | 8207 | `hackerdogs/responder-mcp` |
| 26 | [crackmapexec-mcp](./crackmapexec-mcp/) | [byt3bl33d3r/CrackMapExec](https://github.com/byt3bl33d3r/CrackMapExec) | Network service exploitation (SMB, WinRM) | 8208 | `hackerdogs/crackmapexec-mcp` |
| 27 | [enum4linux-mcp](./enum4linux-mcp/) | [portcullislab/enum4linux](https://github.com/portcullislab/enum4linux) | SMB enumeration (users, groups, shares) | 8209 | `hackerdogs/enum4linux-mcp` |
| 28 | [enum4linux-ng-mcp](./enum4linux-ng-mcp/) | [cddc/enum4linux-ng](https://github.com/cddc/enum4linux-ng) | Advanced SMB enumeration with enhanced logging | 8210 | `hackerdogs/enum4linux-ng-mcp` |
| 29 | [smbmap-mcp](./smbmap-mcp/) | [ShaunBarton/smbmap](https://github.com/ShaunBarton/smbmap) | SMB share enumeration and exploitation | 8211 | `hackerdogs/smbmap-mcp` |
| 30 | [netexec-mcp](./netexec-mcp/) | [PwnDexter/NetExec](https://github.com/PwnDexter/NetExec) | Network service exploitation (formerly CrackMapExec) | 8212 | `hackerdogs/netexec-mcp` |
| 31 | [gobuster-mcp](./gobuster-mcp/) | [OWASP/gobuster](https://github.com/OWASP/gobuster) | Directory/file/DNS enumeration | 8213 | `hackerdogs/gobuster-mcp` |
| 32 | [dirb-mcp](./dirb-mcp/) | [darkoperator/dirb](https://github.com/darkoperator/dirb) | Web content scanner with recursive scanning | 8214 | `hackerdogs/dirb-mcp` |
| 33 | [dirsearch-mcp](./dirsearch-mcp/) | [maurosoria/dirsearch](https://github.com/maurosoria/dirsearch) | Directory and file discovery | 8215 | `hackerdogs/dirsearch-mcp` |
| 34 | [feroxbuster-mcp](./feroxbuster-mcp/) | [epi052/feroxbuster](https://github.com/epi052/feroxbuster) | Recursive content discovery with filtering | 8216 | `hackerdogs/feroxbuster-mcp` |
| 35 | [hakrawler-mcp](./hakrawler-mcp/) | [hakluke/hakrawler](https://github.com/hakluke/hakrawler) | Fast web endpoint discovery and crawling | 8217 | `hackerdogs/hakrawler-mcp` |
| 36 | [gau-mcp](./gau-mcp/) | [lc/gau](https://github.com/lc/gau) | Get All URLs (Wayback, Common Crawl) | 8218 | `hackerdogs/gau-mcp` |
| 37 | [nikto-mcp](./nikto-mcp/) | [sullo/nikto](https://github.com/sullo/nikto) | Web server vulnerability scanner | 8219 | `hackerdogs/nikto-mcp` |
| 38 | [wpscan-mcp](./wpscan-mcp/) | [wpscanteam/wpscan](https://github.com/wpscanteam/wpscan) | WordPress security scanner | 8220 | `hackerdogs/wpscan-mcp` |
| 39 | [dalfox-mcp](./dalfox-mcp/) | [hahwul/dalfox](https://github.com/hahwul/dalfox) | XSS vulnerability scanning with DOM analysis | 8221 | `hackerdogs/dalfox-mcp` |
| 40 | [xsser-mcp](./xsser-mcp/) | [epsylon/xsser](https://github.com/epsylon/xsser) | XSS vulnerability testing | 8222 | `hackerdogs/xsser-mcp` |
| 41 | [dotdotpwn-mcp](./dotdotpwn-mcp/) | [wireghoul/dotdotpwn](https://github.com/wireghoul/dotdotpwn) | Directory traversal testing | 8223 | `hackerdogs/dotdotpwn-mcp` |
| 42 | [wfuzz-mcp](./wfuzz-mcp/) | [xmendez/wfuzz](https://github.com/xmendez/wfuzz) | Web application fuzzer | 8224 | `hackerdogs/wfuzz-mcp` |
| 43 | [commix-mcp](./commix-mcp/) | [commixproject/commix](https://github.com/commixproject/commix) | Command injection exploitation | 8225 | `hackerdogs/commix-mcp` |
| 44 | [paramspider-mcp](./paramspider-mcp/) | [devanshbatham/ParamSpider](https://github.com/devanshbatham/ParamSpider) | Parameter mining from web archives | 8226 | `hackerdogs/paramspider-mcp` |
| 45 | [qsreplace-mcp](./qsreplace-mcp/) | [projectdiscovery/qsreplace](https://github.com/projectdiscovery/qsreplace) | Query string parameter replacement | 8227 | `hackerdogs/qsreplace-mcp` |
| 46 | [uro-mcp](./uro-mcp/) | [projectdiscovery/uro](https://github.com/projectdiscovery/uro) | URL filtering and deduplication | 8228 | `hackerdogs/uro-mcp` |
| 47 | [anew-mcp](./anew-mcp/) | [projectdiscovery/anew](https://github.com/projectdiscovery/anew) | Append new lines for efficient data processing | 8229 | `hackerdogs/anew-mcp` |
| 48 | [wafw00f-mcp](./wafw00f-mcp/) | [EnableSecurity/wafw00f](https://github.com/EnableSecurity/wafw00f) | Web application firewall fingerprinting | 8230 | `hackerdogs/wafw00f-mcp` |
| 49 | [zap-mcp](./zap-mcp/) | [zaproxy/zap-core](https://github.com/zaproxy/zap-core) | OWASP ZAP automated security scanning proxy | 8231 | `hackerdogs/zap-mcp` |
| 50 | [jaeles-mcp](./jaeles-mcp/) | [jaeles-project/jaeles](https://github.com/jaeles-project/jaeles) | Vulnerability scanning with custom signatures | 8232 | `hackerdogs/jaeles-mcp` |
| 51 | [hydra-mcp](./hydra-mcp/) | [vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra) | Network login cracker (50+ protocols) | 8233 | `hackerdogs/hydra-mcp` |
| 52 | [john-mcp](./john-mcp/) | [openwall/john](https://github.com/openwall/john) | Password hash cracking with custom rules | 8234 | `hackerdogs/john-mcp` |
| 53 | [hashcat-mcp](./hashcat-mcp/) | [hashcat/hashcat](https://github.com/hashcat/hashcat) | GPU-accelerated password recovery | 8235 | `hackerdogs/hashcat-mcp` |
| 54 | [metasploit-mcp](./metasploit-mcp/) | [rapid7/metasploit-framework](https://github.com/rapid7/metasploit-framework) | Exploitation framework (module runner) | 8236 | `hackerdogs/metasploit-mcp` |
| 55 | [peda-mcp](./peda-mcp/) | [longld/peda](https://github.com/longld/peda) | GDB with PEDA for exploit development | 8237 | `hackerdogs/peda-mcp` |
| 56 | [gef-mcp](./gef-mcp/) | [hugsy/gef](https://github.com/hugsy/gef) | GDB Enhanced Features for exploit development | 8238 | `hackerdogs/gef-mcp` |
| 57 | [radare2-mcp](./radare2-mcp/) | [radareorg/radare2](https://github.com/radareorg/radare2) | Reverse engineering framework | 8239 | `hackerdogs/radare2-mcp` |
| 58 | [ghidra-mcp](./ghidra-mcp/) | [NationalSecurityAgency/ghidra](https://github.com/NationalSecurityAgency/ghidra) | NSA reverse engineering suite (headless) | 8240 | `hackerdogs/ghidra-mcp` |
| 59 | [binwalk-mcp](./binwalk-mcp/) | [ReFirmLabs/binwalk](https://github.com/ReFirmLabs/binwalk) | Firmware analysis and extraction | 8241 | `hackerdogs/binwalk-mcp` |
| 60 | [ropgadget-mcp](./ropgadget-mcp/) | [JonathanSalwan/ROPgadget](https://github.com/JonathanSalwan/ROPgadget) | ROP/JOP gadget finder | 8242 | `hackerdogs/ropgadget-mcp` |
| 61 | [ropper-mcp](./ropper-mcp/) | [sashs/Ropper](https://github.com/sashs/Ropper) | ROP gadget finder and exploit dev tool | 8243 | `hackerdogs/ropper-mcp` |
| 62 | [checksec-mcp](./checksec-mcp/) | [slimm609/checksec.sh](https://github.com/slimm609/checksec.sh) | Binary security property checker | 8244 | `hackerdogs/checksec-mcp` |
| 63 | [pwntools-mcp](./pwntools-mcp/) | [Gallopsled/pwntools](https://github.com/Gallopsled/pwntools) | CTF framework and exploit development | 8245 | `hackerdogs/pwntools-mcp` |
| 64 | [angr-mcp](./angr-mcp/) | [angr/angr](https://github.com/angr/angr) | Binary analysis with symbolic execution | 8246 | `hackerdogs/angr-mcp` |
| 65 | [volatility3-mcp](./volatility3-mcp/) | [volatilityfoundation/volatility3](https://github.com/volatilityfoundation/volatility3) | Next-generation memory forensics | 8247 | `hackerdogs/volatility3-mcp` |
| 66 | [volatility-mcp](./volatility-mcp/) | [volatilityfoundation/volatility](https://github.com/volatilityfoundation/volatility) | Memory forensics framework (v2) | 8248 | `hackerdogs/volatility-mcp` |
| 67 | [foremost-mcp](./foremost-mcp/) | [kdz/foremost](https://github.com/kdz/foremost) | File carving and data recovery | 8249 | `hackerdogs/foremost-mcp` |
| 68 | [steghide-mcp](./steghide-mcp/) | [StefanHetze/steghide](https://github.com/StefanHetze/steghide) | Steganography detection and extraction | 8250 | `hackerdogs/steghide-mcp` |
| 69 | [scoutsuite-mcp](./scoutsuite-mcp/) | [nccgroup/ScoutSuite](https://github.com/nccgroup/ScoutSuite) | Multi-cloud security auditing | 8251 | `hackerdogs/scoutsuite-mcp` |
| 70 | [kube-hunter-mcp](./kube-hunter-mcp/) | [aquasecurity/kube-hunter](https://github.com/aquasecurity/kube-hunter) | Kubernetes penetration testing | 8252 | `hackerdogs/kube-hunter-mcp` |
| 71 | [kube-bench-mcp](./kube-bench-mcp/) | [aquasecurity/kube-bench](https://github.com/aquasecurity/kube-bench) | CIS Kubernetes benchmark checker | 8253 | `hackerdogs/kube-bench-mcp` |
| 72 | [docker-bench-security-mcp](./docker-bench-security-mcp/) | [docker/docker-bench-security](https://github.com/docker/docker-bench-security) | Docker security assessment (CIS) | 8254 | `hackerdogs/docker-bench-security-mcp` |
| 73 | [social-analyzer-mcp](./social-analyzer-mcp/) | [qeeqbox/social-analyzer](https://github.com/qeeqbox/social-analyzer) | Social media analysis and OSINT | 8255 | `hackerdogs/social-analyzer-mcp` |
| 74 | [recon-ng-mcp](./recon-ng-mcp/) | [lanmaster53/recon-ng](https://github.com/lanmaster53/recon-ng) | Web reconnaissance framework (modular) | 8256 | `hackerdogs/recon-ng-mcp` |
| 75 | [spiderfoot-mcp](./spiderfoot-mcp/) | [smicallef/spiderfoot](https://github.com/smicallef/spiderfoot) | OSINT automation (200+ modules) | 8257 | `hackerdogs/spiderfoot-mcp` |
| 76 | [trufflehog-mcp](./trufflehog-mcp/) | [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | Git repository secret scanning | 8258 | `hackerdogs/trufflehog-mcp` |
| 77 | [aquatone-mcp](./aquatone-mcp/) | [michenriksen/aquatone](https://github.com/michenriksen/aquatone) | Visual inspection of websites across hosts | 8259 | `hackerdogs/aquatone-mcp` |
| 78 | [subjack-mcp](./subjack-mcp/) | [haccer/subjack](https://github.com/haccer/subjack) | Subdomain takeover vulnerability checker | 8260 | `hackerdogs/subjack-mcp` |
| 79 | [medusa-mcp](./medusa-mcp/) | [jmk-foofus/medusa](https://github.com/jmk-foofus/medusa) | Parallel modular login brute-forcer | 8261 | `hackerdogs/medusa-mcp` |
| 80 | [patator-mcp](./patator-mcp/) | [lanjelot/patator](https://github.com/lanjelot/patator) | Multi-purpose brute-forcer | 8262 | `hackerdogs/patator-mcp` |
| 81 | [evil-winrm-mcp](./evil-winrm-mcp/) | [Hackplayers/evil-winrm](https://github.com/Hackplayers/evil-winrm) | Windows Remote Management shell | 8263 | `hackerdogs/evil-winrm-mcp` |
| 82 | [hashid-mcp](./hashid-mcp/) | [psypanda/hashid](https://github.com/psypanda/hashid) | Hash algorithm identifier | 8264 | `hackerdogs/hashid-mcp` |
| 83 | [jwt-tool-mcp](./jwt-tool-mcp/) | [ticarpi/jwt_tool](https://github.com/ticarpi/jwt_tool) | JWT testing and algorithm confusion | 8265 | `hackerdogs/jwt-tool-mcp` |
| 84 | [nosqlmap-mcp](./nosqlmap-mcp/) | [codingo/NoSQLMap](https://github.com/codingo/NoSQLMap) | NoSQL injection testing | 8266 | `hackerdogs/nosqlmap-mcp` |
| 85 | [tplmap-mcp](./tplmap-mcp/) | [epinna/tplmap](https://github.com/epinna/tplmap) | Server-side template injection exploitation | 8267 | `hackerdogs/tplmap-mcp` |
| 86 | [cloudmapper-mcp](./cloudmapper-mcp/) | [duo-labs/cloudmapper](https://github.com/duo-labs/cloudmapper) | AWS network visualization and security | 8268 | `hackerdogs/cloudmapper-mcp` |
| 87 | [pacu-mcp](./pacu-mcp/) | [RhinoSecurityLabs/pacu](https://github.com/RhinoSecurityLabs/pacu) | AWS exploitation framework | 8269 | `hackerdogs/pacu-mcp` |
| 88 | [clair-mcp](./clair-mcp/) | [quay/clair](https://github.com/quay/clair) | Container vulnerability analysis | 8270 | `hackerdogs/clair-mcp` |
| 89 | [falco-mcp](./falco-mcp/) | [falcosecurity/falco](https://github.com/falcosecurity/falco) | Runtime security monitoring (containers/K8s) | 8271 | `hackerdogs/falco-mcp` |
| 90 | [checkov-mcp](./checkov-mcp/) | [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) | Infrastructure as code security scanning | 8272 | `hackerdogs/checkov-mcp` |
| 91 | [terrascan-mcp](./terrascan-mcp/) | [tenable/terrascan](https://github.com/tenable/terrascan) | Infrastructure security scanner (policy-as-code) | 8273 | `hackerdogs/terrascan-mcp` |
| 92 | [hashpump-mcp](./hashpump-mcp/) | [bwall/HashPump](https://github.com/bwall/HashPump) | Hash length extension attacks | 8274 | `hackerdogs/hashpump-mcp` |
| 93 | [x8-mcp](./x8-mcp/) | [sh1yo/x8](https://github.com/sh1yo/x8) | Hidden parameter discovery | 8275 | `hackerdogs/x8-mcp` |
| 94 | [one-gadget-mcp](./one-gadget-mcp/) | [david942j/one_gadget](https://github.com/david942j/one_gadget) | Find one-shot RCE gadgets in libc | 8276 | `hackerdogs/one-gadget-mcp` |
| 95 | [libc-database-mcp](./libc-database-mcp/) | [niklasb/libc-database](https://github.com/niklasb/libc-database) | Libc identification and offset lookup | 8277 | `hackerdogs/libc-database-mcp` |
| 96 | [pwninit-mcp](./pwninit-mcp/) | [icecream94/pwninit](https://github.com/icecream94/pwninit) | Automate binary exploitation setup | 8278 | `hackerdogs/pwninit-mcp` |
| 97 | [testssl-mcp](./testssl-mcp/) | [drwetter/testssl.sh](https://github.com/drwetter/testssl.sh) | SSL/TLS configuration testing | 8279 | `hackerdogs/testssl-mcp` |
| 98 | [sslyze-mcp](./sslyze-mcp/) | [nablac0d3/sslyze](https://github.com/nablac0d3/sslyze) | SSL/TLS configuration analyzer | 8280 | `hackerdogs/sslyze-mcp` |
| 99 | [whatweb-mcp](./whatweb-mcp/) | [urbanadventurer/WhatWeb](https://github.com/urbanadventurer/WhatWeb) | Web technology identification and fingerprinting | 8281 | `hackerdogs/whatweb-mcp` |
| 100 | [graphql-voyager-mcp](./graphql-voyager-mcp/) | [APIs-guru/graphql-voyager](https://github.com/APIs-guru/graphql-voyager) | GraphQL schema exploration | 8282 | `hackerdogs/graphql-voyager-mcp` |
| 101 | [testdisk-mcp](./testdisk-mcp/) | [cgsecurity/testdisk](https://github.com/cgsecurity/testdisk) | Disk partition recovery and file carving | 8283 | `hackerdogs/testdisk-mcp` |
| 102 | [upx-mcp](./upx-mcp/) | [upx/upx](https://github.com/upx/upx) | Executable packer/unpacker | 8284 | `hackerdogs/upx-mcp` |

### Phase 3 — Extended Security Arsenal (81 tools)

| # | Tool | Source | Description | Port | Image |
|---|------|--------|-------------|------|-------|
| 103 | [certipy-mcp](./certipy-mcp/) | [ly4k/Certipy](https://github.com/ly4k/Certipy) | AD certificate abuse and enumeration | 8285 | `hackerdogs/certipy-mcp` |
| 104 | [bloodhound-mcp](./bloodhound-mcp/) | [SpecterOps/BloodHound](https://github.com/SpecterOps/BloodHound) | AD attack path analysis and enumeration | 8286 | `hackerdogs/bloodhound-mcp` |
| 105 | [psudohash-mcp](./psudohash-mcp/) | [t3l3machus/psudohash](https://github.com/t3l3machus/psudohash) | Password list generator for targeted attacks | 8287 | `hackerdogs/psudohash-mcp` |
| 106 | [wapiti-mcp](./wapiti-mcp/) | [wapiti-scanner/wapiti](https://github.com/wapiti-scanner/wapiti) | Web app vulnerability scanner (black-box) | 8288 | `hackerdogs/wapiti-mcp` |
| 107 | [sstimap-mcp](./sstimap-mcp/) | [vladko312/SSTImap](https://github.com/vladko312/SSTImap) | SSTI detection and exploitation | 8289 | `hackerdogs/sstimap-mcp` |
| 108 | [crlfuzz-mcp](./crlfuzz-mcp/) | [dwisiswant0/crlfuzz](https://github.com/dwisiswant0/crlfuzz) | CRLF injection vulnerability scanner | 8290 | `hackerdogs/crlfuzz-mcp` |
| 109 | [smuggler-mcp](./smuggler-mcp/) | [defparam/smuggler](https://github.com/defparam/smuggler) | HTTP request smuggling detection | 8291 | `hackerdogs/smuggler-mcp` |
| 110 | [corscanner-mcp](./corscanner-mcp/) | [chenjj/CORScanner](https://github.com/chenjj/CORScanner) | CORS misconfiguration detection | 8292 | `hackerdogs/corscanner-mcp` |
| 111 | [dnsreaper-mcp](./dnsreaper-mcp/) | [punk-security/dnsReaper](https://github.com/punk-security/dnsReaper) | Subdomain takeover vulnerability scanner | 8293 | `hackerdogs/dnsreaper-mcp` |
| 112 | [ai-infra-guard-mcp](./ai-infra-guard-mcp/) | [Tencent/AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | AI infrastructure security scanning | 8294 | `hackerdogs/ai-infra-guard-mcp` |
| 113 | [ramparts-mcp](./ramparts-mcp/) | [highflame-ai/ramparts](https://github.com/highflame-ai/ramparts) | AI security guardrails and safety framework | 8295 | `hackerdogs/ramparts-mcp` |
| 114 | [mcpscan-mcp](./mcpscan-mcp/) | [antgroup/MCPScan](https://github.com/antgroup/MCPScan) | MCP server security scanning | 8296 | `hackerdogs/mcpscan-mcp` |
| 115 | [securemcp-mcp](./securemcp-mcp/) | [makalin/SecureMCP](https://github.com/makalin/SecureMCP) | MCP server security hardening and validation | 8297 | `hackerdogs/securemcp-mcp` |
| 116 | [nova-proximity-mcp](./nova-proximity-mcp/) | [Nova-Hunting/nova-proximity](https://github.com/Nova-Hunting/nova-proximity) | Network proximity analysis and threat detection | 8298 | `hackerdogs/nova-proximity-mcp` |
| 117 | [nova-framework-mcp](./nova-framework-mcp/) | [Nova-Hunting/nova-framework](https://github.com/Nova-Hunting/nova-framework) | Automated security testing orchestration | 8299 | `hackerdogs/nova-framework-mcp` |
| 118 | [openvas-mcp](./openvas-mcp/) | [greenbone/openvas-scanner](https://github.com/greenbone/openvas-scanner) | Open Vulnerability Assessment Scanner | 8300 | `hackerdogs/openvas-mcp` |
| 119 | [sublist3r-mcp](./sublist3r-mcp/) | [aboul3la/Sublist3r](https://github.com/aboul3la/Sublist3r) | Fast subdomain enumeration using OSINT | 8301 | `hackerdogs/sublist3r-mcp` |
| 120 | [exploitdb-mcp](./exploitdb-mcp/) | [offensive-security/exploitdb](https://github.com/offensive-security/exploitdb) | Exploit Database search for known vulns | 8302 | `hackerdogs/exploitdb-mcp` |
| 121 | [zmap-mcp](./zmap-mcp/) | [zmap/zmap](https://github.com/zmap/zmap) | High-speed internet-wide network scanner | 8303 | `hackerdogs/zmap-mcp` |
| 122 | [dnsenum-mcp](./dnsenum-mcp/) | [fwaeytens/dnsenum](https://github.com/fwaeytens/dnsenum) | DNS enumeration for host discovery | 8304 | `hackerdogs/dnsenum-mcp` |
| 123 | [joomscan-mcp](./joomscan-mcp/) | [OWASP/joomscan](https://github.com/OWASP/joomscan) | OWASP Joomla vulnerability scanner | 8305 | `hackerdogs/joomscan-mcp` |
| 124 | [ncrack-mcp](./ncrack-mcp/) | [nmap/ncrack](https://github.com/nmap/ncrack) | High-speed network auth cracking | 8306 | `hackerdogs/ncrack-mcp` |
| 125 | [crowbar-mcp](./crowbar-mcp/) | [galkan/crowbar](https://github.com/galkan/crowbar) | Brute-forcing for uncommon protocols | 8307 | `hackerdogs/crowbar-mcp` |
| 126 | [brutespray-mcp](./brutespray-mcp/) | [x90skysn3k/brutespray](https://github.com/x90skysn3k/brutespray) | Automated brute-forcing from scan output | 8308 | `hackerdogs/brutespray-mcp` |
| 127 | [fping-mcp](./fping-mcp/) | [schweikert/fping](https://github.com/schweikert/fping) | High-performance parallel host probing | 8309 | `hackerdogs/fping-mcp` |
| 128 | [bully-mcp](./bully-mcp/) | [aanarchyy/bully](https://github.com/aanarchyy/bully) | WPS brute-force attack tool for WiFi | 8310 | `hackerdogs/bully-mcp` |
| 129 | [pixiewps-mcp](./pixiewps-mcp/) | [wiire-a/pixiewps](https://github.com/wiire-a/pixiewps) | Offline WPS brute-force (low entropy) | 8311 | `hackerdogs/pixiewps-mcp` |
| 130 | [wifiphisher-mcp](./wifiphisher-mcp/) | [wifiphisher/wifiphisher](https://github.com/wifiphisher/wifiphisher) | Automated WiFi phishing attacks | 8312 | `hackerdogs/wifiphisher-mcp` |
| 131 | [ettercap-mcp](./ettercap-mcp/) | [Ettercap/ettercap](https://github.com/Ettercap/ettercap) | Man-in-the-middle attacks on LAN | 8313 | `hackerdogs/ettercap-mcp` |
| 132 | [ngrep-mcp](./ngrep-mcp/) | [jpr5/ngrep](https://github.com/jpr5/ngrep) | Network packet analyzer with pattern matching | 8314 | `hackerdogs/ngrep-mcp` |
| 133 | [wireshark-mcp](./wireshark-mcp/) | [wireshark/wireshark](https://github.com/wireshark/wireshark) | Network protocol analyzer (tshark) | 8315 | `hackerdogs/wireshark-mcp` |
| 134 | [slowhttptest-mcp](./slowhttptest-mcp/) | [shekyan/slowhttptest](https://github.com/shekyan/slowhttptest) | Application layer DoS attack simulator | 8316 | `hackerdogs/slowhttptest-mcp` |
| 135 | [sherlock-mcp](./sherlock-mcp/) | [sherlock-project/sherlock](https://github.com/sherlock-project/sherlock) | Username hunting across social networks | 8317 | `hackerdogs/sherlock-mcp` |
| 136 | [bettercap-mcp](./bettercap-mcp/) | [bettercap/bettercap](https://github.com/bettercap/bettercap) | Network attack and monitoring framework (MITM) | 8318 | `hackerdogs/bettercap-mcp` |
| 137 | [yersinia-mcp](./yersinia-mcp/) | [tomac/yersinia](https://github.com/tomac/yersinia) | Layer 2 network vulnerability exploitation | 8319 | `hackerdogs/yersinia-mcp` |
| 138 | [cutter-mcp](./cutter-mcp/) | [rizinorg/cutter](https://github.com/rizinorg/cutter) | Reverse engineering platform (Rizin) | 8320 | `hackerdogs/cutter-mcp` |
| 139 | [aircrack-ng-mcp](./aircrack-ng-mcp/) | [aircrack-ng/aircrack-ng](https://github.com/aircrack-ng/aircrack-ng) | WiFi security auditing (WEP/WPA/WPA2) | 8321 | `hackerdogs/aircrack-ng-mcp` |
| 140 | [netdiscover-mcp](./netdiscover-mcp/) | [netdiscover-scanner/netdiscover](https://github.com/netdiscover-scanner/netdiscover) | Active/passive ARP reconnaissance | 8322 | `hackerdogs/netdiscover-mcp` |
| 141 | [sslscan-mcp](./sslscan-mcp/) | [rbsec/sslscan](https://github.com/rbsec/sslscan) | SSL/TLS configuration and certificate scanner | 8323 | `hackerdogs/sslscan-mcp` |
| 142 | [crunch-mcp](./crunch-mcp/) | [crunchsec/crunch](https://github.com/crunchsec/crunch) | Custom wordlist generator for password cracking | 8324 | `hackerdogs/crunch-mcp` |
| 143 | [smtp-user-enum-mcp](./smtp-user-enum-mcp/) | [pentestmonkey/smtp-user-enum](https://github.com/pentestmonkey/smtp-user-enum) | SMTP username enumeration (VRFY, EXPN, RCPT) | 8325 | `hackerdogs/smtp-user-enum-mcp` |
| 144 | [lynis-mcp](./lynis-mcp/) | [CISOfy/lynis](https://github.com/CISOfy/lynis) | Security auditing and compliance testing | 8326 | `hackerdogs/lynis-mcp` |
| 145 | [netcat-mcp](./netcat-mcp/) | [diegocr/netcat](https://github.com/diegocr/netcat) | TCP/UDP networking utility | 8327 | `hackerdogs/netcat-mcp` |
| 146 | [yara-mcp](./yara-mcp/) | [VirusTotal/yara](https://github.com/VirusTotal/yara) | Pattern matching for malware classification | 8328 | `hackerdogs/yara-mcp` |
| 147 | [capa-mcp](./capa-mcp/) | [mandiant/capa](https://github.com/mandiant/capa) | Capability detection for malware triage | 8329 | `hackerdogs/capa-mcp` |
| 148 | [trivy-mcp](./trivy-mcp/) | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | Container/filesystem/IaC vulnerability scanner | 8330 | `hackerdogs/trivy-mcp` |
| 149 | [roadtools-mcp](./roadtools-mcp/) | [dirkjanm/ROADtools](https://github.com/dirkjanm/ROADtools) | Azure AD enumeration and attack tools | 8331 | `hackerdogs/roadtools-mcp` |
| 150 | [gitleaks-mcp](./gitleaks-mcp/) | [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | Secret detection for git repos and files | 8332 | `hackerdogs/gitleaks-mcp` |
| 151 | [boofuzz-mcp](./boofuzz-mcp/) | [jtpereyda/boofuzz](https://github.com/jtpereyda/boofuzz) | Network protocol fuzzing framework | 8333 | `hackerdogs/boofuzz-mcp` |
| 152 | [dharma-mcp](./dharma-mcp/) | [MozillaSecurity/dharma](https://github.com/MozillaSecurity/dharma) | Grammar-based test case generation for fuzzing | 8334 | `hackerdogs/dharma-mcp` |
| 153 | [semgrep-mcp](./semgrep-mcp/) | [semgrep/semgrep](https://github.com/semgrep/semgrep) | Static analysis for code security (5000+ rules) | 8335 | `hackerdogs/semgrep-mcp` |
| 154 | [yaraflux-mcp](./yaraflux-mcp/) | [ThreatFlux/YaraFlux](https://github.com/ThreatFlux/YaraFlux) | YARA-based malware scanning via MCP | 8336 | `hackerdogs/yaraflux-mcp` |
| 155 | [yeti-mcp](./yeti-mcp/) | [yeti-platform/yeti-mcp](https://github.com/yeti-platform/yeti-mcp) | Threat intelligence platform integration | 8337 | `hackerdogs/yeti-mcp` |
| 156 | [bloodhound-mcp-ai-mcp](./bloodhound-mcp-ai-mcp/) | [stevenyu113228/BloodHound-MCP](https://github.com/stevenyu113228/BloodHound-MCP) | AI-powered AD attack path analysis | 8338 | `hackerdogs/bloodhound-mcp-ai-mcp` |
| 157 | [vulnerability-scanner-mcp](./vulnerability-scanner-mcp/) | [RobertoDure/mcp-vulnerability-scanner](https://github.com/RobertoDure/mcp-vulnerability-scanner) | Vulnerability scanning and assessment | 8339 | `hackerdogs/vulnerability-scanner-mcp` |
| 158 | [mcpserver-audit-mcp](./mcpserver-audit-mcp/) | [ModelContextProtocol-Security/mcpserver-audit](https://github.com/ModelContextProtocol-Security/mcpserver-audit) | Security auditing for MCP servers | 8340 | `hackerdogs/mcpserver-audit-mcp` |
| 159 | [a2a-scanner-mcp](./a2a-scanner-mcp/) | [cisco-ai-defense/a2a-scanner](https://github.com/cisco-ai-defense/a2a-scanner) | Agent-to-Agent communication security scanner | 8341 | `hackerdogs/a2a-scanner-mcp` |
| 160 | [cisco-mcp-scanner-mcp](./cisco-mcp-scanner-mcp/) | [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | AI defense protocol security scanning | 8342 | `hackerdogs/cisco-mcp-scanner-mcp` |
| 161 | [aibom-mcp](./aibom-mcp/) | [cisco-ai-defense/aibom](https://github.com/cisco-ai-defense/aibom) | AI Bill of Materials generator | 8343 | `hackerdogs/aibom-mcp` |
| 162 | [knostic-mcp-scanner-mcp](./knostic-mcp-scanner-mcp/) | [knostic/MCP-Scanner](https://github.com/knostic/MCP-Scanner) | Security scanner for AI agent servers | 8344 | `hackerdogs/knostic-mcp-scanner-mcp` |
| 163 | [threat-hunting-mcp](./threat-hunting-mcp/) | [THORCollective/threat-hunting-mcp-server](https://github.com/THORCollective/threat-hunting-mcp-server) | Threat hunting and intelligence gathering | 8345 | `hackerdogs/threat-hunting-mcp` |
| 164 | [aws-s3-mcp](./aws-s3-mcp/) | [samuraikun/aws-s3-mcp](https://github.com/samuraikun/aws-s3-mcp) | AWS S3 bucket security analysis | 8346 | `hackerdogs/aws-s3-mcp` |
| 165 | [osv-mcp](./osv-mcp/) | [StacklokLabs/osv-mcp](https://github.com/StacklokLabs/osv-mcp) | Open Source Vulnerability database query | 8347 | `hackerdogs/osv-mcp` |
| 166 | [vanta-mcp](./vanta-mcp/) | [VantaInc/vanta-mcp-server](https://github.com/VantaInc/vanta-mcp-server) | Compliance and security monitoring | 8348 | `hackerdogs/vanta-mcp` |
| 167 | [xsstrike-mcp](./xsstrike-mcp/) | [s0md3v/XSStrike](https://github.com/s0md3v/XSStrike) | Advanced XSS detection and exploitation | 8349 | `hackerdogs/xsstrike-mcp` |
| 168 | [gospider-mcp](./gospider-mcp/) | [jaeles-project/gospider](https://github.com/jaeles-project/gospider) | Fast web crawling and URL discovery | 8350 | `hackerdogs/gospider-mcp` |
| 169 | [ipinfo-mcp](./ipinfo-mcp/) | [ipinfo/cli](https://github.com/ipinfo/cli) | IP address intelligence and geolocation | 8351 | `hackerdogs/ipinfo-mcp` |
| 170 | [garak-mcp](./garak-mcp/) | [EdenYavin/Garak-MCP](https://github.com/EdenYavin/Garak-MCP) | AI red teaming and LLM vulnerability testing | 8352 | `hackerdogs/garak-mcp` |
| 171 | [rasn-mcp](./rasn-mcp/) | [copyleftdev/rasn](https://github.com/copyleftdev/rasn) | Rust-based ASN lookup and network intelligence | 8353 | `hackerdogs/rasn-mcp` |
| 172 | [port-scanner-mcp](./port-scanner-mcp/) | [relaxcloud-cn/mcp-port-scanner](https://github.com/relaxcloud-cn/mcp-port-scanner) | Network port scanning tool | 8354 | `hackerdogs/port-scanner-mcp` |
| 173 | [zap-lis-mcp](./zap-lis-mcp/) | [LisBerndt/zap-mcp-server](https://github.com/LisBerndt/zap-mcp-server) | OWASP ZAP integration for web security testing | 8355 | `hackerdogs/zap-lis-mcp` |
| 174 | [trivy-neutr0n-mcp](./trivy-neutr0n-mcp/) | [Mr-Neutr0n/trivy-mcp-server](https://github.com/Mr-Neutr0n/trivy-mcp-server) | Trivy-based container vulnerability scanner | 8356 | `hackerdogs/trivy-neutr0n-mcp` |
| 175 | [grype-mcp](./grype-mcp/) | [anchore/grype](https://github.com/anchore/grype) | Container image vulnerability scanner | 8357 | `hackerdogs/grype-mcp` |
| 176 | [syft-mcp](./syft-mcp/) | [anchore/syft](https://github.com/anchore/syft) | Software bill of materials (SBOM) generator | 8358 | `hackerdogs/syft-mcp` |
| 177 | [horusec-mcp](./horusec-mcp/) | [Checkmarx/Horusec](https://github.com/Checkmarx/Horusec) | Static application security testing (SAST) | 8359 | `hackerdogs/horusec-mcp` |
| 178 | [bearer-mcp](./bearer-mcp/) | [Bearer/bearer](https://github.com/Bearer/bearer) | Code security scanning for sensitive data flows | 8360 | `hackerdogs/bearer-mcp` |
| 179 | [dependency-check-mcp](./dependency-check-mcp/) | [jeremylong/DependencyCheck](https://github.com/jeremylong/DependencyCheck) | Software composition analysis for known vulns | 8361 | `hackerdogs/dependency-check-mcp` |
| 180 | [kubescape-mcp](./kubescape-mcp/) | [kubescape/kubescape](https://github.com/kubescape/kubescape) | Kubernetes security posture management | 8362 | `hackerdogs/kubescape-mcp` |
| 181 | [ggshield-mcp](./ggshield-mcp/) | [GitGuardian/ggshield](https://github.com/GitGuardian/ggshield) | Secret detection and code security (GitGuardian) | 8363 | `hackerdogs/ggshield-mcp` |
| 182 | [retire-js-mcp](./retire-js-mcp/) | [RetireJS/retire.js](https://github.com/RetireJS/retire.js) | JavaScript library vulnerability scanner | 8364 | `hackerdogs/retire-js-mcp` |
| 183 | [suricata-mcp](./suricata-mcp/) | [Medinios/SuricataMCP](https://github.com/Medinios/SuricataMCP) | Network intrusion detection and monitoring | 8365 | `hackerdogs/suricata-mcp` |

### Port Allocation

| Phase | Range | Count |
|-------|-------|-------|
| Phase 1 | 8100–8116 | 17 |
| Phase 2 | 8200–8284 | 85 |
| Phase 3 | 8285–8365 | 81 |
| IVRE | 8366 | 1 |

### Reserved Ports (do not use)

- 80 (HTTP)
- 8000-8010 (general app servers)
- 8501-8510 (Streamlit)
- 9000-9010 (monitoring)

## Quick Start

### Run All Services

```bash
docker compose up -d
```

### Run a Single Service

```bash
docker compose up -d julius-mcp
```

### Build All Images Locally

```bash
docker compose build
```

### Use with Claude Desktop / Cursor (stdio mode)

Each tool has a `mcpServer.json` file. Example for julius-mcp:

```json
{
  "mcpServers": {
    "julius-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/julius-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport protocol: `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (when using streamable-http) | per-tool (see table) |
| `OPENAI_API_KEY` | Required for openrisk-mcp only | — |
| `HD_MAX_DOWNLOAD_MB` | Max file download size in MB (URL fetch) | `500` |
| `HD_FETCH_TIMEOUT` | Download timeout in seconds (URL fetch) | `120` |
| `HD_FETCH_ALLOW_PRIVATE` | Allow downloads from private/internal IPs | `false` |
| `HD_FETCH_AUTH_HEADER` | Auth header for private URL downloads | — |

### URL-Based File Ingestion

Tools that analyze local files (source code scanners, binary analyzers, forensics tools, etc.) support downloading files directly from URLs — no host volume mounts required. This works in both cloud and local desktop deployments.

**How it works:** 57 file-dependent tools include a shared `hd_fetch` module that handles HTTP(S) downloads, git clone, and archive extraction into the container workspace.

**Supported URL types:**
- Direct HTTP(S) file downloads
- Archives (`.zip`, `.tar.gz`, `.tar.bz2`) — auto-extracted
- GitHub/GitLab repository URLs — shallow-cloned via `git clone --depth=1`
- `data:` URIs (base64-encoded) — for small inline payloads

**Usage patterns:**

1. **`source_url` parameter** (generic-argument tools like semgrep, trivy, radare2):

```
run_semgrep(
  source_url="https://github.com/org/repo",
  arguments="scan {source} --config auto"
)
```

2. **Direct URL in path parameters** (explicit-path tools like titus):

```
scan_path(path="https://github.com/org/repo")
```

3. **`download_file` tool** (all file-dependent tools — download once, analyze multiple times):

```
download_file(url="https://example.com/firmware.bin")
# Returns: {"path": "/app/workdir/abc123/firmware.bin", "job_id": "abc123"}

run_binwalk(arguments="/app/workdir/abc123/firmware.bin")
run_checksec(arguments="--file /app/workdir/abc123/firmware.bin")

cleanup_downloads(job_id="abc123")
```

## Directory Structure

Each tool follows this structure:

```
<tool>-mcp/
├── Dockerfile              # Multi-stage Docker build
├── mcp_server.py           # FastMCP server wrapping the CLI tool
├── hd_fetch.py             # URL download utility (file-dependent tools)
├── requirements.txt        # Python dependencies
├── publish_to_hackerdogs.sh # Build & publish script
├── mcpServer.json          # MCP client configuration
├── docker-compose.yml      # Standalone compose file
├── test.sh                 # Test script
├── README.md               # Tool-specific documentation
└── progress.md             # Implementation progress tracking
```

## Publishing

Each tool has a `publish_to_hackerdogs.sh` script:

```bash
cd julius-mcp
./publish_to_hackerdogs.sh --build                    # Build locally
./publish_to_hackerdogs.sh --publish hackerdogs       # Publish to Docker Hub
./publish_to_hackerdogs.sh --build --publish hackerdogs # Build and publish
./publish_to_hackerdogs.sh --help                     # Show help
```

## Testing

Each tool has a `test.sh` script:

```bash
cd julius-mcp
./test.sh
```

## IVRE — Network Reconnaissance Platform

[ivre-mcp](./ivre-mcp/) is architecturally different from every other tool above. Instead of wrapping a CLI binary, it acts as an **HTTP client** to an existing [IVRE](https://ivre.rocks/) deployment's Web API — a full network reconnaissance platform that combines active scanning (Nmap, Masscan, ZGrab2, Nuclei), passive intelligence (Zeek, p0f), passive DNS, network flows, and IP geolocation into a single queryable database.

| | |
|---|---|
| **Directory** | [ivre-mcp](./ivre-mcp/) |
| **Source** | [ivre/ivre](https://github.com/ivre/ivre) |
| **Port** | 8366 |
| **Image** | `hackerdogs/ivre-mcp` |
| **Architecture** | Web API client (httpx) connecting to a running IVRE stack |
| **Requires** | A deployed IVRE instance (`ivre/web` + `ivre/db` + `ivre/client`) |

**Why it's different:**
- Does **not** bundle a database or IVRE itself — it queries an external IVRE Web API over HTTP
- Requires `IVRE_WEB_URL` environment variable pointing to a running IVRE web interface
- Provides **12 tools**: host queries, passive recon, passive DNS, flow analysis, IP geolocation, aggregations (top/distinct values), and specialized views (IPs-only, IPs+ports, timeline)
- Includes [DEPLOY_IVRE.md](./ivre-mcp/DEPLOY_IVRE.md) with a step-by-step guide to deploying IVRE with Docker

```
MCP Client (Cursor/Claude) ──MCP──▶ ivre-mcp ──HTTP──▶ IVRE Web (Nginx+uWSGI) ──▶ MongoDB
```

**stdio mode:**

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--network", "ivre-deployment_default",
               "-e", "IVRE_WEB_URL", "-e", "MCP_TRANSPORT",
               "hackerdogs/ivre-mcp:latest"],
      "env": {
        "IVRE_WEB_URL": "http://ivreweb:80",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**streamable-http mode:**

```bash
docker run -d --rm --network ivre-deployment_default \
  -e IVRE_WEB_URL=http://ivreweb:80 \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8366 \
  -p 8366:8366 hackerdogs/ivre-mcp:latest
```

Then connect your MCP client to `http://localhost:8366/mcp`.

## License

See [LICENSE](./LICENSE) for details.
