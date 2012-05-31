#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import urllib
import urllib2
from snoop import *
from xml.dom.minidom import parseString

API_KEY = '3872d838749d5d80eda9e3870c8b5e2a'

# last.fm account details

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

def getArtistImage(artist_name):
    params = urllib.urlencode({'method': 'artist.getinfo', 'artist': artist_name, 'api_key': API_KEY})
    url = "http://ws.audioscrobbler.com/2.0/?" + params

    xml = urllib2.urlopen(url).read()


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class TagCloudHandler(Handler):
    def get(self):
        artists = getArtists()
        self.render("tag_cloud.html", artists = artists, word_cloud = None,artist_name = "")
        
    def post(self):
        artists = getArtists()
        artist_id = self.request.get("artist_id")
        artist_name = self.request.get("artist")
        word_count = getWordCountsForArtist(Artist(artist_id,artist_name))
        self.render("tag_cloud.html", artists = artists, word_cloud = word_count, artist_name = artist_name)
        

app = webapp2.WSGIApplication([('/tag_cloud', TagCloudHandler)],
                              debug=True)
