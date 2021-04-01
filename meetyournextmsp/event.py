import re
import datetime
import pytz

class Event:

    def __init__(self, data):
        self.title = data['title']
        self.description = data['description']
        self.id = data['id']
        self.cancelled = data['cancelled']
        self.deleted = data['deleted']
        self.url = data['url']
        self.data = data

    def get_start_strftime(self):
        start = datetime.datetime(
            self.data['start_year'],
            self.data['start_month'],
            self.data['start_day'],
            self.data['start_hour'],
            self.data['start_minute'],
            tzinfo=pytz.timezone('Europe/London')
        )
        return start.strftime('%a %d %b %Y %I:%M%p')

    def get_start_strftime_for_time_tag(self):
        start = datetime.datetime(
            self.data['start_year'],
            self.data['start_month'],
            self.data['start_day'],
            self.data['start_hour'],
            self.data['start_minute'],
            tzinfo=pytz.timezone('Europe/London')
        )
        # Can't use isoformat - produces a different and incorrect result on live server!
        return start.strftime('%Y-%m-%dT%H:%M+01:00')

    def get_end_strftime(self):
        end = datetime.datetime(
            self.data['end_year'],
            self.data['end_month'],
            self.data['end_day'],
            self.data['end_hour'],
            self.data['end_minute'],
            tzinfo=pytz.timezone('Europe/London')
        )
        return end.strftime('%I:%M%p')

    def get_end_strftime_for_time_tag(self):
        end = datetime.datetime(
            self.data['end_year'],
            self.data['end_month'],
            self.data['end_day'],
            self.data['end_hour'],
            self.data['end_minute'],
            tzinfo=pytz.timezone('Europe/London')
        )
        # Can't use isoformat - produces a different and incorrect result on live server!
        return end.strftime('%Y-%m-%dT%H:%M+01:00')

    def has_end(self):
        return \
            self.data['start_year'] != self.data['end_year'] or \
            self.data['start_month'] != self.data['end_month'] or \
            self.data['start_day'] != self.data['end_day'] or \
            self.data['start_hour'] != self.data['end_hour'] or \
            self.data['start_minute'] != self.data['end_minute']
