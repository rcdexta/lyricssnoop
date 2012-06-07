import webapp2
import jinja2
import os
import urllib
import urllib2
import logging
from snoop import *
from album import *
from xmlobj import xml2obj
from HTMLParser import HTMLParser

API_KEY = '3872d838749d5d80eda9e3870c8b5e2a'

# last.fm account details

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def stripTags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def getLargestImage(images, image_pref):
    image_url = None
    images.reverse()
    for image in images:
        if image.size == image_pref[0]:
            image_url = image.data
            break
        elif image.size == image_pref[1]:
            image_url = image.data
    return image_url


def getTopAlbums(artist):
    params = urllib.urlencode({'method': 'artist.gettopalbums', 'artist': artist.name, 'api_key': API_KEY})
    url = "http://ws.audioscrobbler.com/2.0/?" + params
    xml = urllib2.urlopen(url).read()
    lfm = xml2obj(xml)
    albums = []
    for node in lfm.topalbums.album:
        album = Album(name = node.name)
        logging.error(node.image)
        album.image_url = getLargestImage(node.image, ["large", "extralarge"])
        albums.append(album)
        if len(albums) == 4: break

    return albums

def getArtistDetails(artist):
    params = urllib.urlencode({'method': 'artist.getinfo', 'artist': artist.name, 'api_key': API_KEY})
    url = "http://ws.audioscrobbler.com/2.0/?" + params
    xml = urllib2.urlopen(url).read()
    lfm = xml2obj(xml)
    artist.bio = stripTags(lfm.artist.bio.summary)
    populateArtistImage(artist, lfm)
    populateArtistTags(artist, lfm)
    return artist

def populateArtistTags(artist, lfm):
    for tag in lfm.artist.tags.tag:
        artist.tags.append(tag.name)

def populateArtistImage(artist, lfm):
    images =  lfm.artist.image
    artist.image_url = getLargestImage(images, ["extralarge", "large"])
    

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
        self.render("tag_cloud.html", artists = artists, word_cloud = None, artist = Artist("",""))
        
    def post(self):
        artists = getArtists()
        artist = Artist(self.request.get("artist_id"),self.request.get("artist"))
        word_cloud = getWordCountsForArtist(artist)
        artist = getArtistDetails(artist)
        albums = getTopAlbums(artist)
        self.render("tag_cloud.html", artists = artists, word_cloud = word_cloud, artist = artist, albums = albums)
        

app = webapp2.WSGIApplication([('/tag_cloud', TagCloudHandler)], debug=True)
                              