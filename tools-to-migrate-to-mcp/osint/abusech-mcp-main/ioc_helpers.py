from __future__ import annotations

from typing import Optional, Union

import constants
import schemas
import utils

async def _get_threatfox_ioc_report(
    ioc: str,
    abusech_api_key: Optional[str] = None,
) -> Union[schemas.ThreatFoxIOCReport, dict]:
    """
        Fetches the ThreatFox report for a given IOC (Indicator of Compromise).
    """
    response = await utils._make_abusech_http_request(
        url=f'{constants.THREATFOX_API_URL}/',
        req_data={
            'query': 'search_ioc',
            'search_term': ioc,
        },
        is_req_data_json=True,
        abusech_api_key=abusech_api_key,
    )

    if isinstance(response, dict) and response.get("error"):
        return {"error": response.get("error")}
    
    query_status = response.get('query_status')
    if query_status != 'ok':
        return schemas.ThreatFoxIOCReport()

    ioc_info = response.get('data')
    if not ioc_info:
        return schemas.ThreatFoxIOCReport()
    
    threatfox_report = schemas.ThreatFoxIOCReport(**response)
    # only keeping the first 20 items in the urls list to avoid large responses
    if threatfox_report.data and len(threatfox_report.data) > 20:
        threatfox_report.data = threatfox_report.data[:20]

    return threatfox_report

async def _get_urlhaus_host_report(
    ioc: str,
    abusech_api_key: Optional[str] = None,
) -> Union[schemas.URLHausHostReport, dict]:
    """
        Fetches the URLhaus report for a given host IOC.
    """
    response = await utils._make_abusech_http_request(
        url=f'{constants.URLHAUS_API_URL}/host/',
        req_data={
            'host': ioc
        },
        is_req_data_json=False,
        abusech_api_key=abusech_api_key,
    )

    if isinstance(response, dict) and response.get("error"):
        return {"error": response.get("error")}

    query_status = response.get('query_status')
    if query_status != 'ok':
        return schemas.URLHausHostReport()

    urlhaus_report = schemas.URLHausHostReport(**response)

    # only keeping the first 20 items in the urls list to avoid large responses
    if urlhaus_report.urls and len(urlhaus_report.urls) > 20:
        urlhaus_report.urls = urlhaus_report.urls[:20]

    return urlhaus_report

async def _get_urlhaus_url_report(
    url: str,
    abusech_api_key: Optional[str] = None,
) -> Union[schemas.URLHausURLReport, dict]:
    """
        Fetches the URLhaus report for a given URL.
    """
    response = await utils._make_abusech_http_request(
        url=f'{constants.URLHAUS_API_URL}/url/',
        req_data={
            'url': url
        },
        is_req_data_json=False,
        abusech_api_key=abusech_api_key,
    )

    if isinstance(response, dict) and response.get("error"):
        return {"error": response.get("error")}

    query_status = response.get('query_status')
    if query_status != 'ok':
        return schemas.URLHausURLReport()

    urlhaus_report = schemas.URLHausURLReport(**response)

    # only keeping the first 20 items in the payloads list to avoid large responses
    if urlhaus_report.payloads and len(urlhaus_report.payloads) > 20:
        urlhaus_report.payloads = urlhaus_report.payloads[:20]

    return urlhaus_report