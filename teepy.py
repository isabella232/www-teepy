#!/usr/bin/env python
from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')
@app.route('/<page>')
def page(page='index'):
    return render_template('{}.html'.format(page), page=page)


if __name__ == '__main__':
    from sassutils.wsgi import SassMiddleware
    app.wsgi_app = SassMiddleware(app.wsgi_app, {
        'teepy': ('sass', 'static/css', '/static/css')})
    app.run(debug=True)
