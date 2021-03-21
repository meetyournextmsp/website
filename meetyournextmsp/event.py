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
        return start.strftime('%I:%M%p %d %b %Y')

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
