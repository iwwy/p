from core import url_patterns, template

from . import views


routes = url_patterns(
    "portal",
    ("/", template("portal/main.html")),
    ("/feed", views.feed),
)
