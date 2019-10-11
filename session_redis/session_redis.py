import werkzeug.contrib.sessions
from odoo import http, tools
from odoo.tools.func import lazy_property


def is_redis_session_store_activated():
    return tools.config.get('session_redis')


try:
    import cPickle
except ImportError:
    import _pickle as cPickle

try:
    import redis
except ImportError:
    if is_redis_session_store_activated():
        raise


DEFAULT_SESSION_TIMEOUT = 60 * 60 * 24 * 7  # 1 weeks in seconds


class RedisSessionStore(werkzeug.contrib.sessions.SessionStore):

    def __init__(self, *args, **kwargs):
        super(RedisSessionStore, self).__init__(*args, **kwargs)
        self.expire = kwargs.get('expire', DEFAULT_SESSION_TIMEOUT)
        if self.expire == DEFAULT_SESSION_TIMEOUT:
            self.expire = int(tools.config.get('session_redis_expire', DEFAULT_SESSION_TIMEOUT))
        self.key_prefix = kwargs.get('key_prefix', tools.config.get('session_redis_prefix', ''))
        self.redis = redis.Redis(
            host=tools.config.get('session_redis_host', 'localhost'),
            port=int(tools.config.get('session_redis_port', 6379)),
            db=int(tools.config.get('session_redis_dbindex', 1)),
            password=tools.config.get('session_redis_pass', None))
        self._is_redis_server_running()

    def _get_session_key(self, sid):
        key = self.key_prefix + sid
        return key.encode('utf-8')

    def _is_redis_server_running(self):
        self.redis.ping()

    def save(self, session):
        key = self._get_session_key(session.sid)
        data = cPickle.dumps(dict(session))
        self.redis.setex(name=key, value=data, time=self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)

    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        if data:
            self.redis.setex(name=key, value=data, time=self.expire)
            data = cPickle.loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)


if is_redis_session_store_activated():
    def session_gc(session_store):
        pass

    @lazy_property
    def session_store(self):
        return RedisSessionStore(session_class=http.OpenERPSession)

    http.session_gc = session_gc
    http.Root.session_store = session_store

