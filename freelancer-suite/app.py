"""Loopback-only freelancer workspace. Python standard library + SQLite."""
import argparse
from contextlib import contextmanager
import csv
import io
import json
import secrets
import sqlite3
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from intelligence import answer, extract

ROOT=Path(__file__).parent

@contextmanager
def connect(path):
    db=sqlite3.connect(path)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()

def initialize(path):
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,draft TEXT NOT NULL,sources TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS meetings(id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL,mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,meeting_id INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,title TEXT NOT NULL,owner TEXT NOT NULL,due TEXT NOT NULL,evidence TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'todo');
        ''')

def required(data,key,limit=30000):
    value=data.get(key)
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise ValueError(f'{key} must contain 1–{limit} characters')
    return value.strip()

def make_server(path,port=8765):
    initialize(path)
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,data,status=200,mime='application/json; charset=utf-8'):
            body=json.dumps(data).encode() if mime.startswith('application/json') else data.encode()
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)
        def trusted_host(self):
            return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def do_GET(self):
            if not self.trusted_host(): return self.reply({'error':'Invalid host'},403)
            route=urlparse(self.path).path
            if route in ('/','/support','/meetings','/app.js','/style.css'):
                name={'/':'index.html','/support':'index.html','/meetings':'index.html'}.get(route,route[1:])
                mime='text/html; charset=utf-8' if name.endswith('html') else ('text/javascript; charset=utf-8' if name.endswith('js') else 'text/css; charset=utf-8')
                return self.reply((ROOT/'web'/name).read_text(),mime=mime)
            with connect(path) as db:
                if route=='/api/state':
                    state={t:[dict(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY id DESC')] for t in ('documents','tickets','meetings','tasks')}
                    state['token']=token
                    return self.reply(state)
                if route=='/api/export':
                    output=io.StringIO(); writer=csv.writer(output)
                    writer.writerow(['task','owner','due','status','source'])
                    def safe(v): return "'"+v if v.lstrip().startswith(('=','+','-','@')) else v
                    for r in db.execute('SELECT title,owner,due,status,evidence FROM tasks ORDER BY id'):
                        writer.writerow([safe(str(v)) for v in r])
                    return self.reply(output.getvalue(),mime='text/csv; charset=utf-8')
            self.reply({'error':'Not found'},404)
        def do_POST(self):
            if not self.trusted_host() or self.headers.get('X-Workspace-Token')!=token:
                return self.reply({'error':'Invalid session; reload the app'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>100000: raise ValueError('Request too large or empty')
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict): raise ValueError('Expected JSON object')
                route=urlparse(self.path).path
                with connect(path) as db:
                    if route=='/api/documents':
                        db.execute('INSERT INTO documents(title,body) VALUES (?,?)',(required(data,'title',200),required(data,'body')))
                    elif route=='/api/tickets':
                        title=required(data,'title',200); body=required(data,'body')
                        result=answer(body,[dict(r) for r in db.execute('SELECT * FROM documents')])
                        db.execute('INSERT INTO tickets(title,body,draft,sources) VALUES (?,?,?,?)',(title,body,result['draft'],json.dumps(result['sources'])))
                    elif route=='/api/meetings':
                        title=required(data,'title',200); body=required(data,'body')
                        tasks,mode=extract(body,data.get('ai') is True)
                        mid=db.execute('INSERT INTO meetings(title,body,mode) VALUES (?,?,?)',(title,body,mode)).lastrowid
                        for t in tasks:
                            db.execute('INSERT INTO tasks(meeting_id,title,owner,due,evidence) VALUES (?,?,?,?,?)',(mid,t['title'],t['owner'],t['due'],t['evidence']))
                    elif route=='/api/task':
                        title=required(data,'title',2000); owner=data.get('owner',''); due=data.get('due',''); status=data.get('status')
                        if not isinstance(owner,str) or len(owner)>200 or not isinstance(due,str): raise ValueError('Invalid owner or date')
                        if due: date.fromisoformat(due)
                        if status not in ('todo','doing','done'): raise ValueError('Invalid status')
                        if db.execute('UPDATE tasks SET title=?,owner=?,due=?,status=? WHERE id=?',(title,owner,due,status,data.get('id'))).rowcount!=1: raise ValueError('Task not found')
                    elif route=='/api/ticket':
                        status=data.get('status')
                        if status not in ('open','resolved'): raise ValueError('Invalid status')
                        draft=required(data,'draft')
                        if db.execute('UPDATE tickets SET draft=?,status=? WHERE id=?',(draft,status,data.get('id'))).rowcount!=1: raise ValueError('Ticket not found')
                    elif route=='/api/delete':
                        table=data.get('table')
                        if table not in ('documents','tickets','meetings','tasks'): raise ValueError('Invalid item type')
                        db.execute(f'DELETE FROM {table} WHERE id=?',(data.get('id'),))
                    else: return self.reply({'error':'Not found'},404)
                self.reply({'ok':True})
            except (ValueError,TypeError,sqlite3.IntegrityError) as exc:
                self.reply({'error':str(exc)},400)
            except Exception:
                self.reply({'error':'Operation failed. Check input and retry.'},500)
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--db',default=str(ROOT/'workspace.db'))
    args=parser.parse_args()
    server=make_server(args.db,args.port)
    print(f'Open http://127.0.0.1:{server.server_port} — Ctrl+C to stop',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
