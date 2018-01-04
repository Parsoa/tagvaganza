import os
import argparse

from vaganza import(
    config,
    commons,
    musicbrainz,
    capitalization
)

# ============================================================================================================================ #
# 
# ============================================================================================================================ #

class Artist(object):
    def __init__(self, name, dir):
        self.name = name
        self.albums = {}
        self.dir = dir

class Album(object):
    def __init__(self, title, dir):
        self.title = title
        self.discs = []
        self.dir = dir

    def get_num_tracks(self):
        return sum(map(lambda x: len(x.tracks), self.discs))

class Disc(object):
    def __init__(self, number, dir):
        self.number = number
        self.tracks = {}
        self.dir = dir

class Track(object):
    def __init__(self, title, dir):
        self.title = title
        self.dir = dir

# ============================================================================================================================ #
# file and directory parsing/iteration helpers
# ============================================================================================================================ #

def is_audio_track(filename):
    return get_file_extension(filename).upper() in commons.file_formats

def get_file_extension(filename):
    return filename.split('.')[-1]

def get_file_name_without_extension(filename):
    chunks = filename.split('.')[:-1]
    result = ''
    for chunk in chunks:
        result = result + chunk + '.'
    # get rid of the final dot
    # print('|', result, '|')
    return result[:-1].strip()

def get_artist_for_directory(path, artists):
    for artist in artists:
        if path == artists[artist].dir:
            return artists[artist]
    return None

def get_album_for_directory(path, artists):
    for artist in artists:
        for album in artists[artist].albums:
            if path == artists[artist].albums[album].dir:
                return artists[artist].albums[album]
    return None

def get_disc_for_directory(path, artists):
    for artist in artists:
        for album in artists[artist].albums:
            for disc in artists[artist].albums[album].discs:
                if path == disc.dir:
                    return disc
    return None

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

if __name__ == '__main__':
    config.init()
    c = config.Configuration()
    artists = {}
    # get all artists and album names
    for (dirpath, dirnames, filenames) in os.walk(c.work_dir):
        if dirpath == c.work_dir:
            for artist in dirnames:
                print('found artist', artist)
                artists[artist] = Artist(name = artist, dir = os.path.join(dirpath, artist))
            continue
        # if we are inside an artist directory
        artist = get_artist_for_directory(dirpath, artists)
        if artist:
            for album in dirnames:
                print('\tfound album', album)
                artist.albums[album] = Album(title = album, dir = os.path.join(dirpath, album))
            continue
        # if we are inside an album directory
        album = get_album_for_directory(dirpath, artists)
        if album:
            found = False
            for disc in dirnames:
                if disc.startswith('Disc'):
                    found = True
                    #TODO we are cheating here, I've assumed disk directories are manually fixed
                    album.discs.append(Disc(number = int(disc[5:]), dir = os.path.join(dirpath, disc)))
                    print('\t\tfound disc', disc)
            # single disc album
            if not found:
                album.discs.append(Disc(number = 1, dir = dirpath))
                for track in filenames:
                    if is_audio_track(track):
                        album.discs[0].tracks[track] = Track(title = track, dir = os.path.join(dirpath, track))
            continue
        # we are inside a disc direcotry
        disc = get_disc_for_directory(dirpath, artists)
        if disc:
            for track in filenames:
                if is_audio_track(track):
                    disc.tracks[track] = Track(title = get_file_name_without_extension(track),\
                        dir = os.path.join(dirpath, track))
                # print('\t\t\tfound track', track)
            continue
    # 
    for artist in artists:
        for album in artists[artist].albums:
            musicbrainz.get_album_track_list(artists[artist], artists[artist].albums[album])
            # exit()