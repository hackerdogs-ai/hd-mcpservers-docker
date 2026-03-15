from __future__ import annotations

from typing import Any

from pydantic import BaseModel

class URLHausVTReport(BaseModel):
    result: str | None = None
    percent: str | None = None

class MalwareBazaarHashReport(BaseModel):
    """
        Schema for MalwareBazaar API report.
    """
    sha256_hash: str | None = None
    md5_hash: str | None = None
    sha1_hash: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    file_type: str | None = None
    file_type_mime: str | None = None
    reporter: str | None = None
    origin_country: str | None = None
    anonymous: int | None = None
    signature: str | None = None
    imphash: str | None = None
    tlsh: str | None = None
    telfhash: str | None = None
    gimphash: str | None = None
    ssdeep: str | None = None
    magika: str | None = None
    dhash_icon: str | None = None
    trid: object | None = None
    archive_pw: str | None = None
    tags: object | None = None
    code_sign: object | None = None
    delivery_method: str | None = None
    intelligence: object | None = None
    yara_rules: object | None = None
    comments: object | None = None
    vendor_intel: object | None = None

class URLhausHashReport(BaseModel):
    """
        Schema for URLhaus API hash report.
    """
    md5_hash: str | None = None
    sha256_hash: str | None = None
    file_type: str | None = None
    file_size: int | None = None
    signature: str | None = None
    firstseen: str | None = None
    lastseen: str | None = None
    url_count: int | None = None
    urlhaus_download: str | None = None
    virustotal: URLHausVTReport | None = None
    imphash: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    magika: str | None = None
    urls: list['URLhausURLItem'] | None = None

class URLhausURLItem(BaseModel):
    """
        Schema for individual URL item in URLhaus hash report.
    """
    url: str | None = None
    url_status: str | None = None
    firstseen: str | None = None

class ThreatFoxHashReport(BaseModel):
    data: list['ThreatFoxFileItem'] | None = None

class ThreatFoxFileItem(BaseModel):
    ioc: str | None = None
    ioc_type: str | None
    threat_type: str | None
    malware: str | None = None
    confidence_level: int | None = None
    first_seen: str | None = None
    tags: list[str] | None = None

class ThreatFoxIOCReport(BaseModel):
    data: list['ThreatFoxIOCItem'] | None = None

class ThreatFoxIOCItem(BaseModel):
    ioc: str | None = None
    ioc_type: str | None
    threat_type: str | None
    threat_type_desc: str | None = None
    malware: str | None = None
    confidence_level: int | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    tags: list[str] | None = None
    malware_samples: list['ThreatFoxIOCFileItem'] | None = None

class ThreatFoxIOCFileItem(BaseModel):
    sha256_hash: str | None = None
    md5_hash: str | None = None
    time_stamp: str | None = None

class URLHausHostReport(BaseModel):
    """
        Schema for URLHaus API host report.
    """
    host: str | None = None
    firstseen: str | None = None
    url_count: str | None = None
    blacklists: object | None = None
    urls: list['URLHausHostItem'] | None = None

class URLHausHostItem(BaseModel):
    url: str | None = None
    url_status: str | None = None
    date_added: str | None = None
    threat: str | None = None
    tags: list[str] | None = None


class URLHausURLReport(BaseModel):
    """
        Schema for URLHaus API URL report.
    """
    url: str | None = None
    url_status: str | None = None
    host: str | None = None
    date_added: str | None = None
    last_online: str | None = None
    threat: str | None = None
    blacklists: object | None = None
    tags: list[str] | None = None
    payloads: list['URLHausPayloadItem'] | None = None

class URLHausPayloadItem(BaseModel):
    """
        Schema for individual payload item in URLhaus URL report.
    """
    firstseen: str | None = None
    filename: str | None = None
    file_type: str | None = None
    response_size: str | None = None
    response_md5: str | None = None
    response_sha256: str | None = None
    signature: str | None = None
    virustotal: URLHausVTReport | None = None
    imphash: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    magika: str | None = None


class FileReport(BaseModel):
    sha256_hash: str | None = None
    md5_hash: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    file_type_mime: str | None = None
    signature: str | None = None
    imphash: str | None = None
    tlsh: str | None = None
    telfhash: str | None = None
    gimphash: str | None = None
    ssdeep: str | None = None
    magika: str | None = None
    dhash_icon: str | None = None
    trid: object | None = None
    archive_pw: str | None = None
    code_sign: object | None = None
    delivery_method: str | None = None
    virustotal: URLHausVTReport | None = None

    malwarebazaar_yara_rules: object | None = None
    malwarebazaar_vendor_intel: object | None = None
    malwarebazaar_comments: object | None = None

    urlhaus_url_count: int | None = None
    urlhaus_download: str | None = None
    urlhaus_related_urls: list[URLhausURLItem] | None = None

    threatfox_related_iocs: list[ThreatFoxFileItem] | None = None

class UrlReport(BaseModel):
    url: str | None = None
    url_status: str | None = None
    host: str | None = None
    date_added: str | None = None
    last_online: str | None = None
    threat: str | None = None
    blacklists: object | None = None
    urlhaus_tags: list[str] | None = None
    related_payloads: list['URLHausPayloadItem'] | None = None

class HostReport(BaseModel):
    urlhaus_host: str | None = None
    urlhaus_firstseen: str | None = None
    urlhaus_url_count: str | None = None
    urlhaus_blacklists: object | None = None
    urlhaus_related_urls: list['URLHausHostItem'] | None = None
    
    threatfox_related_iocs: list['ThreatFoxIOCItem'] | None = None

class DomainReport(HostReport):
    pass

class IpReport(HostReport):
    pass

