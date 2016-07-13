#!/usr/bin/env python
from flask import Flask, redirect, render_template, request, url_for
import mandrill


app = Flask(__name__)
app.config.from_envvar('BACKOFFICE_CONFIG', silent=True)

MANDRILL_KEY = app.config.get('MANDRILL_KEY')


@app.route('/')
@app.route('/<page>')
def page(page='index'):
    return render_template('{}.html'.format(page), page=page)


@app.route('/contact', methods=['POST'])
def contact():
    form = request.form
    message = {
        'to': [{'email': 'backoffice@lagestiondutierspayant.fr'}],
        'subject': 'Prise de contact sur le site de ',
        'from_email': 'contact@kozea.fr'}
    if 'name' in form:
        message['html'] = '<br>'.join([
            'Nom : %s' % form['name'],
            'Téléphone : %s' % form['phone'],
            'Email : %s' % form['email'],
            'Demande : %s ' % form['message']])
    else:
        message['html'] = '<br>'.join([
            'Demande de rappel au téléphone.',
            'Téléphone : %s' % form['phone']])

    if not app.debug:
        mandrill.Mandrill(MANDRILL_KEY).messages.send(message=message)

    return redirect(url_for('page', page='contact_confirmation'))


if __name__ == '__main__':
    from sassutils.wsgi import SassMiddleware
    app.wsgi_app = SassMiddleware(app.wsgi_app, {
        'teepy': ('sass', 'static/css', '/static/css')})
    app.run(debug=True)
