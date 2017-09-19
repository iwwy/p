import settings

import datetime
from datetime import timedelta
from functools import wraps
from http.cookies import SimpleCookie
from importlib import import_module
import logging
import re
import sys
import time
from urllib.parse import urlunparse
import uuid

from pyratemp import Template
from render import static_asset, static_directory

if settings.SQLITE_DBNAME:
    import db


TEXT_TYPES = (
    "text/plain",
    "text/html",
    "application/json",
)


class DummyDb(object):

    def save_session(self, a, b):
        pass

    def close(self):
        pass


class HttpFound(Exception):

    pass


class Route(object):

    def __init__(self, url, type_):
        self.url = url
        self.type_ = type_


class Request(object):

    def __init__(self, path, query_string, cookie, method, post,
                 url_scheme, host):

        self._routes = dict()
        self.pattern_url = ""
        self.path = path
        self.full_path = path
        self.query_string = query_string
        self.method = method
        self.post = post
        self.url_scheme = url_scheme
        self.host = host
        self.matchdict = {}

        self.reinit()
        if settings.SQLITE_DBNAME:
            self.db = db.Database(settings.SQLITE_DBNAME)
            if cookie:
                request_cookie = SimpleCookie(cookie)
                if request_cookie.get("session"):
                    session_id = request_cookie["session"].value
                    if session_id:
                        self.session_id = session_id
            if not self.session_id:
                self.session_id = uuid.uuid4().hex
                self.db.insert_session(self.session_id)
            session = self.db.get_session(self.session_id)
            self.session, self.session_expires = session
            if self.session_expires >  datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc) - timedelta(days=1):
                cookie = SimpleCookie()
                cookie["session"] = self.session_id
                cookie["session"]["expires"] = settings.SESSION_LENGTH
                self.set_cookie = tuple(cookie.output().split(": ", 1))
            self.user = self.db.get_user_by_session(self.session_id)

    def set_static(self):
        """Disable session for this request

        Set persistance methods as no-op as this is a request for a
        static resource."""
        self.set_cookie = False
        self.db = DummyDb()

    def reinit(self):
        self.session = {}
        self.session_id = ""
        self.set_cookie = None
        self.user = None

    def loginsalt(self):
        salt = uuid.uuid4().hex
        self.session.update({
            "loginsalt": salt,
            "loginexpire": int(time.time()) + 300,
        })
        return salt

    def login(self, username, hash_):
        if not settings.SQLITE_DBNAME:
            return "Login is disabled in settings"
        now = int(time.time())
        expire = self.session.pop("loginexpire", now-300)
        loginsalt = self.session.pop("loginsalt", "")
        if (datetime.datetime.fromtimestamp(now) >
                datetime.datetime.fromtimestamp(expire)):
            return "Login timeout"
        if not loginsalt:
            return "Invalid login session"
        user = self.db.get_user_by_name_salt_hash(username, loginsalt, hash_)
        if user is None:
            return "Invalid username or password"
        self.db.set_user_session(user.uid, self.session_id)

    def logout(self):
        self.db.logout_session(self.session_id)
        self.reinit()

    def redirect(self, path=None):
        if path is None:
            path = self.path
        raise HttpFound(path)

    def _redirect(self, path):
        url_tuple = (self.url_scheme, self.host, path, "", "", "",)
        headers = [("Location", urlunparse(url_tuple))]
        response = dict(content=b"", status=302, content_type=None,
                        headers=headers)
        return response

    def route_url(self, name, data=None):
        route = self._routes[name]
        if route.type_ == "str":
            return route.url
        if route.type_ == "pattern":
            return route.url + data


class HandlerFinder(object):

    def __init__(self, script, *patterns):
        self.script = script
        self.patterns = patterns
        scripts = set([script])
        self._routes = dict()
        for url, handler in patterns:
            if callable(handler):
                if isinstance(url, re._pattern_type):
                    url = ""
                    type_ = "pattern"
                else:
                    type_ = "str"
                if isinstance(handler, (template, access_template)):
                    key = ":".join([script, handler.name])
                    self._routes[key] = Route(url, type_)
                elif isinstance(handler, (static_asset, static_directory)):
                    key = ":".join([script, handler.path])
                    self._routes[key] = Route(url, type_)
                else:
                    module = handler.__module__.split(".")[-1]
                    name = ".".join([module, handler.__name__])
                    key = ":".join([script, name])
                    self._routes[key] = Route(url, type_)
            elif isinstance(handler, dict):
                module = handler["module"] + ".urls"
                if not module in sys.modules.keys():
                    sys.modules[module] = import_module(module)
                if sys.modules[module].routes.script in scripts:
                    raise Exception("Duplicate script name: {}".format(
                        sys.modules[module].routes.script))
                scripts.add(sys.modules[module].routes.script)
                routes = sys.modules[module].routes._routes.items()
                for k, v in routes:
                    self._routes[k] = Route(url + v.url, v.type_)
                    sys.modules[module].routes._routes[k] = self._routes[k]
            else:
                raise Exception(f"Invalid handler: {repr(handler)}")

    def __call__(self, request):
        path = request.path
        request._routes = self._routes
        for url, handler in self.patterns:
            if callable(handler):
                if isinstance(handler,
                              static_directory) and path.startswith(url):
                    request.pattern_url = url
                    return handler(request)
                if isinstance(url, str) and url == path:
                    request.pattern_url = url
                    return handler(request)
                if isinstance(url, re._pattern_type):
                    match = re.match(url, path)
                    if match:
                        request.matchdict = dict(match.groupdict())
                        request.pattern_url = url
                        return handler(request)
            if isinstance(handler, dict) and path.startswith(url + "/"):
                module = handler["module"] + ".urls"
                request.path = path[len(url):]
                return sys.modules[module].routes(request)


class template(object):

    def __init__(self, name, **data):
        self.name = name
        self.data = data

    def __call__(self, request):
        self.data["request"] = request
        filename = settings.PYRATEMP_PATH + self.name
        content = Template(filename=filename)(**self.data)
        return {"content": content}


class access(object):

    def __init__(self, level):
        self.level = level

    def __call__(self, func):
        @wraps(func)
        def wrapper(request):
            if request.user is None:
                error = "Please login to access the requested page."
                request.session["loginerror"] = error
                request.session["full_path"] = request.full_path
                raise HttpFound("/login")
            if self.level not in request.user.access:
                return dict(content="Access Denied", content_type="text/plain")
            return func(request)
        return wrapper


class access_template(object):

    def __init__(self, level, name, **data):
        self.level = level
        self.name = name
        self.data = data

    def __call__(self, request):
        if request.user is None:
            error = "Please login to access the requested page."
            request.session["loginerror"] = error
            request.session["full_path"] = request.full_path
            raise HttpFound("/login")
        if self.level not in request.user.access:
            return dict(content="Access Denied", content_type="text/plain")
        self.data["request"] = request
        filename = settings.PYRATEMP_PATH + self.name
        content = Template(filename=filename)(**self.data)
        return {"content": content}


url_patterns = HandlerFinder
include = lambda x: {"module": x}
