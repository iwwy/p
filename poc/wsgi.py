import os
import sys


path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.append(path)


def server():
    from wsgiref.simple_server import make_server
    from server import application
    httpd = make_server("0.0.0.0", 8008, application)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Exit")


if __name__ == "__main__":
    server()
