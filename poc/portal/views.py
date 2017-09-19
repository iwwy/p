from datetime import datetime

from core import access
from render import template

@access("user")
@template("portal/feed.html")
def feed(request):
    today = datetime.today()
    return dict(today=today.strftime("%d %b %Y"))
