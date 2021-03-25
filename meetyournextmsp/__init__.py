import os
import sqlite3
from .event import Event
import yaml
import uuid
import datetime


from flask import Flask, render_template, abort, redirect, request

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'meetyournextmsp.sqlite'),
        DATABASE_POSTCODES=os.path.join(app.instance_path, 'postcodes.sqlite'),
        CONTRIBUTIONS_DIRECTORY=''
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/", methods = ['POST', 'GET'] )
    def index():
        if request.method == 'POST' and request.form['postcode']:
            postcode = request.form['postcode'].replace(' ','').lower()
            database = sqlite3.connect(app.config['DATABASE_POSTCODES'])
            database.row_factory = sqlite3.Row
            cur = database.cursor()
            cur.execute('SELECT * FROM lookup WHERE Postcode=?', [postcode])
            data = cur.fetchone()
            if data:
                return redirect('/constituency/'+data['ScottishParliamentaryConstituency2014Name'])
            else:
                return render_template('index-postcode-error.html')
        else:
            return render_template('index.html')

    @app.route("/contribute", methods = ['POST', 'GET'] )
    def contribute():
        if request.method == 'POST' and request.form['feedback'].strip() in ['2','two']:
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
            database = sqlite3.connect(app.config['DATABASE'])
            database.row_factory = sqlite3.Row
            cur = database.cursor()
            cur.execute('SELECT * FROM tag WHERE  extra_is_constituency=1 ORDER by title ASC', [])
            constituencies = cur.fetchall()
            cur.execute('SELECT * FROM tag WHERE  extra_is_region=1 ORDER by title ASC', [])
            regions = cur.fetchall()
            return render_template('contribute.html', constituencies=constituencies, regions=regions )

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

    @app.route("/constituencies")
    def constituencies():
        database = sqlite3.connect(app.config['DATABASE'])
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute('SELECT * FROM tag WHERE  extra_is_constituency=1 ORDER by title ASC', [])
        constituencies = cur.fetchall()
        return render_template('constituencies.html', constituencies=constituencies)

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
        cur.execute('SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event.deleted = 0 AND event_has_tag.tag_id=? ORDER BY event.start_epoch ASC', ['national'])
        national_events = [Event(i) for i in cur.fetchall()]

        # TODO don't show event that have passed
        # TODO need a group by so if an event is in both region and constituency it won't appear twice
        cur.execute(
            'SELECT event.* FROM event JOIN event_has_tag ON event_has_tag.event_id = event.id WHERE event.deleted = 0 AND  (event_has_tag.tag_id=? OR event_has_tag.tag_id=?) ORDER BY event.start_epoch ASC',
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