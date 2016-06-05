#!/usr/bin/env python
from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')
@app.route('/<page>')
def page(page='index'):
    return render_template('{}.html'.format(page), page=page)


if __name__ == '__main__':
    app.run(debug=True)
