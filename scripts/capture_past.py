#!/usr/bin/env python3
"""Capture the bounded 2001 PAST example corpus and preserve its source bytes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://palaeo-electronica.org/2001_1/past/pastprog/'
CORPUS = ROOT / 'benchmarks' / 'past'
VIGNETTES = CORPUS / 'vignettes'
USER_AGENT = 'Mozilla/5.0'


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs['src'])


def extract_archive() -> dict:
    archive = CORPUS / 'casefiles.ZIP'
    destination = CORPUS / 'legacy-data'
    destination.mkdir(parents=True, exist_ok=True)
    members = []
    with zipfile.ZipFile(archive) as handle:
        corrupt = handle.testzip()
        if corrupt:
            raise ValueError(f'Archive CRC failed: {corrupt}')
        for info in handle.infolist():
            name = Path(info.filename)
            if info.is_dir() or len(name.parts) != 1 or name.name != info.filename:
                raise ValueError(f'Expected a flat dataset archive; found {info.filename!r}')
            if name.suffix.lower() not in {'.dat', '.nex'} or info.file_size > 20_000_000:
                raise ValueError(f'Unexpected archive member: {info.filename!r}')
            content = handle.read(info)
            (destination / name).write_bytes(content)
            members.append({
                'filename': info.filename, 'bytes': len(content),
                'sha256': sha256(content), 'zip_crc32': f'{info.CRC:08x}',
                'path': (destination / name).relative_to(ROOT).as_posix(),
            })
    return {
        'path': archive.relative_to(ROOT).as_posix(),
        'source': 'User-supplied case-study ZIP from the 2001 website',
        'sha256': sha256(archive.read_bytes()),
        'bytes': archive.stat().st_size,
        'members': members,
    }


def decode_html(content: bytes, content_type: str) -> str:
    charset = re.search(r'charset=([\w-]+)', content_type, re.I)
    return content.decode(charset.group(1) if charset else 'windows-1252')


def fetch(url: str, category: str, prior: dict, refresh: bool, offline: bool) -> dict:
    name = urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1]
    folder = 'originals' if category == 'html' else 'assets'
    path = VIGNETTES / folder / name
    prior_record = prior.get(url)
    if not refresh and prior_record and prior_record.get('status') == 'captured' and path.exists():
        content = path.read_bytes()
        if sha256(content) != prior_record['sha256']:
            raise ValueError(f'Local source checksum mismatch: {path}')
        return dict(prior_record)
    if offline:
        return {'url': url, 'status': 'unavailable_offline', 'category': category}
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', '')
            final_url = response.url
            status_code = response.status
    except (urllib.error.URLError, TimeoutError) as exc:
        return {'url': url, 'status': 'fetch_failed', 'category': category, 'error': str(exc)}
    if category == 'html':
        text = decode_html(content, content_type)
        is_challenge = re.search(r'please wait while your request|verify you are human|just a moment|cf-chl-', text, re.I)
        case_match = re.search(r'study(\d+)\.html$', name)
        substantive = len(content) > 400 and not is_challenge
        if case_match:
            substantive = substantive and bool(re.search(r'case\s+study\s*' + case_match.group(1) + r'\b', text, re.I))
        if not substantive:
            return {'url': url, 'status': 'not_substantive_html', 'category': category,
                    'http_status': status_code, 'bytes': len(content)}
    elif not content_type.lower().startswith('image/'):
        return {'url': url, 'status': 'unexpected_content_type', 'category': category,
                'content_type': content_type}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {
        'url': url, 'final_url': final_url, 'status': 'captured', 'category': category,
        'retrieved_at_utc': utc_now(), 'http_status': status_code,
        'content_type': content_type, 'bytes': len(content), 'sha256': sha256(content),
        'path': path.relative_to(ROOT).as_posix(),
    }


def local_source_url(href: str, page_url: str) -> str | None:
    url = urllib.parse.urljoin(page_url, unescape(href))
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname not in {'palaeo-electronica.org', 'www.palaeo-electronica.org'}:
        return None
    if not parsed.path.startswith('/2001_1/past/pastprog/'):
        return None
    return BASE + parsed.path.rsplit('/', 1)[-1]


def create_offline_pages(records: list[dict], archive: dict) -> None:
    captured = {record['url']: record for record in records if record['status'] == 'captured'}
    data_names = {member['filename'] for member in archive['members']}
    output = VIGNETTES / 'html'
    output.mkdir(parents=True, exist_ok=True)
    attr_pattern = re.compile(r'''(?P<prefix>\b(?:href|src)\s*=\s*)(?P<quote>["']?)(?P<value>[^\s>"']+)(?P=quote)''', re.I)
    for url, record in captured.items():
        if record['category'] != 'html':
            continue
        content = (ROOT / record['path']).read_bytes()
        text = decode_html(content, record['content_type'])

        def rewrite(match):
            href = unescape(match.group('value'))
            if href.startswith('#') or urllib.parse.urlsplit(href).scheme in {'mailto', 'javascript', 'data'}:
                return match.group(0)
            absolute = urllib.parse.urljoin(url, href)
            source_url = local_source_url(href, url)
            fragment = urllib.parse.urlsplit(absolute).fragment
            name = urllib.parse.urlsplit(absolute).path.rsplit('/', 1)[-1]
            target = absolute
            if source_url in captured:
                other = captured[source_url]
                target = name if other['category'] == 'html' else '../assets/' + name
                if fragment:
                    target += '#' + fragment
            elif source_url and name in data_names:
                target = '../../legacy-data/' + name
            return match.group('prefix') + '"' + escape(target, quote=True) + '"'

        text = attr_pattern.sub(rewrite, text)
        text = re.sub(r'<meta\b[^>]*charset[^>]*>', '', text, flags=re.I)
        banner = ('<meta charset="utf-8"><div style="border:1px solid #888;padding:0.8em;margin:1em 0">'
                  '<strong>Archived PAST 2001 example.</strong> '
                  f'Source: <a href="{escape(url)}">{escape(url)}</a>. '
                  'This reading copy rewrites links for offline use; exact source bytes and hashes '
                  'are retained in ../originals and ../manifest.json. Historical interpretations '
                  'are preserved for comparison, not endorsed as current guidance.</div>')
        text, inserted = re.subn(r'(<body\b[^>]*>)', lambda match: match.group(1) + banner, text, count=1, flags=re.I)
        if not inserted:
            text = banner + text
        path = output / Path(record['path']).name
        path.write_text(text, encoding='utf-8')
        record['offline_path'] = path.relative_to(ROOT).as_posix()
        record['offline_sha256'] = sha256(path.read_bytes())


def write_case_inventory(records: list[dict], archive: dict) -> None:
    sources = {record['url']: record for record in records}
    members = {member['filename']: member for member in archive['members']}
    cases = []
    for case_id in range(1, 15):
        url = BASE + f'study{case_id}.html'
        record = sources[url]
        case = {'case_id': case_id, 'case_url': url, 'page_status': record['status'], 'files': []}
        if record['status'] == 'captured':
            text = decode_html((ROOT / record['path']).read_bytes(), record['content_type'])
            title = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
            case['title'] = ' '.join(unescape(re.sub(r'<[^>]+>', '', title.group(1))).split()) if title else None
            links = Links()
            links.feed(text)
            linked_names = sorted({urllib.parse.urlsplit(href).path.rsplit('/', 1)[-1]
                                   for href in links.hrefs
                                   if urllib.parse.urlsplit(href).path.rsplit('/', 1)[-1] in members})
            case['files'] = [
                {'filename': name, 'url': BASE + name, 'source_status': 'link_observed',
                 'acquired': True, 'acquisition': 'user_supplied_casefiles_zip',
                 'path': members[name]['path'], 'sha256': members[name]['sha256']}
                for name in linked_names
            ]
            case['offline_path'] = record['offline_path']
            case['source_sha256'] = record['sha256']
        tips_url = BASE + f'study{case_id}tips.html'
        if tips_url in sources:
            case['suggested_answers'] = {'url': tips_url, 'status': sources[tips_url]['status']}
        case['reference_status'] = 'published_procedures_only_no_new_past_run'
        cases.append(case)
    inventory = {
        'schema_version': 1,
        'observed_date': max((item.get('retrieved_at_utc', '')[:10] for item in records), default=''),
        'corpus': 'legacy_2001',
        'scope': 'Fourteen archived 2001 case studies; distinct from the unenumerated PAST 5 corpus.',
        'index_url': BASE + 'doc1.html', 'acquired_files': len(members),
        'past_reference_runs': 0, 'dataset_redistribution_terms': 'no_open_licence_asserted',
        'acquisition_manifest': 'benchmarks/past/vignettes/manifest.json', 'cases': cases,
    }
    (CORPUS / 'legacy-cases.json').write_text(json.dumps(inventory, indent=2) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Refetch sources instead of using verified local captures.')
    parser.add_argument('--offline', action='store_true', help='Regenerate and verify existing captures without network access.')
    args = parser.parse_args()
    if args.refresh and args.offline:
        parser.error('--refresh and --offline cannot be combined')
    manifest_path = VIGNETTES / 'manifest.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    prior = {item['url']: item for item in previous.get('sources', [])}
    archive = extract_archive()

    def capture(item):
        return fetch(item[0], item[1], prior, args.refresh, args.offline)

    initial = [(BASE + 'doc1.html', 'html')] + [(BASE + f'study{i}.html', 'html') for i in range(1, 15)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(capture, initial))
    links_by_page = {}
    for item in records:
        if item['status'] != 'captured':
            continue
        links = Links()
        links.feed(decode_html((ROOT / item['path']).read_bytes(), item['content_type']))
        links_by_page[item['url']] = links
    extras = set()
    for url, links in links_by_page.items():
        for href in links.hrefs:
            source_url = local_source_url(href, url)
            if source_url and re.search(r'/study\d+tips\.html$', source_url):
                extras.add((source_url, 'html'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        records.extend(pool.map(capture, sorted(extras)))
    for item in records:
        if item['status'] != 'captured' or item['url'] in links_by_page:
            continue
        links = Links()
        links.feed(decode_html((ROOT / item['path']).read_bytes(), item['content_type']))
        links_by_page[item['url']] = links
    assets = set()
    for url, links in links_by_page.items():
        for src in links.images:
            source_url = local_source_url(src, url)
            if source_url:
                assets.add((source_url, 'image'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        records.extend(pool.map(capture, sorted(assets)))
    create_offline_pages(records, archive)
    write_case_inventory(records, archive)
    cases = [item for item in records if re.search(r'/study\d+\.html$', item['url'])]
    manifest = {
        'schema_version': 1,
        'corpus': 'legacy_2001',
        'source_scope': 'doc1.html, fourteen study pages, directly linked suggested answers and local image dependencies',
        'software_redistribution': 'PAST executable is not included.',
        'rights': 'Third-party material retained in the private development repository at user request; no open redistribution licence asserted.',
        'archive': archive,
        'case_count': len(cases),
        'captured_case_count': sum(item['status'] == 'captured' for item in cases),
        'sources': sorted(records, key=lambda item: item['url']),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    failures = [item for item in records if item['status'] != 'captured']
    print(f"ZIP: {len(archive['members'])} members verified and extracted byte-for-byte.")
    print(f"Vignettes: {manifest['captured_case_count']}/{len(cases)} substantive HTML pages captured.")
    print(f"All sources: {len(records) - len(failures)}/{len(records)} captured.")
    for item in failures:
        print(f"UNRESOLVED {item['url']}: {item['status']}")
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
