"""Persistent users and opaque sessions for the workbench."""
import hashlib
import hmac
import re
import secrets
import sqlite3
import time
import uuid
from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from .lab import LabError, now
from .utils.validators import validate_email


class Accounts:
    def __init__(self, app, lab):
        self.app, self.lab, self.db = app, lab, lab.connection
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS lab_users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, enabled INTEGER NOT NULL, version INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS lab_sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL, csrf TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS lab_login_attempts(identity TEXT PRIMARY KEY, failures INTEGER NOT NULL, started REAL NOT NULL);
        ''')
        self.db.execute('CREATE TABLE IF NOT EXISTS lab_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        self.db.execute('INSERT OR IGNORE INTO lab_meta VALUES(?,?)',('instance',str(uuid.uuid4())))
        self.instance=self.db.execute("SELECT value FROM lab_meta WHERE key='instance'").fetchone()[0]
        self.cookie_name='ht_session_'+self.instance.replace('-','')[:12]
        self.db.commit()
        self.dummy = generate_password_hash(secrets.token_urlsafe(32))

    @staticmethod
    def public(row):
        return {'id':row[0], 'username':row[1], 'email':row[2], 'role':row[4], 'enabled':bool(row[5]), 'version':row[6]}

    def setup_required(self):
        return not self.db.execute('SELECT 1 FROM lab_users LIMIT 1').fetchone()

    def list_users(self, page=1, per_page=10):
        users = [self.public(row) for row in self.db.execute('SELECT * FROM lab_users ORDER BY username')]
        return {'success':True, 'users':users, 'total':len(users)}

    def create_user(self, username, email, password, role='viewer'):
        if not isinstance(username, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{3,50}', username):
            raise LabError('Username must contain 3–50 letters, numbers, dots, underscores, or hyphens.')
        if not isinstance(email, str) or len(email) > 254 or not validate_email(email)[0]:
            raise LabError('Enter a valid email address.')
        self.valid_password(password)
        if role not in ('viewer','operator','admin'):
            raise LabError('Choose viewer, operator, or admin.')
        if self.db.execute('SELECT COUNT(*) FROM lab_users').fetchone()[0] >= 100:
            raise LabError('The workspace supports 100 accounts.', 409)
        identity = str(uuid.uuid4())
        try:
            self.db.execute('INSERT INTO lab_users VALUES(?,?,?,?,?,1,1)', (identity,username.lower(),email,generate_password_hash(password),role))
        except sqlite3.IntegrityError as error:
            raise LabError('Username already exists.',409) from error
        self.db.commit()
        self.lab.log(f'Created {role} account {username.lower()}.')
        self.lab.save()
        return {'success':True, 'userId':identity}

    @staticmethod
    def valid_password(password):
        if not isinstance(password,str) or not 12 <= len(password) <= 128:
            raise LabError('Passwords must contain 12–128 characters.')

    def authenticate_user(self, username, password):
        if not isinstance(username,str) or len(username)>50 or not isinstance(password,str) or len(password)>128:
            raise LabError('Invalid username or password.',401)
        key = hashlib.sha256(((request.remote_addr or 'unknown') + ':' + username.lower()).encode()).hexdigest()
        previous = self.db.execute('SELECT failures,started FROM lab_login_attempts WHERE identity=?',(key,)).fetchone()
        current = time.time()
        if previous and current - previous[1] < 600 and previous[0] >= 5:
            raise LabError('Too many login attempts. Try again in 10 minutes.',429)
        row = self.db.execute('SELECT * FROM lab_users WHERE username=?',(username.lower(),)).fetchone()
        valid = check_password_hash(row[3] if row else self.dummy,password)
        if not row or not valid or not row[5]:
            failures, started = (previous[0]+1,previous[1]) if previous and current-previous[1]<600 else (1,current)
            self.db.execute('INSERT OR REPLACE INTO lab_login_attempts VALUES(?,?,?)',(key,failures,started))
            self.db.commit()
            raise LabError('Invalid username or password.',401)
        self.db.execute('DELETE FROM lab_login_attempts WHERE identity=?',(key,))
        self.db.commit()
        return {'success':True, 'user':self.public(row)}

    def session(self):
        token = request.cookies.get(self.cookie_name,'')
        if len(token)>200: return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        row = self.db.execute('SELECT user_id,csrf,expires FROM lab_sessions WHERE token=?',(digest,)).fetchone()
        if not row or row[2] <= time.time(): return None
        user = self.db.execute('SELECT * FROM lab_users WHERE id=? AND enabled=1',(row[0],)).fetchone()
        return (self.public(user),row[1]) if user else None

    def require(self, role='viewer', csrf=False):
        session = self.session()
        if not session: raise LabError('Sign in to access the shared workspace.',401)
        user, expected = session
        if {'viewer':0,'operator':1,'admin':2}[user['role']] < {'viewer':0,'operator':1,'admin':2}[role]:
            raise LabError(f'This action requires the {role} role.',403)
        if csrf and not hmac.compare_digest(request.headers.get('X-CSRF-Token','').encode(),expected.encode()):
            raise LabError('Session verification failed. Refresh the page and retry.',403)
        return user

    def issue(self, user):
        old = hashlib.sha256(request.cookies.get(self.cookie_name,'').encode()).hexdigest()
        self.db.execute('DELETE FROM lab_sessions WHERE token=? OR expires<=?',(old,time.time()))
        token, csrf = secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        self.db.execute('INSERT INTO lab_sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,time.time()+28800))
        self.db.commit()
        response = jsonify(enabled=True,setupRequired=False,user=user,csrf=csrf)
        response.set_cookie(self.cookie_name,token,max_age=28800,httponly=True,samesite='Strict',secure=self.app.config['LAB_COOKIE_SECURE'],path='/api')
        return response

    def update(self, identity, data):
        row = self.db.execute('SELECT * FROM lab_users WHERE id=?',(identity,)).fetchone()
        if not row: raise LabError('Account not found.',404)
        if data.get('version') != row[6]: raise LabError('Account changed. Reload before saving.',409)
        role, enabled = data.get('role',row[4]),data.get('enabled',bool(row[5]))
        if role not in ('viewer','operator','admin') or not isinstance(enabled,bool): raise LabError('Invalid role or enabled setting.')
        if row[4]=='admin' and row[5] and (role!='admin' or not enabled) and self.db.execute("SELECT COUNT(*) FROM lab_users WHERE role='admin' AND enabled=1").fetchone()[0]<=1:
            raise LabError('Keep at least one enabled admin account.',409)
        password = data.get('password')
        if password is not None: self.valid_password(password)
        self.db.execute('UPDATE lab_users SET role=?,enabled=?,password=?,version=version+1 WHERE id=?',(role,int(enabled),generate_password_hash(password) if password else row[3],identity))
        if password or not enabled: self.db.execute('DELETE FROM lab_sessions WHERE user_id=?',(identity,))
        self.db.commit()
        self.lab.log(f'Updated account {row[1]} ({role}, {"enabled" if enabled else "disabled"}).')
        self.lab.save()


def required_role(path, method):
    if method=='GET' or path.endswith('/blueprints/preview'): return 'viewer'
    if path in ('/api/lab/runs','/api/lab/runs/cancel','/api/lab/connect-bench') or path.endswith('/run') or re.fullmatch(r'/api/lab/devices/[^/]+/(connection|command|fault|diagnostics)',path): return 'operator'
    return 'admin'


def register_auth(app,lab):
    from .services.user_management_service import UserManagementService
    accounts = Accounts(app,lab)
    app.extensions['accounts'] = accounts

    @app.route('/api/auth/session',methods=['GET'])
    def session_info():
        with lab.lock:
            session = accounts.session() if app.config['LAB_AUTH_ENABLED'] else None
            return jsonify(enabled=app.config['LAB_AUTH_ENABLED'],setupRequired=accounts.setup_required(),user=session[0] if session else None,csrf=session[1] if session else None)

    @app.post('/api/auth/setup')
    @app.post('/api/auth/login')
    def login():
        with lab.lock:
            if not app.config['LAB_AUTH_ENABLED']: raise LabError('Authentication is disabled.',409)
            data=request.get_json()
            if not isinstance(data,dict): raise LabError('Request body must be a JSON object.')
            if request.path.endswith('/setup'):
                if not accounts.setup_required(): raise LabError('An admin already exists. Sign in.',409)
                UserManagementService.create_user(data.get('username'),data.get('email'),data.get('password'),repository=accounts,role='admin')
            user=UserManagementService.authenticate_user(data.get('username'),data.get('password'),repository=accounts)['user']
            return accounts.issue(user)

    @app.post('/api/auth/logout')
    def logout():
        with lab.lock:
            accounts.require(csrf=True)
            digest=hashlib.sha256(request.cookies.get(accounts.cookie_name,'').encode()).hexdigest()
            accounts.db.execute('DELETE FROM lab_sessions WHERE token=?',(digest,));accounts.db.commit()
            response=jsonify(enabled=True,setupRequired=False,user=None,csrf=None)
            response.delete_cookie(accounts.cookie_name,path='/api',samesite='Strict',secure=app.config['LAB_COOKIE_SECURE'])
            return response

    @app.route('/api/auth/users',methods=['GET','POST'])
    @app.route('/api/auth/users/<identity>',methods=['PATCH'])
    def users(identity=None):
        with lab.lock:
            accounts.require('admin',csrf=request.method!='GET')
            if request.method!='GET':
                data=request.get_json()
                if not isinstance(data,dict): raise LabError('Request body must be a JSON object.')
                if identity: accounts.update(identity,data)
                else: UserManagementService.create_user(data.get('username'),data.get('email'),data.get('password'),repository=accounts,role=data.get('role','viewer'))
            return jsonify(**UserManagementService.list_users(repository=accounts))
