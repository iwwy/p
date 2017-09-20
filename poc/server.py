"""Pure Python WSGI Server with Pyratemp
"""

from urllib.parse import parse_qs

import core
from render import template, static_asset
import urls
import settings


@template("404.html")
def _http404(request):
    return {"path": request.path}


class Application(object):

    def __init__(self):
        self.start_response = None

    def __call__(self, environ, start_response):

        self.start_response = start_response

        post = None
        if environ["REQUEST_METHOD"] == "POST":
            size = int(environ.get("CONTENT_LENGTH", 0))
            if size:
                data = environ["wsgi.input"].read(size)
                post = dict((k, v[0]) for k, v in
                            parse_qs(data.decode("utf-8")).items())
        query_string = environ["QUERY_STRING"] and dict((k, v[0]) for k, v in
            parse_qs(environ["QUERY_STRING"]).items()) or {}

        request = core.Request(
            # http://lucumr.pocoo.org/2010/5/25/wsgi-on-python-3/
            path=environ["PATH_INFO"].encode("latin1").decode("utf-8"),
            query_string=query_string,
            cookie=environ.get("HTTP_COOKIE"),
            method=environ["REQUEST_METHOD"],
            post=post,
            url_scheme=environ["wsgi.url_scheme"],
            host=environ["HTTP_HOST"],
        )

        save_session = False
        if request.path.startswith(settings.STATIC_URL):
            request.path = request.path[len(settings.STATIC_URL):]
            response = static_asset(request.path)(request)
        else:
            save_session = True
            try:
                response = urls.routes(request)
            except core.HttpFound as redirect:
                response = request._redirect(redirect.args[0])
        if response:
            if settings.SQLITE_DBNAME and save_session:
                request.db.save_session(request.session_id, request.session)
                if request.set_cookie:
                    response.setdefault(
                        "headers", []).append(request.set_cookie)
                    request.db.update_session(request.session_id,
                                              request.set_cookie[1][-29:])
                request.db.close()
            return self._serve(**response)
        else:
            return self._serve(status=404, **_http404(request))

    def _serve(self, content, status=200, content_type="text/html",
               headers=[]):
        status_map = {
            200: "200 OK",
            302: "302 Found",
            404: "404 Not Found",
        }
        start_response = self.start_response
        self.start_response = None
        response = (isinstance(content, str) and content.encode("utf-8") or
                    content)
        response_headers = []
        if content_type:
            if content_type in core.TEXT_TYPES:
                content_type += "; charset=utf-8"
            response_headers.append(("Content-type", content_type))
        if len(response):
            response_headers.append(("Content-length", str(len(response))))
        response_headers += headers
        start_response(status_map[status], response_headers)
        return [response]


def application(environ, start_response):
    app = Application()
    return app(environ, start_response)
