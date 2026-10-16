"""Local research application. Start: python app.py; open http://127.0.0.1:8840."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit
from ingestion import review_document
from report import ROOT, load_report, export_html

MAX_REQUEST=8*1024*1024


def make_server(port=8840, report=None):
    loaded=report if report is not None else load_report()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self,*args):
            pass  # Uploaded text, filenames, URLs and user identifiers never enter HTTP logs.

        def send(self,status,body,content_type='application/json; charset=utf-8',download=None):
            if not isinstance(body,bytes):
                body=body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            if download:
                self.send_header('Content-Disposition',f'attachment; filename="{download}"')
            self.end_headers()
            self.wfile.write(body)

        def error(self,status,message):
            self.send(status,json.dumps(dict(error=message)))

        def trusted_request(self):
            actual_port=self.server.server_address[1]
            allowed={f'127.0.0.1:{actual_port}',f'localhost:{actual_port}'}
            if self.headers.get('Host') not in allowed:
                self.error(403,'Local access only')
                return False
            return True

        def do_GET(self):
            if not self.trusted_request(): return
            path=urlsplit(self.path).path
            if path in ('/api/report','/api/export.json','/report.json'):
                self.send(200,json.dumps(loaded,ensure_ascii=False,allow_nan=False),download='merger-report.json' if path.endswith('.json') else None)
            elif path in ('/api/export.html','/report.html'):
                self.send(200,export_html(loaded),'text/html; charset=utf-8','merger-report.html')
            else:
                files={'/':('index.html','text/html'),'/index.html':('index.html','text/html'),'/styles.css':('styles.css','text/css'),'/app.js':('app.js','text/javascript')}
                if path not in files:
                    self.error(404,'Not found')
                    return
                name,mime=files[path]
                try: body=(ROOT/'public'/name).read_bytes()
                except FileNotFoundError:
                    self.error(404,'Not found')
                    return
                self.send(200,body,mime+'; charset=utf-8')

        def do_POST(self):
            if not self.trusted_request(): return
            origin=self.headers.get('Origin')
            if (origin and origin not in {f'http://127.0.0.1:{self.server.server_address[1]}',f'http://localhost:{self.server.server_address[1]}'}) or self.headers.get('Sec-Fetch-Site')=='cross-site':
                self.error(403,'Cross-site requests are not permitted')
                return
            if self.path!='/api/review':
                self.error(404,'Not found')
                return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                self.error(415,'Expected application/json')
                return
            if self.headers.get('Transfer-Encoding'):
                self.error(400,'Transfer encoding is not supported')
                return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=MAX_REQUEST:
                    self.error(413,'Request must be between 1 byte and 8 MB')
                    return
                payload=json.loads(self.rfile.read(length))
                result=review_document(payload)
                self.send(200,json.dumps(result,ensure_ascii=False,allow_nan=False))
            except (ValueError,TypeError,UnicodeError) as exc:
                self.error(400,str(exc))
            except TimeoutError:
                self.error(408,'Upload timed out')

    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Run Merger Comparison Engine locally')
    parser.add_argument('--port',type=int,default=8840)
    parser.add_argument('--case',type=Path,help='Reviewed case JSON following data/case.json schema')
    args=parser.parse_args()
    server=make_server(args.port,load_report(args.case))
    print(f'Merger Comparison Engine: http://127.0.0.1:{server.server_address[1]}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
