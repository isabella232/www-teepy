#!/usr/bin/env python3

import socket
from email.utils import parsedate_to_datetime
from locale import LC_ALL, setlocale
from urllib.request import urlopen
from xml.etree import ElementTree

import jinja2
import mandrill
from flask import (Flask, Response, abort, redirect, render_template, request,
                   url_for)

app = Flask(__name__)
app.config.from_envvar('BACKOFFICE_CONFIG', silent=True)

setlocale(LC_ALL, 'fr_FR')

MANDRILL_KEY = app.config.get('MANDRILL_KEY')


def get_news():
    news = []
    try:
        feed = urlopen(
            'https://kozeagroup.wordpress.com/category/backoffice/feed/',
            timeout=3)
    except socket.timeout:
        return news
    tree = ElementTree.parse(feed)
    for item in tree.find('channel').findall('item'):
        date = parsedate_to_datetime(item.find('pubDate').text)
        entry = {
            'title': item.find('title').text,
            'description': item.find('description').text,
            'link': item.find('link').text,
            'isodate': date.strftime('%Y-%m-%d'),
            'date': date.strftime('%d %B %Y')}
        image = item.find(
            'media:thumbnail',
            namespaces={'media': 'http://search.yahoo.com/mrss/'})
        if image is not None:
            entry['image'] = image.attrib['url']
        news.append(entry)
    return news


@app.route('/')
@app.route('/<page>')
def page(page='index'):
    extra = {'news': get_news()[:2]} if page == 'index' else {}
    try:
        return render_template('{}.html'.format(page), page=page, **extra)
    except jinja2.exceptions.TemplateNotFound:
        abort(404)


@app.route('/robots.txt')
def robots():
    return Response('User-agent: *\nDisallow: \n', mimetype='text/plain')


@app.route('/contact/<name>', methods=['POST'])
def contact(name=None):
    form = request.form

    # Catch bots with a hidden field
    if request.form.get('city'):
        return redirect(url_for('page', page='contact_confirmation'))

    message = {
        'to': [{'email': 'backoffice@lagestiondutierspayant.fr'}],
        'subject': 'Prise de contact sur le site de BackOffice',
        'from_email': 'contact@kozea.fr'}
    if name == 'contact':
        message['html'] = '<br>'.join([
            'Objet : %s' % form.get('object', ''),
            'Nom : %s' % form.get('name', ''),
            'Email : %s' % form.get('email', ''),
            'Société : %s' % form.get('company', ''),
            'Téléphone : %s' % form.get('phone', ''),
            'Code promotionnel : %s' % form.get('promotion', ''),
            'Demande : %s ' % form.get('message', '')])
    elif name == 'phone':
        message['html'] = '<br>'.join([
            'Demande de rappel au téléphone.',
            'Téléphone : %s' % form.get('phone')])
    elif name == 'whitepaper':
        message['html'] = 'Téléchargement du livre blanc Backoffice<br><br>'
        message['html'] += '<br>'.join([
            'Nom : %s' % form.get('name', ''),
            'Email : %s' % form.get('email', ''),
            'Société : %s' % form.get('company', ''),
            'Téléphone : %s' % form.get('phone', '')])
    elif name == 'newsletter':
        message['html'] = 'Inscription à la newsletter<br><br>'
        message['html'] += '<br>'.join([
            'Email : %s' % form.get('email', ''),
            'Contact par e-mail : %s' % (
                'Oui' if form.get('contact-email', '') else 'Non'),
            'contact par courrier direct : %s' % (
                'Oui' if form.get('contact-direct-mail', '') else 'Non')])
    else:
        abort(404)

    if app.debug:
        print(message)
    else:
        mandrill.Mandrill(MANDRILL_KEY).messages.send(message=message)

    if name == 'whitepaper':
        return redirect(
            url_for('static', filename='pdf/livre_blanc_backoffice.pdf'))
    else:
        return redirect(url_for('page', page='contact_confirmation'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    from sassutils.wsgi import SassMiddleware
    app.wsgi_app = SassMiddleware(app.wsgi_app, {
        'teepy': ('sass', 'static/css', '/static/css')})
    app.run(debug=True)
