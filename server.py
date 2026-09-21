"""Harness Studio portfolio demo. Python 3.10+, no external dependencies."""
import argparse, json, math, os, re, sqlite3, uuid, webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'harness.sqlite'
COLORS = {'blue','green','yellow','brown','purple','orange'}
SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS harness(id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL, notes TEXT NOT NULL, bundles TEXT NOT NULL, updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS point(harness_id TEXT NOT NULL REFERENCES harness(id), id TEXT NOT NULL, x REAL NOT NULL, y REAL NOT NULL, PRIMARY KEY(harness_id,id));
CREATE TABLE IF NOT EXISTS segment(harness_id TEXT NOT NULL, id TEXT NOT NULL, a TEXT NOT NULL,b TEXT NOT NULL,length_cm REAL,color TEXT NOT NULL,bends TEXT NOT NULL,PRIMARY KEY(harness_id,id),FOREIGN KEY(harness_id,a) REFERENCES point(harness_id,id),FOREIGN KEY(harness_id,b) REFERENCES point(harness_id,id));
CREATE TABLE IF NOT EXISTS wire(harness_id TEXT NOT NULL,id TEXT NOT NULL,a TEXT NOT NULL,b TEXT NOT NULL,color TEXT NOT NULL,gauge REAL NOT NULL,allowance_cm REAL NOT NULL,PRIMARY KEY(harness_id,id),FOREIGN KEY(harness_id,a) REFERENCES point(harness_id,id),FOREIGN KEY(harness_id,b) REFERENCES point(harness_id,id));
CREATE TABLE IF NOT EXISTS route_step(harness_id TEXT NOT NULL,wire_id TEXT NOT NULL,position INTEGER NOT NULL,segment_id TEXT NOT NULL,PRIMARY KEY(harness_id,wire_id,position),FOREIGN KEY(harness_id,wire_id) REFERENCES wire(harness_id,id),FOREIGN KEY(harness_id,segment_id) REFERENCES segment(harness_id,id));
CREATE TABLE IF NOT EXISTS revision(harness_id TEXT NOT NULL REFERENCES harness(id),version INTEGER NOT NULL,saved TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(harness_id,version));
'''

def connect():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def validate(d):
    def fail(message): raise ValueError(message)
    def number(v, lo, hi): return type(v) in (int,float) and math.isfinite(v) and lo <= v <= hi
    if not isinstance(d,dict): fail('Ugyldigt dokument.')
    if not isinstance(d.get('name'),str) or not 1 <= len(d['name'].strip()) <= 100: fail('Navnet skal være 1–100 tegn.')
    if d.get('status') not in ('draft','reviewed'): fail('Ugyldig status.')
    if not isinstance(d.get('notes'),str) or len(d['notes'])>10000: fail('Ugyldige noter.')
    for key, limit in [('points',2000),('segments',3000),('wires',5000),('bundles',100)]:
        if not isinstance(d.get(key),list) or len(d[key])>limit: fail('Ugyldig liste: '+key)
    points={};segments={};wids=set()
    for p in d['points']:
        if not isinstance(p,dict) or not isinstance(p.get('id'),str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,19}',p['id']) or p['id'] in points: fail('Punktnavne skal være unikke bogstaver/tal.')
        if not number(p.get('x'),0,152.5) or not number(p.get('y'),0,297): fail('Punktet skal ligge på bordet.')
        points[p['id']]=p
    for s in d['segments']:
        if not isinstance(s,dict) or not isinstance(s.get('id'),str) or not re.fullmatch(r'M[1-9][0-9]{0,4}',s['id']) or s['id'] in segments: fail('Ugyldigt eller gentaget M-nummer.')
        if s.get('a') not in points or s.get('b') not in points or s['a']==s['b']: fail('Strækningen skal forbinde to forskellige punkter.')
        if s.get('length_cm') is not None and not number(s['length_cm'],0.01,100000): fail('Længden skal være positiv eller tom.')
        if s.get('color') not in COLORS: fail('Ukendt føringsfarve.')
        if not isinstance(s.get('bends'),list) or len(s['bends'])>100: fail('Ugyldige knæk.')
        for xy in s['bends']:
            if not isinstance(xy,list) or len(xy)!=2 or not number(xy[0],0,152.5) or not number(xy[1],0,297): fail('Knæk skal ligge på bordet.')
        segments[s['id']]=s
    bundled=set()
    for b in d['bundles']:
        if not isinstance(b,dict) or not isinstance(b.get('ids'),list) or len(b['ids'])<2 or not number(b.get('length_cm'),0.01,100000): fail('Ugyldigt fælles mål.')
        for key in b['ids']:
            if key not in segments or key in bundled: fail('Fælles mål skal bruge forskellige eksisterende strækninger.')
            bundled.add(key)
    for w in d['wires']:
        if not isinstance(w,dict) or not isinstance(w.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',w['id']) or w['id'] in wids: fail('Ugyldigt internt ledningsnummer.')
        wids.add(w['id'])
        if w.get('a') not in points or w.get('b') not in points or w['a']==w['b'] or not w['a'].startswith('X') or not w['b'].startswith('X'): fail('Ledningen skal forbinde to forskellige X-punkter.')
        if not isinstance(w.get('color'),str) or not 1<=len(w['color'])<=60 or not number(w.get('gauge'),0.01,500) or not number(w.get('allowance_cm'),0,10000): fail('Kontrollér ledningsfarve, kvadrat og tillæg.')
        if not isinstance(w.get('route'),list) or any(key not in segments for key in w['route']) or len(w['route'])!=len(set(w['route'])): fail('Ruten indeholder ugyldige eller gentagne strækninger.')
    if d['status']=='reviewed':
        if not d['wires']: fail('Et tomt net kan ikke markeres gennemgået.')
        if any(wire_result(d,w)['length_cm'] is None for w in d['wires']): fail('Ret ledninger med manglende rute eller mål før nettet markeres gennemgået.')

def wire_result(d,w):
    segments={s['id']:s for s in d['segments']}; cur=w['a']; keys=w['route']
    if not keys: return {'length_cm':None,'issue':'Rute mangler'}
    for key in keys:
        s=segments.get(key)
        if not s or cur not in (s['a'],s['b']): return {'length_cm':None,'issue':'Ruten hænger ikke sammen'}
        cur=s['b'] if s['a']==cur else s['a']
    if cur!=w['b']: return {'length_cm':None,'issue':'Ruten ender ved et andet X-punkt'}
    total=0; used=set()
    for b in d['bundles']:
        overlap=set(b['ids']) & set(keys)
        # Separate confirmed values take precedence after both have been entered.
        if overlap and any(segments[k]['length_cm'] is None for k in b['ids']):
            if overlap != set(b['ids']): return {'length_cm':None,'issue':'Kun en del af et fælles mål bruges'}
            total+=b['length_cm'];used.update(b['ids'])
    for key in keys:
        if key in used: continue
        val=segments[key]['length_cm']
        if val is None: return {'length_cm':None,'issue':'Mål mangler: '+key}
        total+=val
    return {'length_cm':round(total+w['allowance_cm'],3),'issue':None}

def load(c,hid):
    row=c.execute('SELECT * FROM harness WHERE id=?',(hid,)).fetchone()
    if row is None: raise KeyError('Nettet findes ikke.')
    d=dict(row);d['bundles']=json.loads(d['bundles'])
    d['points']=[{k:r[k] for k in ('id','x','y')} for r in c.execute('SELECT * FROM point WHERE harness_id=? ORDER BY rowid',(hid,))]
    d['segments']=[]
    for r in c.execute('SELECT * FROM segment WHERE harness_id=? ORDER BY rowid',(hid,)):
        s={k:r[k] for k in ('id','a','b','length_cm','color')};s['bends']=json.loads(r['bends']);d['segments'].append(s)
    d['wires']=[]
    for r in c.execute('SELECT * FROM wire WHERE harness_id=? ORDER BY rowid',(hid,)):
        w={k:r[k] for k in ('id','a','b','color','gauge','allowance_cm')}
        w['route']=[r[0] for r in c.execute('SELECT segment_id FROM route_step WHERE harness_id=? AND wire_id=? ORDER BY position',(hid,w['id']))];d['wires'].append(w)
    return d

class Conflict(Exception): pass

def save(d,hid=None,expected=None):
    validate(d);now=datetime.now(timezone.utc).isoformat()
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        if hid:
            old=c.execute('SELECT version FROM harness WHERE id=?',(hid,)).fetchone()
            if not old: raise KeyError('Nettet findes ikke.')
            if expected!=old[0]: raise Conflict('En anden fane har gemt ændringer. Eksportér dine rettelser og genindlæs nettet.')
            version=old[0]+1
            for table in ('route_step','wire','segment','point'): c.execute(f'DELETE FROM {table} WHERE harness_id=?',(hid,))
            c.execute('UPDATE harness SET name=?,status=?,version=?,notes=?,bundles=?,updated=? WHERE id=?',(d['name'].strip(),d['status'],version,d['notes'],json.dumps(d['bundles']),now,hid))
        else:
            hid=uuid.uuid4().hex;version=1
            c.execute('INSERT INTO harness VALUES(?,?,?,?,?,?,?)',(hid,d['name'].strip(),d['status'],version,d['notes'],json.dumps(d['bundles']),now))
        c.executemany('INSERT INTO point VALUES(?,?,?,?)',[(hid,p['id'],p['x'],p['y']) for p in d['points']])
        c.executemany('INSERT INTO segment VALUES(?,?,?,?,?,?,?)',[(hid,s['id'],s['a'],s['b'],s['length_cm'],s['color'],json.dumps(s['bends'])) for s in d['segments']])
        c.executemany('INSERT INTO wire VALUES(?,?,?,?,?,?,?)',[(hid,w['id'],w['a'],w['b'],w['color'],w['gauge'],w['allowance_cm']) for w in d['wires']])
        c.executemany('INSERT INTO route_step VALUES(?,?,?,?)',[(hid,w['id'],i,key) for w in d['wires'] for i,key in enumerate(w['route'])])
        result=load(c,hid)
        c.execute('INSERT INTO revision VALUES(?,?,?,?)',(hid,version,now,json.dumps(result,ensure_ascii=False)))
    return result

def init():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with connect() as c: c.executescript(SCHEMA)
    with connect() as c: empty=c.execute('SELECT COUNT(*) FROM harness').fetchone()[0]==0
    if empty: save(json.loads((ROOT/'seed.json').read_text(encoding='utf-8')))

class Handler(BaseHTTPRequestHandler):
    def reply(self,data,status=200):
        body=json.dumps(data,ensure_ascii=False,allow_nan=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        try:
            if path=='/api/harnesses':
                with connect() as c: rows=[dict(r) for r in c.execute('SELECT id,name,status,version,updated FROM harness ORDER BY updated DESC')]
                return self.reply(rows)
            m=re.fullmatch(r'/api/harnesses/([a-f0-9]+)(/history)?',path)
            if m:
                with connect() as c:
                    if m[2]: d=[dict(r) for r in c.execute('SELECT version,saved FROM revision WHERE harness_id=? ORDER BY version DESC',(m[1],))]
                    else: d=load(c,m[1])
                return self.reply(d)
            m=re.fullmatch(r'/api/harnesses/([a-f0-9]+)/history/(\d+)',path)
            if m:
                with connect() as c: r=c.execute('SELECT document FROM revision WHERE harness_id=? AND version=?',(m[1],int(m[2]))).fetchone()
                if not r: raise KeyError('Versionen findes ikke.')
                return self.reply(json.loads(r[0]))
            files={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
            if path not in files: return self.reply({'error':'Ikke fundet'},404)
            fn,mime=files[path];body=(ROOT/'static'/fn).read_bytes();self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        except KeyError as e: self.reply({'error':str(e)},404)
    def mutate(self):
        try:
            # Local application: deny cross-origin writes, including DNS rebinding.
            host=self.headers.get('Host','')
            if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'): return self.reply({'error':'Ugyldig vært'},403)
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'): return self.reply({'error':'Ugyldig oprindelse'},403)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.reply({'error':'JSON kræves'},415)
            n=int(self.headers.get('Content-Length',0))
            if not 0<n<4_000_000: return self.reply({'error':'Ugyldig størrelse'},413)
            d=json.loads(self.rfile.read(n));path=urlparse(self.path).path
            if self.command=='POST' and path=='/api/harnesses': return self.reply(save(d),201)
            m=re.fullmatch(r'/api/harnesses/([a-f0-9]+)',path)
            if self.command=='PUT' and m: return self.reply(save(d,m[1],d.get('version')))
            return self.reply({'error':'Ikke fundet'},404)
        except Conflict as e: self.reply({'error':str(e)},409)
        except KeyError as e: self.reply({'error':str(e)},404)
        except (ValueError,TypeError,AttributeError,sqlite3.IntegrityError) as e: self.reply({'error':str(e)},400)
    do_POST=mutate
    do_PUT=mutate

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');parser.add_argument('--db',type=Path);args=parser.parse_args()
    if args.db: DB=args.db.resolve()
    init();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    url=f'http://127.0.0.1:{server.server_port}';print('Lindeberg ledningsnet: '+url,flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
