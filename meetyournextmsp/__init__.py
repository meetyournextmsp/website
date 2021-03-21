import os
import sqlite3
from .event import Event


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
        return render_template('event.html', event=Event(event))

    @app.route("/constituency/<id>")
    def constituency(id):
        database = sqlite3.connect(app.config['DATABASE'])
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute('SELECT * FROM tag WHERE extra_is_constituency=1 AND id=?', [id])
        tag = cur.fetchone()
        if not tag:
            abort(404)

        cur.execute('SELECT * FROM tag WHERE extra_is_region=1 AND id=?', [tag['extra_region']])
        region_tag = cur.fetchone()
        # TODO don't show event that have passed
        cur.execute('SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event_has_tag.tag_id=? ORDER BY event.start_epoch ASC', ['national'])
        national_events = [Event(i) for i in cur.fetchall()]

        # TODO don't show event that have passed
        # TODO need a group by so if an event is in both region and constituency it won't appear twice
        cur.execute(
            'SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event_has_tag.tag_id=? OR event_has_tag.tag_id=? ORDER BY event.start_epoch ASC',
            [tag['id'], tag['extra_region']]
        )
        events = [Event(i) for i in cur.fetchall()]

        return render_template(
            'constituency.html',
            constituency_title=tag['title'],
            national_events=national_events,
            events=events,
            region_title=region_tag['title']
        )

    return app