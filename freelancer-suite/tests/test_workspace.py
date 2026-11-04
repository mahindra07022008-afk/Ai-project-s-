import json, os, sqlite3, tempfile, threading, unittest, urllib.request, urllib.error
from unittest.mock import patch
from app import make_server
from intelligence import answer, extract

class IntelligenceTests(unittest.TestCase):
    def test_retrieval(self):
        docs=[dict(id=1,title='Refunds',body='Refund unused packages within 14 days.')]
        r=answer('refund packages',docs)
        self.assertEqual(r['draft'],docs[0]['body']);self.assertEqual(r['sources'][0]['document_id'],1)
        self.assertEqual(answer('astronomy',docs)['sources'],[])
        self.assertEqual(answer('refund',[])['sources'],[])
    def test_actions(self):
        tasks,mode=extract('Decision: Ship later.\nAction: Maya: Send proposal by 2026-12-15.\nArjun will test navigation.\nNote: Discuss later.')
        self.assertEqual(len(tasks),2);self.assertEqual(tasks[0]['owner'],'Maya');self.assertEqual(tasks[0]['due'],'2026-12-15');self.assertEqual(tasks[1]['owner'],'Arjun');self.assertIn('Offline',mode)
        self.assertEqual(extract('We discussed the launch.')[0],[])
    def test_missing_model(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ValueError): extract('notes',True)
    def ai(self,tasks,text):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return json.dumps({'response':json.dumps({'tasks':tasks})}).encode()
        with patch.dict(os.environ,{'OLLAMA_MODEL':'test'}),patch('urllib.request.urlopen',return_value=Response()): return extract(text,True)
    def test_ai_evidence(self):
        text='Maya will send proposal by 2026-12-15.'
        tasks,_=self.ai([dict(title='Send proposal',owner='Maya',due='2026-12-15',evidence=text)],text)
        self.assertEqual(tasks[0]['owner'],'Maya')
    def test_ai_invalid_evidence(self):
        with self.assertRaises(ValueError): self.ai([dict(title='Send',owner='Maya',due='',evidence='invented')],'meeting')
    def test_ai_unproven_fields(self):
        tasks,_=self.ai([dict(title='Send proposal',owner='Invented',due='2026-12-15',evidence='Send proposal.')],'Send proposal.')
        self.assertEqual(tasks[0]['owner'],'');self.assertEqual(tasks[0]['due'],'')

class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/test.db';self.server=make_server(self.path,0)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port);self.token=self.get('/api/state')['token']
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.worker.join();self.tmp.cleanup()
    def get(self,path):
        with urllib.request.urlopen(self.base+path) as r: return json.load(r)
    def post(self,path,data,token=True):
        headers={'Content-Type':'application/json'}
        if token: headers['X-Workspace-Token']=self.token
        req=urllib.request.Request(self.base+'/api/'+path,data=json.dumps(data).encode(),headers=headers)
        with urllib.request.urlopen(req) as r: return json.load(r)
    def test_support_flow_persistence(self):
        self.post('documents',dict(title='Refund policy',body='Refund unused packages within 14 days.'))
        self.post('tickets',dict(title='Client A',body='refund unused package'))
        ticket=self.get('/api/state')['tickets'][0];self.assertIn('14 days',ticket['draft']);self.assertEqual(len(json.loads(ticket['sources'])),1)
        self.post('ticket',dict(id=ticket['id'],draft='Reviewed reply',status='resolved'))
        self.assertEqual(self.get('/api/state')['tickets'][0]['status'],'resolved')
        with sqlite3.connect(self.path) as db: self.assertEqual(db.execute('SELECT draft FROM tickets').fetchone()[0],'Reviewed reply')
    def test_meeting_edit_export_cascade(self):
        self.post('meetings',dict(title='Launch',body='Action: Maya: Send mockup by 2026-12-15.',ai=False))
        state=self.get('/api/state');task=state['tasks'][0]
        self.post('task',dict(id=task['id'],title='=HYPERLINK("bad")',owner='Maya',due='2026-12-16',status='done'))
        with urllib.request.urlopen(self.base+'/api/export') as r:
            content=r.read().decode();self.assertIn("'=HYPERLINK",content);self.assertIn('done',content)
        self.post('delete',dict(table='meetings',id=state['meetings'][0]['id']));self.assertEqual(self.get('/api/state')['tasks'],[])
    def test_csrf_validation(self):
        for route,data,token,status in [('documents',dict(title='a',body='b'),False,403),('documents',dict(title='',body='x'),True,400),('delete',dict(table='sqlite_master',id=1),True,400),('task',dict(id=9,title='a',due='bad',status='todo'),True,400)]:
            with self.assertRaises(urllib.error.HTTPError) as e: self.post(route,data,token)
            self.assertEqual(e.exception.code,status)
    def test_host_traversal(self):
        with self.assertRaises(urllib.error.HTTPError) as e: urllib.request.urlopen(urllib.request.Request(self.base+'/api/state',headers={'Host':'evil.example'}))
        self.assertEqual(e.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as e: urllib.request.urlopen(self.base+'/../app.py')
        self.assertEqual(e.exception.code,404)
    def test_pages(self):
        for path in ['/support','/meetings','/app.js','/style.css']:
            with urllib.request.urlopen(self.base+path) as r:
                self.assertEqual(r.status,200);self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy']);self.assertTrue(r.read())
    def test_ai_error_atomic(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(urllib.error.HTTPError): self.post('meetings',dict(title='a',body='Maya will send',ai=True))
        self.assertEqual(self.get('/api/state')['meetings'],[])

if __name__=='__main__': unittest.main()
