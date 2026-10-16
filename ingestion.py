"""Untrusted documents yield candidates, never silently approved financial data."""
import argparse
import base64
import binascii
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from engine import number

MAX_FILE = 5 * 1024 * 1024
UNITS = {'INR crore', 'INR lakh', 'percent', 'INR/share', 'shares', 'INR million'}


def safe_url(value):
    if not value:
        return ''
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Source URL must be an ordinary HTTP or HTTPS address without credentials')
    return value


def detect_events(text):
    patterns = {
        'loan_book_purchase': r'loan[ -]book (?:purchase|acquisition)|portfolio (?:purchase|transfer)',
        'demerger': r'\bdemerger\b|\bde-merger\b',
        'capital_raise': r'capital (?:raise|raising|infusion)|preferential allotment',
        'amalgamation': r'\bamalgamat\w*|\bmerger\b|\bmerge[ds]?\b',
        'acquisition': r'\bacquisition\b|acquisition of control|takeover',
    }
    candidates = []
    for sentence in re.split(r'[\n.!?]+', text):
        kinds = [kind for kind, pattern in patterns.items() if re.search(pattern, sentence, re.I)]
        if 'loan_book_purchase' in kinds:
            kinds = [k for k in kinds if k != 'acquisition']
        for kind in kinds:
            candidates.append(dict(type=kind, excerpt=sentence.strip()[:600],
                                   status='needs_review', confidence='keyword candidate',
                                   dates=re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2} [A-Za-z]+ \d{4}\b', sentence)))
    return candidates[:100]


def review_document(payload):
    if not isinstance(payload, dict):
        raise ValueError('Expected an object')
    source_url = safe_url(str(payload.get('source_url', '')))
    text = payload.get('text', '')
    if not isinstance(text, str):
        raise ValueError('Text must be a string')
    method = 'user-supplied text; not verified'
    digest = hashlib.sha256(text.encode()).hexdigest()
    pages = None
    if payload.get('file_base64'):
        try:
            raw = base64.b64decode(payload['file_base64'], validate=True)
        except (ValueError, TypeError, binascii.Error) as exc:
            raise ValueError('Invalid base64 document') from exc
        if len(raw) > MAX_FILE:
            raise ValueError('Document exceeds 5 MB')
        digest = hashlib.sha256(raw).hexdigest()
        if not raw.startswith(b'%PDF-'):
            raise ValueError('Only PDF binary uploads are supported')
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError('PDF support is optional: install pypdf or paste reviewed text') from exc
        try:
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted:
                raise ValueError('Encrypted PDF: provide a permitted text extract')
            pages = len(reader.pages)
            if pages > 100:
                raise ValueError('Review at most 100 PDF pages per upload; split the document')
            extracted = []
            total = 0
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ''
                total += len(page_text)
                if total > 500_000:
                    raise ValueError('Extracted text too large; use a smaller excerpt')
                extracted.append(f'[PDF page {i+1}]\n{page_text}')
            text = '\n'.join(extracted)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('PDF could not be extracted; use a permitted manual transcription') from exc
        method = 'pypdf text extraction; layout and numbers require review'
    if len(text.encode('utf-8')) > MAX_FILE or len(text) > 500_000:
        raise ValueError('Text exceeds review limit')
    numbers = [dict(token=m.group(), context=text[max(0,m.start()-70):m.end()+90],
                    status='unverified', offset=m.start())
               for m in list(re.finditer(r'(?<!\w)[+-]?\d[\d,]*(?:\.\d+)?\s*%?', text))[:200]]
    return dict(status='needs_review', source_url=source_url, sha256=digest,
                extraction_method=method, pages=pages, event_candidates=detect_events(text),
                numbers=numbers, text_preview=text[:16000],
                mapping={key:payload.get(key) for key in ('entity','period','unit')},
                validation=dict(eligible_for_analysis=False, unit=False, period=False,
                                subtotal=False, source_reconciliation=False),
                notes=['Nothing uploaded is saved or added to the verified case.',
                       'Confirm entity identifiers, transaction type, reporting dates, units, subtotals, original source and restatements before import.',
                       'Scanned PDFs need manual transcription or locally approved OCR. Keyword events and number tokens are not financial observations.'])


def validate_observations(observations, sources, checks):
    errors = []
    if not isinstance(observations, list) or not observations:
        return ['No observations supplied']
    source_map = {s.get('id'):s for s in sources if isinstance(s, dict)}
    for check in ('unit','period','subtotal','source_reconciliation'):
        if checks.get(check) is not True:
            errors.append('Human review has not confirmed '+check)
    seen = set()
    for index, row in enumerate(observations):
        prefix = f'Row {index+1}: '
        if not isinstance(row, dict):
            errors.append(prefix+'not an object')
            continue
        for field in ('id','entity','period','metric','value','unit','basis','sourceId','locator'):
            if field not in row or row[field] in (None, ''):
                errors.append(prefix+'missing '+field)
        if row.get('id') in seen:
            errors.append(prefix+'duplicate observation id')
        seen.add(row.get('id'))
        try:
            number(row.get('value'))
            date.fromisoformat(row.get('period', ''))
        except (ValueError, TypeError):
            errors.append(prefix+'invalid number or ISO reporting date')
        if row.get('unit') not in UNITS:
            errors.append(prefix+'unsupported unit')
        if row.get('reviewed') is not True:
            errors.append(prefix+'observation has not been reviewed')
        source = source_map.get(row.get('sourceId'))
        if not source:
            errors.append(prefix+'source missing')
        else:
            try:
                if not safe_url(source.get('url', '')) and not source.get('uploadedFileSha256'):
                    raise ValueError('missing source location')
                date.fromisoformat(source.get('publishedDate', ''))
                date.fromisoformat(source.get('retrievedAt', ''))
                if not source.get('extractionMethod'):
                    raise ValueError('missing extraction method')
            except (ValueError, TypeError):
                errors.append(prefix+'source metadata incomplete')
    return errors


def main():
    parser = argparse.ArgumentParser(description='Review local evidence. Never auto-approve extraction.')
    parser.add_argument('file', type=Path)
    parser.add_argument('--validate', action='store_true', help='Validate a reviewed observation package')
    args = parser.parse_args()
    if args.validate:
        package = json.loads(args.file.read_text(encoding='utf-8-sig'))
        errors = validate_observations(package.get('observations'), package.get('sources', []), package.get('checks', {}))
        print(json.dumps(dict(valid=not errors, errors=errors), indent=2))
        return 1 if errors else 0
    if args.file.stat().st_size > MAX_FILE:
        parser.error('File exceeds 5 MB')
    raw = args.file.read_bytes()
    payload = dict(file_base64=base64.b64encode(raw).decode(), file_name=args.file.name) if args.file.suffix.lower()=='.pdf' else dict(text=raw.decode('utf-8-sig'))
    print(json.dumps(review_document(payload), indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
