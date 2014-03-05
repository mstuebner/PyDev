# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line skeleton application for Calendar API.
Usage:
  $ python sample.py

You can also get help on all the command-line flags the program understands
by running:

  $ python sample.py --help

"""

import argparse
import os
import sys
from collections import namedtuple
from datetime import datetime

from google_calendar import httplib2
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools


g_event = namedtuple(
    'g_event',
    [
        'creator',
        'organizer',
        'created',
        'start',
        'end',
        'summary',
        'description',
        'location',
    ]
)

g_calendar = namedtuple(
    'g_calendar',
    [
        'id',
        'name',
        'summary',
        'description',
        'location',
    ]
)

service = None

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

class GoogleCalenderConnector(object):

    # CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret. You can see the Client ID
    # and Client secret on the APIs page in the Cloud Console:
    # <https://cloud.google.com/console#/project/1003076437992/apiui>
    CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

    # Set up a Flow object to be used for authentication.
    # Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
    # NEED. For more information on using scopes please see
    # <https://developers.google.com/+/best-practices>.
    FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
                                          scope=[
                                              'https://www.googleapis.com/auth/calendar',
                                              'https://www.googleapis.com/auth/calendar.readonly',
                                          ],
                                          message=tools.message_if_missing(CLIENT_SECRETS))

    flags = None
    service = None

    def __init__(self, flags):
        self.flags = flags
        self.service = self.initialize()

    def initialize(self):
        # If the credentials don't exist or are invalid run through the native client
        # flow. The Storage object will ensure that if successful the good
        # credentials will get written back to the file.
        storage = file.Storage('sample.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(self.FLOW, storage, self.flags)

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        http = credentials.authorize(httplib2.Http())

        # Construct the service object for the interacting with the Calendar API.
        return discovery.build('calendar', 'v3', http=http)


    def get_calendar_name_id(self):
        page_token = None
        calendar_list = []

        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendar_list.append(calendar_list_entry['summary'],
                                     calendar_list_entry['id'])

            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        return calendar_list


    def make_g_event(self, raw_event):
        """
        Method converts the raw event data into a namedtuple

        :param raw_event: raw event data
        :return: namedtuple with event data
        """
        _fs = '%Y-%m-%dT%H:%M:%S+01:00'

        try:
            start = datetime.strptime(raw_event.get('start', None)[u'dateTime'], _fs)
            end = datetime.strptime(raw_event.get('end', None)[u'dateTime'], _fs)

            event = g_event(raw_event.get('creator', None),
                            raw_event.get('organizer', None),
                            raw_event.get('created', None),
                            start,
                            end,
                            raw_event.get('summary', None),
                            raw_event.get('description', None),
                            raw_event.get('location', None)
            )

            return event

        except Exception, ex:
            print(ex)
            return None

    def get_events(self, service):

        """
        Method queries events from calendar, converts them to namedtuples and returns a list of events

        :param service:
        :return: list of namedtuples
        """
        try:
            #print "Success! Now add code here."
            calendar_id = '8fmqekkir19l3fdqpmagogsah4@group.calendar.google.com'
            page_token = None
            event_list = []

            # Source: https://developers.google.com/google-apps/calendar/v3/reference/calendarList/list?hl=de
            # Info: https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/
            while True:
                events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()

                for event in events['items']:
                    event_list.append(self.make_g_event(event))

                page_token = events.get('nextPageToken')
                if not page_token:
                    break

        except client.AccessTokenRefreshError:
            print ("The credentials have been revoked or expired, please re-run the application to re-authorize")

        return event_list

    def output(self, event_list):
        _fs = '%d.%m.%Y %H:%M'
        for g_event in event_list:
            if g_event.description:
                cmd = g_event.description.split(':')[0]
                temp = g_event.description.split(':')[1]
                start = g_event.start.strftime(_fs)
                end = g_event.end.strftime(_fs)

            print('{}: Heizung {}{}{}'.format(g_event.summary,
                                              'einschalten' if cmd == 'on' else 'ausschalten',
                                              ' auf {} °C'.format(temp) if cmd == 'on' else '',
                                              ' von {} bis {}'.format(start, end) if cmd == 'on' else ''
            ))
            #print('Ort: {}'.format(event.location))



# For more information on the Calendar API you can visit:
#   https://developers.google.com/google-apps/calendar/firstapp
#
# For more information on the Calendar API Python library surface you can visit:
#   https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/
#
# For information on the Python Client Library visit:
#   https://developers.google.com/api-client-library/python/start/get_started
if __name__ == '__main__':

    flags = parser.parse_args(sys.argv[1:])
    gcc = GoogleCalenderConnector(flags)
    gcc.output(gcc.get_events(gcc.service))
