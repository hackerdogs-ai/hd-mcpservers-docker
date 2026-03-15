"""
Backwards-compat shim.

We originally introduced this module as a BaiduSpider-based implementation.
BaiduSpider proved unreliable in practice, so we switched to a theHarvester-style
implementation in `baidusearch_langchain.py`.

Keep this file so older imports keep working:
  from shared.modules.tools.osint.baiduspider_langchain import baidu_search_web
"""

from __future__ import annotations

from shared.modules.tools.osint.baidusearch_langchain import baidu_search_web


