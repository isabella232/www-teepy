#!/usr/bin/env python3

import jinja2
import mandrill
from flask import (Flask, Response, abort, redirect, render_template, request,
                   url_for)

app = Flask(__name__)
app.config.from_envvar('BACKOFFICE_CONFIG', silent=True)

MANDRILL_KEY = app.config.get('MANDRILL_KEY')


@app.route('/')
@app.route('/<page>')
def page(page='index'):
    try:
        return render_template('{}.html'.format(page), page=page)
    except jinja2.exceptions.TemplateNotFound:
        abort(404)


@app.route('/robots.txt')
def robots():
    return Response('User-agent: *\nDisallow: \n', mimetype='text/plain')


@app.route('/contact/<name>', methods=['POST'])
def contact(name=None):
    form = request.form
    message = {
        'to': [{'email': 'backoffice@lagestiondutierspayant.fr'}],
        'subject': 'Prise de contact sur le site de BackOffice',
        'from_email': 'contact@kozea.fr'}
    if name == 'contact':
        message['html'] = '<br>'.join([
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
    else:
        abort(404)

    if not app.debug:
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
