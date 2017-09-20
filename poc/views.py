from core import access
from render import template, responsejson


@template("main/login.html")
def login(request):
    error = request.session.pop("loginerror", "")
    if request.method == "POST":
        error = request.login(request.post.get("username", ""),
                              request.post.get("hash", ""))
        if error is None:
            path = request.session.pop("full_path", "/")
            return request.redirect(path)
    salt = request.loginsalt()
    return dict(error=error, salt=salt)


def logout(request):
    if request.method == "POST":
        request.logout()
        return request.redirect("/")


@access("user")
@responsejson
def usertext(request):
    data = request.db.get_user_data(request.user.uid)
    if request.method == "POST":
        data["usertext"] = request.post["usertext"]
        request.db.save_user_data(request.user.uid, data)
    return {"usertext": data.get("usertext", "")}
