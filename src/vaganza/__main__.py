import os
import json
import string
import argparse
import functools

from vaganza import(
    config,
    commons,
    musicbrainz,
    capitalization
)

import colorama

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
import mutagen.id3 as id3

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

def identitiy(*vargs, sep = ' '):
    return ''.join(functools.reduce(lambda x, y: x + str(y) + sep, vargs))

def white(*args):
    return identitiy(colorama.Fore.WHITE, *args)

def green(*args):
    return identitiy(colorama.Fore.GREEN, *args)

def red(*args):
    return identitiy(colorama.Fore.RED, *args)

def cyan(*args):
    return identitiy(colorama.Fore.CYAN, *args)

def blue(*args):
    return identitiy(colorama.Fore.BLUE, *args)

def magenta(*args):
    return identitiy(colorama.Fore.MAGENTA, *args)

def pretty_print(*args):
    def inner(*vargs):
        return ''.join(functools.reduce(lambda x, y: x + str(y) + ' ', vargs))
    print(inner(colorama.Fore.WHITE, *args))

def json_print(d):
    print(json.dumps(d, sort_keys = True, indent = 4, separators = (',', ': ')))

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class Artist(object):
    def __init__(self, name, dir):
        self.name = name
        self.albums = {}
        self.dir = dir
        self.path = os.path.normpath(self.dir + '/' + self.name)

class Album(object):
    def __init__(self, title, dir):
        self.title = title
        self.discs = []
        self.dir = dir
        self.release = None
        self.path = os.path.normpath(self.dir + '/' + self.title)

    def get_num_tracks(self):
        return sum(map(lambda x: len(x.tracks), self.discs))

    def fix_tags(self, artist):
        for disc in self.discs:
            for track in disc.tracks:
                disc.tracks[track].fix_tags(self.release, disc, artist)
                disc.tracks[track].rename()
        self.rename()

    def rename(self):
        year = self.release['date'].split('-')[0]
        os.rename(self.path, self.dir + '/' + self.release['title'] + ' (' + year + ')')

class Disc(object):
    def __init__(self, number, dir):
        self.number = number
        self.tracks = {}
        self.dir = dir
        self.path = dir

class Track(object):
    def __init__(self, title, dir):
        self.title = title
        self.dir = dir
        self.recording = None
        self.path = os.path.normpath(self.dir + '/' + self.title)
        self.number = 0
        self.extension = get_file_extension(self.title)

    def rename(self):
        if not self.recording:
            os.rename(self.path, self.dir + '/' + get_file_name_without_extension(self.title) + '_CORRECT' + '.' + self.extension)
            return
        n = int(self.number)
        if n < 10:
            self.number = '0' + str(self.number)
        os.rename(self.path, self.dir + '/' + self.number + '. ' + self.recording['title'] + '.' + self.extension)

    def fix_tags(self, release, disc, artist):
        if not self.recording:
            return
        audio = None
        if get_file_extension(self.title) == 'mp3':
            self.fix_mp3_tags(release, disc, artist)
        else:
            self.fix_mp4_tags(release, disc, artist)
            

    def fix_mp4_tags(self, release, disc, artist):
        audio = MP4(self.path)
        tags = audio.tags
        tags['\xa9nam'] = 'KIIIR'
        audio.save()

    def fix_mp3_tags(self, release, disc, artist):
        audio = id3.ID3(self.path)
        year = release['date'].split('-')[0]
        audio.add(id3.TIT2(text = self.recording['title'])) # song title
        audio.add(id3.TALB(text = release['title'])) # album
        audio.add(id3.TPE1(text = artist['name'])) # artist
        audio.add(id3.TOPE(text = artist['name'])) # artist
        audio.add(id3.TOLY(text = artist['name'])) # artist
        audio.add(id3.TPOS(text = str(disc.number))) # disc number
        audio.add(id3.TRCK(text = str(self.number))) # track number
        audio.add(id3.TDRC(text = year)) # date
        #TODO audio.delall('TCON') # genre
        audio.save()
        print('deleting excess tags')
        # Delete these
        # Identification frames
        audio.delall('TIT3')
        audio.delall('TOAL')
        audio.delall('TSST')
        audio.delall('TSRC')
        # Involved persons frames
        # audio.delall('TPE1')
        audio.delall('TPE2')
        audio.delall('TPE3')
        audio.delall('TPE4')
        audio.delall('TOPE')
        audio.delall('TEXT')
        audio.delall('TOLY')
        audio.delall('TCOM')
        audio.delall('TMCL')
        audio.delall('TIPL')
        audio.delall('TENC')
        # Derived and subjective properties frames
        audio.delall('TOLY')
        audio.delall('TLEN')
        audio.delall('TKEY')
        audio.delall('TLAN')
        audio.delall('TFLT')
        audio.delall('TMED')
        audio.delall('TMOO')
        # Rights and license frames
        audio.delall('TCOP')
        audio.delall('TPRO')
        audio.delall('TPUB')
        audio.delall('TOWN')
        audio.delall('TRSN')
        audio.delall('TRSO')
        # Other text frames
        audio.delall('TOFN')
        audio.delall('TDLY')
        audio.delall('TDEN')
        audio.delall('TDOR')# "Original Date"
        audio.delall('TDRL')
        audio.delall('TDTG')
        audio.delall('TSSE')
        audio.delall('TSOA')
        audio.delall('TSOP')
        audio.delall('TSOT')
        # User defined text information frame
        audio.delall('TXXX')
        # URL link frames
        audio.delall('WXXX')
        alphabet = 'abcdefghijklmnopqrstuvwqyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for c1 in alphabet:
            for c2 in alphabet:
                for c3 in alphabet:
                    frame = 'W' + c1 + c2 + c3
                    audio.delall(frame)
        # URL link frames - details
        audio.delall('WCOM')
        audio.delall('WCOP')
        audio.delall('WOAF')
        audio.delall('WOAR')
        audio.delall('WOAS')
        audio.delall('WORS')
        audio.delall('WPAY')
        audio.delall('WPUB')
        # Music CD identifier
        audio.delall('MCDI')
        # Event timing codes
        audio.delall('ETCO')
        # MPEG location lookup table
        audio.delall('MLLT')
        # Synchronised tempo codes
        audio.delall('SYTC')
        #TODO Unsynchronised lyrics/text transcription
        audio.delall('USLT')
        # Synchronised lyrics/text
        audio.delall('SYLT')
        # Comments
        audio.delall('COMM')
        # Relative volume adjustment
        audio.delall('RVA2')
        # Equalisation
        audio.delall('EQU2')
        # Reverb
        audio.delall('RVRB')
        # Geneal encapsulated object
        audio.delall('GEOB')
        # Play counter
        audio.delall('PCNT')
        # Popularimeter
        audio.delall('POPM')
        # Recommended buffer size
        audio.delall('RBUF')
        # Audio encryption
        audio.delall('AENC')
        # Linked information
        audio.delall('LINK')
        # Position synchronisation frame
        audio.delall('POSS')
        # Term of use frame
        audio.delall('USER')
        # Ownership frame
        audio.delall('OWNE')
        # Commercial frame
        audio.delall('COMR')
        # Encryption method registration
        audio.delall('ENCR')
        # Group identification registration
        audio.delall('GRID')
        # Private frame
        audio.delall('PRIV')
        # Signature
        audio.delall('SIGN')
        # Seek frame
        audio.delall('SEEK')
        # Audio seek point index
        audio.delall('ASPI')
        # 
        audio.save()

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
    return result[:-1].strip()

def get_artist_for_directory(path, artists):
    for artist in artists:
        if path == artists[artist].path:
            return artists[artist]
    return None

def get_album_for_directory(path, artists):
    for artist in artists:
        for album in artists[artist].albums:
            if path == artists[artist].albums[album].path:
                return artists[artist].albums[album]
    return None

def get_disc_for_directory(path, artists):
    for artist in artists:
        for album in artists[artist].albums:
            for disc in artists[artist].albums[album].discs:
                if path == disc.path:
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
                artists[artist] = Artist(name = artist, dir = dirpath)
            continue
        # if we are inside an artist directory
        artist = get_artist_for_directory(dirpath, artists)
        if artist:
            for album in dirnames:
                print('\tfound album', album)
                artist.albums[album] = Album(title = album, dir = dirpath)
            continue
        # if we are inside an album directory
        album = get_album_for_directory(dirpath, artists)
        if album:
            found = False
            for disc in dirnames:
                if disc.startswith('Disc'):
                    found = True
                    #TODO we are cheating here, I've assumed disk directories are manually fixed
                    number = int(disc[5:])
                    album.discs.append(Disc(number = number, dir = dirpath + '/Disc ' + str(number)))
                    print('\t\tfound disc', disc)
            # single disc album
            if not found:
                album.discs.append(Disc(number = 1, dir = dirpath))
                for track in filenames:
                    if is_audio_track(track):
                        album.discs[0].tracks[track] = Track(title = track, dir = dirpath)
                    # print('\t\t\tfound track', track)
            continue
        # we are inside a disc direcotry
        disc = get_disc_for_directory(dirpath, artists)
        if disc:
            for track in filenames:
                if is_audio_track(track):
                    disc.tracks[track] = Track(title = track, dir = dirpath)
                # print('\t\t\tfound track', track)
            continue
    # 
    for artist in artists:
        for album in artists[artist].albums:
            # if 'atoma' in album.lower():
            musicbrainz.get_album_track_list(artists[artist], artists[artist].albums[album])