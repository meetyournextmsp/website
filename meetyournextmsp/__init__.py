import os
import sqlite3


from flask import Flask, render_template, abort

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'meetyournextmsp.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route("/")
    def index():
        return render_template('index.html')

    @app.route("/contribute")
    def contribute():
        return render_template('contribute.html')

    @app.route("/event/<id>")
    def event(id):
        database = sqlite3.connect(app.config['DATABASE'])
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute('SELECT * FROM event WHERE id=?', [id])
        event = cur.fetchone()
        if not event:
            abort(404)
        return render_template('event.html', event=event)

    return app