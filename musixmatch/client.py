# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
import logging

logger = logging.getLogger('musixmatch.queries')

API_VERSION = "1.1"
API_URL = "http://api.musixmatch.com/ws/1.1/"
API_ENCODING = "utf-8"
DEBUG = False

__all__ = ['API_VERSION', 'MusiXMatch', 'ApiResponseException', 'InvalidRequest',
'AuthenticationFailed', 'RequestLimitReached', 'UnauthorizedOperation', 'MethodNotFound']

def clean_querydict(data):
    if not DEBUG:
        # hide the api key in case and exception is throwed
        if 'apikey' in data:
            data['apikey'] = '*' * len(data['apikey'])
    return data

class ApiResponseException(Exception):
    pass


class InvalidRequest(ApiResponseException):
    pass


class AuthenticationFailed(ApiResponseException):
    pass


class RequestLimitReached(ApiResponseException):
    pass


class UnauthorizedOperation(ApiResponseException):
    pass


class ResourceNotFound(ApiResponseException):
    pass


class MethodNotFound(ApiResponseException):
    pass


RESPONSE_STATUS = {
    400: InvalidRequest,
    401: AuthenticationFailed,
    402: RequestLimitReached,
    403: UnauthorizedOperation,
    404: ResourceNotFound,
    405: MethodNotFound,
}

DEFAULT_PAGE_SIZE = 10


class MusiXMatch(object):
    def __init__(self, api_key, format='json'):
        self.api_key = api_key
        self.api_format = format
        self.track = TrackApiMethods(api_key, format)
        self.artist = ArtistApiMethods(api_key, format)
        self.album = AlbumApiMethods(api_key, format)


class BaseApiMethods(object):

    def __init__(self, api_key, format):
        self.opener = urllib2.build_opener()
        self.api_key = api_key
        self.api_format = format
        self.last_requested_url = None

    def makeRequest(self, method, params):
        url = "".join([API_URL, method])
        data = params.copy()
        data.update({
            'apikey': self.api_key,
            'format': self.api_format
        })
        self.last_requested_url = url, urllib.urlencode(data)
        logger.debug("[musixmatch] %s %s", method, data)
        response = self.opener.open("?".join([url, urllib.urlencode(data)]))
        response = self.parseResponse(response.read())

        status_code = response['message']['header']['status_code']

        # I raise an exception for each response different than 200 so i can catch it in a
        # second moment if i really want
        if status_code != 200:
            exception = RESPONSE_STATUS.get(status_code, ApiResponseException)
            raise exception(url, status_code, response, clean_querydict(data))

        return response

    def parseResponse(self, response):
        if self.api_format == 'json':
            return json.loads(response)

        raise Exception("Unimplemented format %s" % self.api_format)

    def cleanQueryDict(self, search_dict):
        """
        This method is used to cleanup the query dictionary from the None values
        """
        keys = []
        for key, value in search_dict.items():
            if value is None:
                keys.append(key)
        for key in keys:
            del search_dict[key]

        return search_dict


class LirycsApiMethods(BaseApiMethods):
    get_method = 'track.lyrics.get'
    post_method = 'track.lyrics.post'
    feedback_post_method = 'track.lyrics.feedback.post'

    def get(self, track_id):
        response = self.makeRequest(self.get_method, {'track_id': track_id})
        return Lirycs(response['message']['body']['lyrics'])
    
    def post_feedback(self, lyrics_id, track_id, feedback):
        VALID_FEEDBACK = ['wrong_attribution', 'bad_characters', 'lines_too_long', 'wrong_verses', 'wrong_formatting']
        if feedback not in VALID_FEEDBACK:
            raise Exception("Invalid feedback, must be in in {0}".format(VALID_FEEDBACK))
        
        return self.makeRequest(self.feedback_post_method, { 'lyrics_id': lyrics_id,  
                                                        'track_id': track_id, 'feedback': feedback})
    
    def post(self, track_id, lyrics_body):
        """
        track_id: the track identifier
        body: body of the lyrics
        """
        return self.makeRequest(self.post_method, { 'track_id': track_id, 
                                                    'lyrics_body': lyrics_body})

    def getByTrackMbid(self, track_mbid):
        response = self.makeRequest(self.get_method, {'track_mbid': track_mbid})
        return Lirycs(response['message']['body']['lyrics'])


class TrackApiMethods(BaseApiMethods):
    search_method = 'track.search'
    get_method = 'track.get'

    def __init__(self, api_key, format):
        super(TrackApiMethods, self).__init__(api_key, format)
        self.lyrics = LirycsApiMethods(api_key, format)
        self.chart = TrackChartApiMethods(api_key, format)

    def search( self, 
                q=None, 
                q_track=None, 
                q_artist=None, 
                q_track_artist=None,
                q_lyrics=None, 
                page=None, 
                page_size=DEFAULT_PAGE_SIZE,
                f_has_lyrics=None, 
                f_artist_id=None, 
                f_artist_mbid=None,
                quorum_factor=None):
    
        """
        q: a string that will be searched in every data field (q_track, q_artist, q_lyrics)
        q_track: words to be searched among track titles
        q_artist: words to be searched among artist names
        q_track_artist: words to be searched among track titles or artist names
        q_lyrics: words to be searched into the lyrics
        page: requested page of results
        page_size: desired number of items per result page
        f_has_lyrics: exclude tracks without an available lyrics (automatic if q_lyrics is set)
        f_artist_id: filter the results by the artist_id
        f_artist_mbid: filter the results by the artist_mbid
        quorum_factor: only works together with q and q_track_artist parameter.
            Possible values goes from 0.1 to 0.9
            A value of 0.9 means: “match at least 90% of the given words”.
        """
        query = {
            'q': q,
            'q_track': q_track,
            'q_artist': q_artist,
            'q_track_artist': q_track_artist,
            'q_lyrics': q_lyrics,
            'page': page,
            'page_size': page_size,
            'f_has_lyrics': f_has_lyrics,
            'f_artist_id': f_artist_id,
            'f_artist_mbid': f_artist_mbid,
            'quorum_factor': quorum_factor
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.search_method, query)
        return TrackSearchResults(response, self)

    def get(self, track_id=None, track_mbid=None):
        query = {
            'track_id': track_id,
            'track_mbid': track_mbid
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return Track(response['message']['body']['track'], self)

class TrackChartApiMethods(BaseApiMethods):
    get_method = 'track.chart.get'

    def get(self, country=None, f_has_lyrics=False, page=None, page_size=DEFAULT_PAGE_SIZE):
        """
        Returns a list of tracks ordered by score of a given country

        page: requested page of results
        page_size: desired number of items per result page
        country: the country code of the desired country chart (refer to [[input-parameters]] page for allowed values)
        f_has_lyrics: exclude tracks without an available lyrics
        """
        query = {
            'country': country,
            'f_has_lyrics': f_has_lyrics,
            'page': page,
            'page_size': page_size
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return TrackSearchResults(response, self)


class ArtistChartApiMethods(BaseApiMethods):
    get_method = 'artist.chart.get'

    def get(self, country=None, page=None, page_size=DEFAULT_PAGE_SIZE):
        """
        Returns a list of artists ordered by score of a given country
        
        country: the country code of the desired country chart (refer to input parameters page for allowed values)
        page: requested page of results
        page_size: desired number of items per result page
        """
        query = {
            'country': country,
            'page': page,
            'page_size': page_size
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return ArtistSearchResults(response, self)


class ArtistApiMethods(BaseApiMethods):
    search_method = 'artist.search'
    get_method = 'artist.get'

    def __init__(self, api_key, format):
        super(ArtistApiMethods, self).__init__(api_key, format)
        self.albums = ArtistAlbumApiMethods(api_key, format)
        self.chart = ArtistChartApiMethods(api_key, format)

    def search(self, q=None, q_track=None, q_artist=None, q_lyrics=None,
                page=None, page_size=DEFAULT_PAGE_SIZE, f_has_lyrics=None,
                f_artist_id=None, f_artist_mbid=None, quorum_factor=None):
        """
        q: a string that will be searched in every data field (q_track, q_artist, q_lyrics)
        q_track: words to be searched among tracks titles
        q_artist: words to be searched among artists names
        q_lyrics: words to be searched into the lyrics
        page: requested page of results
        page_size: desired number of items per result page
        f_has_lyrics: exclude artists without any available lyrics (automatic if q_lyrics is set)
        f_artist_id: filter the results by the artist_id
        f_artist_mbid: filter the results by the artist_mbid
        """
        query = {
            'q': q,
            'q_track': q_track,
            'q_artist': q_artist,
            'q_lyrics': q_lyrics,
            'page': page,
            'page_size': page_size,
            'f_has_lyrics': f_has_lyrics,
            'f_artist_id': f_artist_id,
            'f_artist_mbid': f_artist_mbid,
            'quorum_factor': quorum_factor
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.search_method, query)
        return ArtistSearchResults(response, self)

    def get(self, artist_id=None, artist_mbid=None):
        """
        artist_id | artist_mbid : the artist identifier expressed as a musiXmatch ID or musicbrainz ID
        """
        query = {
            'artist_id': artist_id,
            'artist_mbid': artist_mbid,
        }

        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return Artist(response['message']['body']['artist'], self) 

class AbstractSearchResults(object):

    def __init__(self, response, api):
        self.api = api
        self.object_class = None
        self.response = response
        self.message = response['message']
        self.header = self.message['header']
        self.execute_time = self.header['execute_time']
        self.available = self.header.get('available')
        self.body = self.message['body']
        self.items = []

    def __getitem__(self, index):
        return self.object_class(self.items[index], self.api)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        for ob in self.items:
            yield self.object_class(ob, self.api)


class Track(object):
    """
    Rappresent track returned from the api
    """
    def __init__(self, item, api):
        self.api = api
        self.id = item['track_id']
        self.mbid = item['track_mbid']
        self.lyrics_id = item['lyrics_id'] or None # This is here because is possible that mnusixmatch return 0 instead of a valid id
        self.instrumental = item['instrumental']
        self.subtitle_id = item['subtitle_id']
        self.track_name = item['track_name']
        self.album_coverart_100x100 = item['album_coverart_100x100']
        self.artist_id = item['artist_id']
        self.artist_mbid = item['artist_mbid']
        self.artist_name = item['artist_name']
        self.album_name = item['album_name']
        self.album_id = item['album_id']

    def getLyrics(self):
        """
        Make an extra call to the api to return a lyrics object with the effective 
        lyrics of the song, to perform the get uses the musixmatch id of the track
        """
        return self.api.lyrics.get(self.id)

    def getLyricsByMdib(self):
        """
        Make an extra call to the api to return a lyrics object with the effective 
        lyrics of the song, to perform the get use the mbid of the song
        """
        return self.api.lyrics.getByTrackMbid(self.mbid)

class ArtistAlbumApiMethods(BaseApiMethods):
    get_method = 'artist.albums.get'
    
    def get(self, artist_id=None, page=None, page_size=DEFAULT_PAGE_SIZE, g_album_name=None,
            s_release_date=None):
        """
        artist_id: the album identifier expressed as a musiXmatch ID
        page: requested page of results
        page_size: desired number of items per page
        g_album_name: group albums by name to avoid duplicates
        s_release_date: sort by release date (desc/asc)
        """
        query = {
            'artist_id': artist_id, 
            'page': page, 
            'page_size': page_size, 
            'g_album_name': g_album_name,
            's_release_date': s_release_date
        }
        
        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return AlbumSearchResults(response, self)


class AlbumTracksApiMethods(BaseApiMethods):
    get_method = 'album.tracks.get'

    def get(self, album_id=None):
        """
        album_id: the album identifier expressed as a musiXmatch ID
        """
        query = {
            'album_id': album_id, 
        }
        
        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return TrackSearchResults(response, self)


class AlbumApiMethods(BaseApiMethods):
    get_method = 'album.get'

    def __init__(self, api_key, format):
        super(AlbumApiMethods, self).__init__(api_key, format)
        self.tracks = AlbumTracksApiMethods(api_key, format)
        self.tracks = AlbumTracksApiMethods(api_key, format)
        

    def get(self, album_id=None):
        """
        album_id: the album identifier expressed as a musiXmatch ID
        """
        query = {
            'album_id': album_id, 
        }
        
        query = self.cleanQueryDict(query)
        response = self.makeRequest(self.get_method, query)
        return Album(response['message']['body']['album'], self)

class Album(object):
    
    def __init__(self, item, api):
        self.api = api
        self.id = item['album_id']
        self.mbid = item['album_mbid']
        self.artist_id = item['artist_id']
        self.artist_name = item['artist_name']
        self.name = item['album_name']
        # This value is a possible date formatter value %Y-%m-%d but is possible that the remote
        # call returns an invalid date such as 2000-01-00
        self.release_date = item['album_release_date']
        self.release_type = item['album_release_type']
        self.coverart_100x100 = item['album_coverart_100x100']


class AlbumSearchResults(AbstractSearchResults):
    """
    Iterator for Album search results
    """
    def __init__(self, response, api):
        super(AlbumSearchResults, self).__init__(response, api)
        self.object_class = Album
        self.items = [ ob['album'] for ob in self.body['album_list'] ]


class Lirycs(object):
    """
    Rappresent a lyrics returned from the api
    """
    def __init__(self, item, api=None):
        self.api = api
        self.id = item['lyrics_id']
        self.body = item['lyrics_body']
        self.language = item['lyrics_language']
        self.restricted = item['restricted']
        self.copyright = item['lyrics_copyright']
        self.pixel_tracking_url = item['pixel_tracking_url']
        self.script_tracking_url = item['script_tracking_url']


class TrackSearchResults(AbstractSearchResults):
    """
    Iterator for Track search results
    """
    def __init__(self, response, api):
        super(TrackSearchResults, self).__init__(response, api)
        self.object_class = Track
        self.items = [ob['track'] for ob in self.body['track_list']]


class Artist(object):
    """
    Rappresent an artist returned from the api
    """
    def __init__(self, item, api=None):
        self.id = item['artist_id']
        self.mbid = item['artist_mbid']
        self.name = item['artist_name']

    def __unicode__(self):
        return u"%s" % self.name


class ArtistSearchResults(AbstractSearchResults):
    """
    Iterator for Artist search results
    """
    def __init__(self, response, api):
        super(ArtistSearchResults, self).__init__(response, api)
        self.object_class = Artist
        self.items = [ ob['artist'] for ob in self.body['artist_list'] ]
