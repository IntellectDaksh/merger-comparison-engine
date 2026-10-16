import http.client
import json
import threading
import unittest
from app import make_server
from report import build_report


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        report=build_report(dict(name='HTTP test',observations=[],sources=[],comparisons=[]),dict(rows=[]))
        cls.server=make_server(0,report)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.port=cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        connection.request(method,path,body=body,headers=headers or {})
        response=connection.getresponse()
        data=response.read()
        result=(response.status,dict(response.getheaders()),data)
        connection.close()
        return result

    def test_report_json_and_html_export(self):
        code,headers,body=self.request('GET','/api/report')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['case']['title'],'HTTP test')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(self.request('GET','/api/export.html')[0],200)
        self.assertEqual(self.request('GET','/report.json')[0],200)
        self.assertEqual(self.request('GET','/report.html')[0],200)

    def test_arbitrary_files_are_never_served(self):
        for path in ['/../app.py','/data/case.json','/%2e%2e/app.py']:
            self.assertEqual(self.request('GET',path)[0],404)

    def test_cross_site_post_and_dns_rebinding_rejected(self):
        self.assertEqual(self.request('POST','/api/review','{}',{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('GET','/api/report',headers={'Host':'evil.example'})[0],403)

    def test_document_review_and_validation_error(self):
        headers={'Content-Type':'application/json'}
        result=self.request('POST','/api/review',json.dumps(dict(text='amalgamation effective 2020-04-01')),headers)
        self.assertEqual(result[0],200)
        self.assertEqual(json.loads(result[2])['status'],'needs_review')
        self.assertEqual(self.request('POST','/api/review','not json',headers)[0],400)
        self.assertEqual(self.request('POST','/api/review','[]',headers)[0],400)


if __name__=='__main__': unittest.main()
