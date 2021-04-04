import os
import sqlite3
from .event import Event
import yaml
import uuid
import datetime
import time
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from contextlib import closing
from flask import Flask, render_template, abort, redirect, request


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'meetyournextmsp.sqlite'),
        DATABASE_POSTCODES=os.path.join(app.instance_path, 'postcodes.sqlite'),
        CONTRIBUTIONS_DIRECTORY='',
        SENTRY_DSN='',
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if app.config['SENTRY_DSN']:
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
        )

    @app.route("/", methods = ['POST', 'GET'] )
    def index():
        if request.method == 'POST' and request.form['postcode']:
            postcode = request.form['postcode'].replace(' ','').lower()
            with closing(sqlite3.connect(app.config['DATABASE_POSTCODES'])) as database:
                database.row_factory = sqlite3.Row
                with closing(database.cursor()) as cur:
                    # Try and find an exact match.
                    cur.execute(
                        'SELECT ScottishParliamentaryConstituency2014Name FROM lookup WHERE Postcode=?',
                        [postcode]
                    )
                    data = cur.fetchone()
                    if data:
                        return redirect('/constituency/'+data['ScottishParliamentaryConstituency2014Name'])
                    # Does a partial match work?
                    cur.execute(
                        'SELECT ScottishParliamentaryConstituency2014Name FROM lookup WHERE Postcode LIKE ? GROUP BY ScottishParliamentaryConstituency2014Name',
                        [postcode+"%"]
                    )
                    data = cur.fetchall()
                    if data and len(data) == 1:
                        return redirect('/constituency/'+data[0]['ScottishParliamentaryConstituency2014Name'])
                    # Give up
                    return render_template('index-postcode-error.html')
        else:
            return render_template('index.html')

    @app.route("/contribute", methods = ['POST', 'GET'] )
    def contribute():
        if request.method == 'POST':
            event_data = {
                'title': request.form['title'],
                'description': request.form['description'],
                'url': request.form['url'],
                'cancelled': False,
                'deleted': False,
                'tags': [],
            }
            if 'tag-national' in request.form:
                event_data['tags'].append('national')
            else:
                for k,v in request.form.items():
                    if v and k.startswith('tag-'):
                        event_data['tags'].append(k[4:])
            date = request.form['start-date']
            event_data['start'] = date + " " + request.form['start-time-hour'] + ":" + request.form['start-time-minute']
            event_data['end'] = date + " " + request.form['end-time-hour'] + ":" + request.form['end-time-minute']
            meta_data = {
                'email': request.form['email']
            }
            dir_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + str(uuid.uuid4())
            os.makedirs(os.path.join(app.config['CONTRIBUTIONS_DIRECTORY'], dir_name))
            with open(os.path.join(app.config['CONTRIBUTIONS_DIRECTORY'], dir_name, 'event.yaml'), "w") as fp:
                yaml.dump(event_data, fp)
            with open(os.path.join(app.config['CONTRIBUTIONS_DIRECTORY'], dir_name, 'meta.yml'), "w") as fp:
                yaml.dump(meta_data, fp)
            return render_template('contribute-thankyou.html')

        else:
            with closing(sqlite3.connect(app.config['DATABASE'])) as database:
                database.row_factory = sqlite3.Row
                with closing(database.cursor()) as cur:
                    cur.execute('SELECT * FROM tag WHERE  extra_is_constituency=1 ORDER by title ASC', [])
                    constituencies = cur.fetchall()
                    cur.execute('SELECT * FROM tag WHERE  extra_is_region=1 ORDER by title ASC', [])
                    regions = cur.fetchall()
                    return render_template('contribute.html', constituencies=constituencies, regions=regions )

    @app.route("/event/<id>")
    def event(id):
        with closing(sqlite3.connect(app.config['DATABASE'])) as database:
            database.row_factory = sqlite3.Row
            with closing(database.cursor()) as cur:
                cur.execute('SELECT * FROM event WHERE id=?', [id])
                event = cur.fetchone()
                if not event:
                    abort(404)
                return render_template('event.html', event=Event(event))

    @app.route("/constituencies")
    def constituencies():
        with closing(sqlite3.connect(app.config['DATABASE'])) as database:
            database.row_factory = sqlite3.Row
            with closing(database.cursor()) as cur:
                cur.execute('SELECT * FROM tag WHERE  extra_is_constituency=1 ORDER by title ASC', [])
                constituencies = cur.fetchall()
                return render_template('constituencies.html', constituencies=constituencies)

    @app.route("/constituency/<id>")
    def constituency(id):
        with closing(sqlite3.connect(app.config['DATABASE'])) as database:
            database.row_factory = sqlite3.Row
            with closing(database.cursor()) as cur:
                cur.execute('SELECT * FROM tag WHERE extra_is_constituency=1 AND id=?', [id])
                tag = cur.fetchone()
                if not tag:
                    abort(404)

                cur.execute('SELECT * FROM tag WHERE extra_is_region=1 AND id=?', [tag['extra_region']])
                region_tag = cur.fetchone()
                cur.execute(
                    'SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event.start_epoch > ? AND event.deleted = 0 AND event_has_tag.tag_id=? ORDER BY event.start_epoch ASC',
                    [time.time(), 'national']
                )
                national_events = [Event(i) for i in cur.fetchall()]

                # TODO need a group by so if an event is in both region and constituency it won't appear twice
                cur.execute(
                    'SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event.start_epoch > ? AND  event.deleted = 0 AND  (event_has_tag.tag_id=? OR event_has_tag.tag_id=?) ORDER BY event.start_epoch ASC',
                    [time.time(), tag['id'], tag['extra_region']]
                )
                events = [Event(i) for i in cur.fetchall()]

                return render_template(
                    'constituency.html',
                    constituency_title=tag['title'],
                    national_events=national_events,
                    events=events,
                    region_title=region_tag['title']
                )

    @app.route("/about")
    def about():
        return render_template('about.html')

    @app.route("/all_events")
    def all_events():
        with closing(sqlite3.connect(app.config['DATABASE'])) as database:
            database.row_factory = sqlite3.Row
            with closing(database.cursor()) as cur:
                cur.execute(
                    'SELECT event.* FROM event WHERE event.start_epoch > ? AND event.deleted = 0 ORDER BY event.start_epoch ASC',
                    [time.time()]
                )
                all_events = [Event(i) for i in cur.fetchall()]
                return render_template('all_events.html', all_events=all_events)

    return app