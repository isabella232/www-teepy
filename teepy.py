#!/usr/bin/env python3

import logging
import socket
from datetime import datetime
from email.utils import parsedate_to_datetime
from locale import LC_ALL, setlocale
from urllib.request import urlopen
from xml.etree import ElementTree

import gspread
import jinja2
import mandrill
from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

app = Flask(__name__)
app.config.from_envvar("BACKOFFICE_CONFIG", silent=True)

setlocale(LC_ALL, "fr_FR")

logging.basicConfig(
    level=logging.DEBUG if app.debug else logging.INFO,
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

MANDRILL_KEY = app.config.get("MANDRILL_KEY")
CONTACT_RECIPIENT = app.config.get("CONTACT_RECIPIENT")
CONTACT_PARTNER_RECIPIENT = app.config.get(
    "CONTACT_PARTNER_RECIPIENT", CONTACT_RECIPIENT
)
CONTACT_SERVICE_ACCOUNT = app.config.get("CONTACT_SERVICE_ACCOUNT")
CONTACT_SPREADSHEET_ID = app.config.get("CONTACT_SPREADSHEET_ID")
CONTACT_BO_WORKSHEET_ID = app.config.get("CONTACT_BO_WORKSHEET_ID")


def get_news():
    news = []
    try:
        feed = urlopen(
            "https://kozeagroup.wordpress.com/category/backoffice/feed/",
            timeout=3,
        )
    except socket.timeout:
        return news
    tree = ElementTree.parse(feed)
    for item in tree.find("channel").findall("item"):
        date = parsedate_to_datetime(item.find("pubDate").text)
        entry = {
            "title": item.find("title").text,
            "description": item.find("description").text,
            "link": item.find("link").text,
            "isodate": date.strftime("%Y-%m-%d"),
            "date": date.strftime("%d %B %Y"),
        }
        image = item.find(
            "media:thumbnail",
            namespaces={"media": "http://search.yahoo.com/mrss/"},
        )
        if image is not None:
            entry["image"] = image.attrib["url"]
        news.append(entry)
    return news


def store_contact(object, name, email, company, phone, promotion, message, **_):
    gc = gspread.service_account(CONTACT_SERVICE_ACCOUNT)

    wks = gc.open_by_key(CONTACT_SPREADSHEET_ID).get_worksheet_by_id(
        CONTACT_BO_WORKSHEET_ID
    )

    contact_date = datetime.now()

    wks.append_row(
        (
            contact_date.strftime("%d/%m/%Y"),
            contact_date.strftime("%H:%M"),
            object,
            name,
            company,
            email,
            phone,
            promotion,
            message,
        )
    )


@app.route("/", endpoint="index")
@app.route("/<page>")
def page(page="index"):
    extra = {"news": get_news()[:2]} if page == "index" else {}
    try:
        return render_template("{}.html".format(page), page=page, **extra)
    except jinja2.exceptions.TemplateNotFound:
        abort(404)


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: \n", mimetype="text/plain")


@app.route("/contact/<name>", methods=["POST"])
def contact(name=None):
    form = request.form

    # Catch bots with a hidden field
    if request.form.get("city"):
        return redirect(url_for("page", page="contact_confirmation"))

    contact_recipient = (
        CONTACT_RECIPIENT
        if form.get("object") != "Recrutement"
        else CONTACT_PARTNER_RECIPIENT
    )

    message = {
        "to": [{"email": contact_recipient}],
        "subject": "Prise de contact sur le site de BackOffice",
        "from_email": "contact@kozea.fr",
    }
    if name == "contact":
        message["html"] = "<br>".join(
            [
                "Objet : %s" % form.get("object", ""),
                "Nom : %s" % form.get("name", ""),
                "Email : %s" % form.get("email", ""),
                "Société : %s" % form.get("company", ""),
                "Téléphone : %s" % form.get("phone", ""),
                "Code promotionnel : %s" % form.get("promotion", ""),
                "Demande : %s " % form.get("message", ""),
            ]
        )
    elif name == "phone":
        message["html"] = "<br>".join(
            [
                "Demande de rappel au téléphone.",
                "Téléphone : %s" % form.get("phone"),
            ]
        )
    elif name == "whitepaper":
        message["html"] = "Téléchargement du livre blanc Backoffice<br><br>"
        message["html"] += "<br>".join(
            [
                "Nom : %s" % form.get("name", ""),
                "Email : %s" % form.get("email", ""),
                "Société : %s" % form.get("company", ""),
                "Téléphone : %s" % form.get("phone", ""),
            ]
        )
    elif name == "newsletter":
        message["html"] = "Inscription à la newsletter<br><br>"
        message["html"] += "<br>".join(
            [
                "Email : %s" % form.get("email", ""),
                "Contact par e-mail : %s"
                % ("Oui" if form.get("contact-email", "") else "Non"),
                "Contact par courrier direct : %s"
                % ("Oui" if form.get("contact-direct-mail", "") else "Non"),
            ]
        )
    else:
        abort(404)

    try:
        if app.debug:
            logger.debug(message)
        else:
            mandrill.Mandrill(MANDRILL_KEY).messages.send(message=message)
    except Exception as e:
        logger.error(f"Error while trying to send mail: {e}")

    try:
        store_contact(**form)
    except Exception as e:
        logger.error(f"Error while storing contact: {e}")

    if name == "whitepaper":
        return redirect(
            url_for("static", filename="pdf/livre_blanc_backoffice.pdf")
        )
    elif name == "newsletter":
        return redirect(url_for("page", page="newsletter_confirmation"))
    else:
        return redirect(url_for("page", page="contact_confirmation"))


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    from sassutils.wsgi import SassMiddleware

    app.wsgi_app = SassMiddleware(
        app.wsgi_app, {"teepy": ("sass", "static/css", "/static/css", False)}
    )
    app.run(debug=True)
