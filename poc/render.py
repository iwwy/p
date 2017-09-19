from functools import wraps
import json
from mimetypes import guess_type
import os.path

from pyratemp import Template
import settings


def template(name):
    def handler(func):
        @wraps(func)
        def wrapper(request, **kwargs):
            data = func(request, **kwargs)
            data["request"] = request
            content = Template(filename=settings.PYRATEMP_PATH + name)(**data)
            return dict(content=content)
        return wrapper
    return handler


class static_asset(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, request):
        request.set_static()
        path = os.path.join(settings.STATIC_PATH, self.path)
        try:
            content_type = guess_type(path)
            if isinstance(content_type, tuple):
                content_type = content_type[0]
            content = open(path, "rb").read()
        except IOError:
            return
        return dict(content=content, content_type=content_type)


class static_directory(object):

    def __init__(self, path):
        self.path = os.path.abspath(path)

    def __call__(self, request):
        request.set_static()
        target = request.path[len(request.pattern_url)+1:]
        path = os.path.join(self.path, *target.split("/"))
        # TODO: sanitize path (so it's under self.path)
        if os.path.isdir(path):
            def a(p):
                return f"""<a href="{request.path}/{p}">{p}</a>"""
            files = os.listdir(path)
            content_type = "text/html"
            content = """<!DOCTYPE html><html><head><meta charset="utf-8">
                         <title>Directory</title></head><body><ul><li>
                         """ + "</li><li>".join(map(a, files)) + """
                         </li></ul></body></html>"""
        elif os.path.isfile(path):
            try:
                content_type = guess_type(path)
                if isinstance(content_type, tuple):
                    content_type = content_type[0]
                content = open(path, "rb").read()
            except IOError:
                return
        return dict(content=content, content_type=content_type)


def responsejson(func):
    @wraps(func)
    def wrapper(request, **kwargs):
        data = func(request, **kwargs)
        content = json.dumps(data)
        return dict(content=content, content_type="application/json")
    return wrapper
