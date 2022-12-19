from flask import Blueprint, render_template

site = Blueprint("site", __name__)


@site.route("/404")
def page_not_found(error):
    return render_template("404.html"), 404


@site.route("/error")
def server_error(error):
    return render_template("error.html"), 500

@site.route("/faq")
def faq():
    return render_template("faq.html")

@site.route("/contact")
def contact():
    return render_template("contact.html")


