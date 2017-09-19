from core import url_patterns, include, template
from render import static_asset, static_directory

import views


routes = url_patterns(
    "main",
    ("/", template("main/main.html")),
    ("/login", views.login),
    ("/logout", views.logout),
    ("/usertext", views.usertext),
    ("/favicon.ico", static_asset("images/favicon.ico")),
    ("/static", static_directory("static")),
    ("/portal", include("portal")),
)
