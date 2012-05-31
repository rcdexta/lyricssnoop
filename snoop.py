import re
from collections import defaultdict
import httplib
import json
import musixmatch
from musixmatch import *
from artist import * 
from os import path
from os import sep


def main():
    stop_file = open('stopwords.txt')
    stop_words = stop_file.read().split("\n")
    lyrics_file = open('lyrics_50cents.txt')
    # print lyrics_file.read()
    lyrics_words = re.findall(r'\w+', lyrics_file.read())
    #print lyrics_words
    lyrics_words = [word.lower() for word in lyrics_words]
    words = list(set(lyrics_words) - set(stop_words))
    
    wordCount = defaultdict(int)
    for word in words:
        wordCount[word] += lyrics_words.count(word)
    
    for key in sorted(wordCount, key=wordCount.__getitem__, reverse=True):
        print key, " : ",  wordCount[key]
   
def parse_musix_url(artistId):
    apikey = 'aea7c70a32c3b8d56a07c99ef9d56ffa'
    artists = musixmatch.ws.artist.albums.get(artist_id=artistId, apikey=apikey)
    albums = []
    for album in artists["body"]["album_list"]:
        albums.append(album["album"]["album_id"])

    tracks = []
    for album_id in albums:
        album_tracks = musixmatch.ws.album.tracks.get(album_id=album_id, apikey=apikey)
        for track in album_tracks["body"]["track_list"]:
            tracks.append(track["track"]["track_id"])
    # print tracks
    
    lyrics=[]
    for trackid in tracks:
        lyric = musixmatch.ws.track.lyrics.get(track_id = trackid, apikey=apikey)
        if lyric["header"]["status_code"] == 200:
            # print lyric["body"]["lyrics"]["lyrics_body"]
            lyrics.append(lyric["body"]["lyrics"]["lyrics_body"])   
    if len(lyrics) > 0:
        return str(lyrics[0])
    else:
        return ''

def getLyricsForArtist(artist):
    lyricsFile = r"lyrics" + sep + "lyrics_" + artist.alias() + ".txt"
    # print lyrics_file
    if(path.exists(lyricsFile)):
        # print 'reading from local file'
        f = open(lyricsFile, 'r')
        lyrics = f.read()
        f.close()
    else:
        return None
        # print 'reading from the web'
        lyrics = str(parse_musix_url(artist.id)[0])
    #print "lyrics are :\n" , lyrics
    return lyrics

def getArtists():
    artist_file = open(r"lyrics" + sep + "artist_info.txt", 'r')
    artists = []
    for info in artist_file.readlines():
        artists.append( Artist(int(info.split(':')[0]), info.split(':')[1].rstrip('\n')
))
    artist_file.close()
    return artists

def tokenize(sentence):
    lyrics_words = re.findall('[^. \n\r\\n]+', sentence)
    lyrics_words = [word.lower() for word in lyrics_words]
    # print "All words : ", lyrics_words
    return lyrics_words
    
def removeStopWords(words):    
    stop_file = open('stopwords.txt')
    stop_words = stop_file.read().split("\n")
    wordSet = list(set(words) - set(stop_words))
    # print "filtered words", wordSet
    return wordSet

def getWordCounts(words, wordSet):    
    wordCount = defaultdict(int)
    for word in wordSet:
        wordCount[word] += words.count(word)
    return wordCount

def getWordCountsForArtist(artist):
    lyrics = getLyricsForArtist(artist)
    if lyrics:
        words = tokenize(lyrics)
        filteredWords = removeStopWords(words)
        return getWordCounts(words, filteredWords)
    else:
        return None
    
if __name__ == "__main__":
    print getArtists()
    #print getWordCountsForArtist(Artist(437407,"LMFAO"))
    # print getLyricsForArtist(getArtists()[7])
    # for artist in getArtists():
        # lyrics = getLyricsForArtist(artist)
        # filepath=r'lyrics\lyrics_' + artist.alias() + '.txt'
        # lyrics_file = open(filepath, 'w')
        # lyrics_file.write(str(lyrics))
    # lyrics_file.close()
    #main()