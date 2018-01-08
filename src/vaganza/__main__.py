import os
import json
import string
import argparse
import functools
import traceback
import subprocess

from vaganza import(
    config,
    commons,
    musicbrainz,
    capitalization
)

import PIL.Image as Image
import colorama

from mutagen.mp3 import MP3
from mutagen.mp4 import *
import mutagen.id3 as id3

from googleapiclient.discovery import build

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
        return (''.join(functools.reduce(lambda x, y: x + str(y) + ' ', vargs))) + colorama.Fore.WHITE
    print(inner(colorama.Fore.WHITE, *args))

def json_print(d):
    print(json.dumps(d, sort_keys = True, indent = 4, separators = (',', ': ')))

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

class Artist(object):
    def __init__(self, name, dir):
        self.dir = dir
        self.name = name
        self.path = os.path.join(self.dir, self.name)
        self.albums = {}

class Album(object):
    def __init__(self, title, dir):
        self.dir = dir
        self.path = os.path.join(self.dir, title)
        self.discs = []
        self.front = None
        self.title = title
        self.release = None
        if '_CORRECT' in self.title:
            self.title = self.title.replace('_CORRECT', '')
            os.rename(self.path, self.dir + '/' + self.title)
            self.path = os.path.join(self.dir, self.title)

    def search_cover_art_google(self, artist):
        try:
            service = build("customsearch", "v1", developerKey = commons.google_api_key)
            q = artist.name + ' ' + self.title
            print(q)
            resolutions = ['large', 'xlarge', 'xxlarge', 'huge']
            for resolution in resolutions:
                res = service.cse().list(q = artist.name + ' ' + self.title, imgSize = resolution, cx = commons.search_engine_name).execute()
                for item in res['items']:
                    if 'pagemap' in item:
                        if 'cse_image' in item['pagemap']:
                            subprocess.call(['wget', '-P', os.path.join(self.dir, self.title, 'covers'), item['pagemap']['cse_image'][0]['src']])
            self.pick_cover()
        except:
            traceback.print_exc()

    def pick_cover(self):
        path = os.path.join(self.dir, self.title, 'covers')
        best = None
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                if not get_file_extension(filename).lower() == 'jpg':
                    os.remove(os.path.join(dirpath, filename))
                else:
                    im = Image.open(os.path.join(dirpath, filename))
                    width, height = im.size
                    if abs(width - height) < 50: # this is square image
                        if min(width, height) > 600: # large enough
                            if not best:
                                best = (filename, width, height)
                            else:
                                if max(best[1], best[2]) < max(width, height):
                                    best = (filename, width, height)
                        else:
                            # os.remove(os.path.join(dirpath, filename))
                            pass
                    else:
                        # os.remove(os.path.join(dirpath, filename))
                        pass
        if best:
            for disc in self.discs:
                os.rename(os.path.join(path, best[0]), os.path.join(disc.dir, 'Cover.jpg'))
        else:
            pretty_print(red('couldn\'t find any good enough images, you may want to search manually'))
        # os.rmdir(path)

    def get_num_tracks(self):
        return sum(map(lambda x: len(x.tracks), self.discs))

    def set_cover_arts(self, artist):
        if not os.path.isfile(os.path.join(self.discs[0].dir, 'Cover.jpg')):
            print('no cover art available searching for one')
            self.search_cover_art_google(artist)
        for disc in self.discs:
            for track in disc.tracks:
                disc.tracks[track].set_cover_art(self)

    def fix_tags(self, artist):
        for disc in self.discs:
            for track in disc.tracks:
                disc.tracks[track].fix_tags(self, disc, artist)
                disc.tracks[track].rename()
        self.rename()

    def rename(self):
        if not self.release:
            os.rename(self.path, self.path + '_CORRECT')
            return
        year = self.release['date'].split('-')[0]
        os.rename(self.path, self.dir + '/' + self.release['title'].replace('/', '-') + ' (' + year + ')')

class Disc(object):
    def __init__(self, number, dir):
        self.dir = dir
        self.path = dir
        self.number = number
        self.tracks = {}

class Track(object):
    def __init__(self, title, dir):
        self.dir = dir
        self.path = os.path.join(self.dir, title)
        self.title = title
        self.number = 0
        self.extension = get_file_extension(self.title)
        self.recording = None
        if '_CORRECT' in self.title:
            self.title = self.title.replace('_CORRECT', '')
            os.rename(self.path, self.dir + '/' + self.title)
            self.path = os.path.join(self.dir, self.title)

    def convert(self):
        try:
            ext = get_file_extension(self.title)
            if ext.lower() == 'flac':
                pretty_print(magenta('convertin FLAC to ALAC:', self.title))
                subprocess.call(['ffmpeg', '-i', self.path, '-acodec', 'alac', os.path.join(self.dir, get_file_name_without_extension(self.title) + '.m4a')])
                self.title = get_file_name_without_extension(self.title) + '.m4a'
                self.extension = get_file_extension(self.title)
                self.path = os.path.join(self.dir, self.title)
        except:
            traceback.print_exc()

    def rename(self):
        if not self.recording:
            os.rename(self.path, self.dir + '/' + get_file_name_without_extension(self.title) + '_CORRECT' + '.' + self.extension)
            return
        # for some EPs or Singles the track number might not be an int but rather a side name
        try:
            n = int(self.number)
            if n < 10:
                self.number = '0' + str(self.number)
        except:
            pass
        os.rename(self.path, self.dir + '/' + self.number + '. ' + self.recording['title'].replace('/', '-').replace(':', ' -') + '.' + self.extension)

    def fix_tags(self, album, disc, artist):
        self.convert()
        if get_file_extension(self.title) == 'mp3':
            self.fix_mp3_tags(album, disc, artist)
        else:
            self.fix_mp4_tags(album, disc, artist)

    def set_cover_art(self, album):
        t = get_file_name_without_extension(self.title)
        self.number = str(t.split('.')[0])
        t = t[t.find('.') + 2:]
        if get_file_extension(self.title) == 'mp3':
            audio = id3.ID3(self.path)
            audio.add(id3.TIT2(text = t))
            audio.add(id3.TRCK(text = str(self.number))) # track number
            audio.delall('APIC')
            try:
                with open(os.path.join(self.dir, 'Cover.jpg'), 'rb') as cover_file:
                    audio.add(id3.APIC(3, 'image/png', 3, 'Cover', cover_file.read()))
            except:
                pass
            audio.save()
        else:
            audio = MP4(self.path)
            tags = audio.tags
            tags.pop('covr', None)
            tags['\xa9nam'] = t
            tags['trkn'] = [(int(self.number), album.get_num_tracks())] # track number
            try:
                with open(os.path.join(self.dir, 'Cover.jpg'), 'rb') as cover_file:
                    tags['covr'] = [
                        MP4Cover(cover_file.read(), imageformat = MP4Cover.FORMAT_JPEG)
                    ]
            except:
                pass
            audio.save()

    def fix_mp4_tags(self, album, disc, artist):
        audio = MP4(self.path)
        tags = audio.tags
        extra_tags = []
        for key in tags:
            if key.startswith('--'):
                extra_tags.append(key)
        tags['\xa9nam'] = self.recording['title'] if self.recording else get_file_name_without_extension(self.title) # song title
        tags['\xa9alb'] = album.release['title'] # album
        tags['\xa9ART'] = artist['name'] # artist
        tags['aART'] = artist['name'] # album artist
        tags['\xa9day'] = album.release['date'].split('-')[0]
        tags['trkn'] = [(int(self.number), album.get_num_tracks())] # track number
        # if self.recording:
        #     try:
        #         # tags.pop('trkn', None)
        #         tags['trkn'] = [(int(self.number), album.get_num_tracks())] # track number
        #     except:
        #         traceback.print_exc()
        try:
            tags['disk'] = [(int(disc.number), len(album.discs))] # disc number
        except:
            traceback.print_exc()
        #TODO tags['\xa9gen'] # genre
        #TODO tags['\xa9lyr'] # lyrics
        tags.pop('covr', None)
        if album.front:
            tags['covr'] = [
                MP4Cover(album.front, imageformat = MP4Cover.FORMAT_JPEG)
            ]
        audio.save()
        # remove extra stuff
        tags.pop('\xa9wrt', None)
        tags.pop('\xa9cmt', None)
        tags.pop('desc', None)
        tags.pop('purd', None)
        tags.pop('\xa9grp', None)
        tags.pop('purl', None)
        tags.pop('egid', None)
        tags.pop('catg', None)
        tags.pop('keyw', None)
        tags.pop('\xa9too', None)
        tags.pop('cprt', None)
        tags.pop('soal', None)
        tags.pop('soaa', None)
        tags.pop('soar', None)
        tags.pop('sonm', None)
        tags.pop('soco', None)
        tags.pop('sosn', None)
        tags.pop('tvsh', None)
        tags.pop('\xa9wrk', None)
        tags.pop('\xa9mvn', None)
        # boolean values
        tags.pop('cpil', None)
        tags.pop('pgap', None)
        tags.pop('pcst', None)
        # integer values
        tags.pop('tmpo', None)
        tags.pop('\xa9mvc', None)
        tags.pop('\xa9mvi', None)
        tags.pop('shwm', None)
        tags.pop('stik', None)
        tags.pop('rtng', None)
        tags.pop('tves', None)
        tags.pop('tmpo', None)
        tags.pop('tvsn', None)
        # iTunes internal IDs
        tags.pop('plID', None)
        tags.pop('cnID', None)
        tags.pop('geID', None)
        tags.pop('atID', None)
        tags.pop('sfID', None)
        tags.pop('cmID', None)
        tags.pop('akID', None)
        # custom -- tags
        for tag in extra_tags:
            tags.pop(tag, None)
        audio.save()

    def fix_mp3_tags(self, album, disc, artist):
        audio = id3.ID3(self.path)
        audio.add(id3.TIT2(text = self.recording['title'] if self.recording else get_file_name_without_extension(self.title))) # song title
        audio.add(id3.TALB(text = album.release['title'])) # album
        audio.add(id3.TPE1(text = artist['name'])) # artist
        audio.add(id3.TOPE(text = artist['name'])) # artist
        audio.add(id3.TPOS(text = str(disc.number))) # disc number
        # if self.recording:
        audio.add(id3.TRCK(text = str(self.number))) # track number
        audio.add(id3.TDRC(text = album.release['date'].split('-')[0])) # date
        audio.delall('APIC')
        if album.front:
            audio.add(id3.APIC(3, 'image/png', 3, 'Cover', album.front))
        #TODO audio.delall('TCON') # genre
        audio.save()
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

def iterate_scans(path):
    print('iterating scans', path)
    # first change everything to a temporary name so that the new names will not overwrite old files in case they are
    # already named in this format 
    n = 1
    for (dirpath, dirnames, filenames) in os.walk(path):
        print(dirpath, dirnames, filenames)
        for filename in filenames:
            ext = get_file_extension(filename)
            number = str(n) if n > 10 else '0' + str(n)
            base = 'KIRE_KHAR_' + number
            n += 1
            os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, base + '.' + ext))
    n = 1
    for (dirpath, dirnames, filenames) in os.walk(path):
        print(dirpath, dirnames, filenames)
        for filename in filenames:
            ext = get_file_extension(filename)
            number = str(n) if n > 10 else '0' + str(n)
            n += 1
            os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, number + '.' + ext))

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
                pretty_print('found artist', artist)
                artists[artist] = Artist(name = artist, dir = dirpath)
            continue
        # if we are inside an artist directory
        artist = get_artist_for_directory(dirpath, artists)
        if artist:
            for album in dirnames:
                pretty_print('\tfound album', album)
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
                    pretty_print('\t\tfound disc', disc)
                if disc == 'Scans':
                    iterate_scans(os.path.join(dirpath, disc))
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
            try:
            # if 'atoma' in album.lower():
                if c.set_covers:
                    artists[artist].albums[album].set_cover_arts(artists[artist])
                    # artists[artist].albums[album].search_cover_art_google(artists[artist])
                else:
                    musicbrainz.get_album_track_list(artists[artist], artists[artist].albums[album])
            except:
                pretty_print(colorama.Fore.RED + 'couldn\'t fix tags for album', magenta(album))
                traceback.print_exc()
