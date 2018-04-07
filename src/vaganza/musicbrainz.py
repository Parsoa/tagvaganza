import os
import re
import json
import string
import functools
import traceback

from vaganza import(
    config,
    commons,
)

import colorama
import musicbrainzngs

# ============================================================================================================================ #
# http://python-musicbrainzngs.readthedocs.io/en/v0.6/api/
# ============================================================================================================================ #

def identitiy(*vargs, sep = ' '):
    return ''.join(functools.reduce(lambda x, y: x + str(y) + sep, vargs))

def white(*args):
    return identitiy(colorama.Fore.WHITE, *args)

def green(*args):
    return identitiy(colorama.Fore.GREEN, *args, colorama.Fore.WHITE)

def red(*args):
    return identitiy(colorama.Fore.RED, *args, colorama.Fore.WHITE)

def cyan(*args):
    return identitiy(colorama.Fore.CYAN, *args, colorama.Fore.WHITE)

def blue(*args):
    return identitiy(colorama.Fore.BLUE, *args, colorama.Fore.WHITE)

def magenta(*args):
    return identitiy(colorama.Fore.MAGENTA, *args, colorama.Fore.WHITE)

def pretty_print(*args):
    def inner(*vargs):
        return (''.join(functools.reduce(lambda x, y: x + str(y) + ' ', vargs))) + colorama.Fore.WHITE
    print(inner(colorama.Fore.WHITE, *args))

def json_print(d):
    print(json.dumps(d, sort_keys = True, indent = 4, separators = (',', ': ')))

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

def remove_non_ascii_characters(s):
    printable = set(string.printable) #removes non-ascii characters
    s = ''.join(filter(lambda x: x in printable, s))
    return s

def remove_whitespaces(s):
    s = re.sub('\s+', '', s) #removes whitespaces
    return s

def remove_punctuation(s):
    s = re.sub(r'[^\w\s]','',s)
    return s

def remove_ambiguous_characters(s):
    return remove_non_ascii_characters(
                remove_whitespaces(
                    remove_punctuation(
                        s.lower()
                    )
                )
            )

def is_subsequence(x, y):
    # print('compare', blue(x), green(y))
    x = x.lower()
    y = y.lower()
    if len(x) > len(y):
        # print('x > y, switching')
        return is_subsequence(y, x)
    it = iter(y)
    return all(c in it for c in x)

def is_subsequence_randomized(x, y):
    x = x.lower()
    y = y.lower()
    if len(x) > len(y):
        # print('x > y, switching')
        return is_subsequence_randomized(y, x)

def edit_distance(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

# This assumes that the title in the filename is always bigger than the one in the database which can cause problems
def find_minimum_cost_match(results, target, key, tie_breaker = None):
    distance = {}
    p = False
    for result in results:
        t = remove_ambiguous_characters(result[key])
        s = remove_ambiguous_characters(target)
        # pretty_print('comparing', blue(t), 'against', green(s))
        if is_subsequence(t, s):
            distance[result['id']] = edit_distance(target, result[key])
        else:
            distance[result['id']] = 10000000
        if p:
            pretty_print('disatnce to', red(result[key]), '=', distance[result['id']], blue(s), blue(t))
    if not distance:
        return None, None
    # find the minimum distance
    m_id = min(distance, key = distance.get)
    m = distance[m_id]
    print('minimum:', m, m_id)
    # get everything with this distance from target
    candidates = list(filter(lambda x: distance[x['id']] == m, results))
    # print(candidates)
    if tie_breaker:
        # get rid of those without the tie-breaker field
        candidates = list(filter(lambda x: tie_breaker in x, candidates))
        candidates = sorted(candidates, key = lambda x: x[tie_breaker])
        choice = candidates[0]
        # json_print(choice)
    else:
        choice = list(filter(lambda x: x['id'] == m_id, results))[0]
    return choice, not m == 10000000

class memoize:
    def __init__(self, f):
        self.f = f
        self.memo = {}
    def __call__(self, *args):
        if not args in self.memo:
            self.memo[args] = self.f(*args)
        return self.memo[args]

@memoize
def get_all_artist_releases(id):
    results = []
    offset = 0
    while True:
        tmp = musicbrainzngs.search_releases(arid = id, offset = offset)['release-list']
        results = results + tmp
        offset += len(tmp)
        if len(tmp) == 0:
            break
    print('got', len(results), 'total')
    # titles = list(map(lambda x: x['title'], results))
    # print(titles)
    return results

# ============================================================================================================================ #
# ============================================================================================================================ #
# ============================================================================================================================ #

def find_closest_artist(artist):
    c = config.Configuration()
    if c.artist_id:
        pretty_print('searching for artist with id', green(c.artist_id))
        result = musicbrainzngs.get_artist_by_id(id = c.artist_id)['artist']
        json_print(result)
        return result
    else:
        pretty_print('searching for closest artist to', colorama.Fore.GREEN, artist.name)
        results = musicbrainzngs.search_artists(artist = artist.name)['artist-list']
        #TODO make choice an array, in case several artists with the same namem, have the user pick the desired one
        choice, certainty = find_minimum_cost_match(results, artist.name, 'name')
        if not choice:
            pretty_print(colorama.Fore.RED + 'couldn\'t find an artist with a matching name')
            return None
        pretty_print('matched against', colorama.Fore.GREEN, choice['name'])
        return choice

def find_closest_release(artist, album):
    pretty_print('searching for closest album to', green(album.title), white('with'), green(album.get_num_tracks()), white('tracks'))
    results = get_all_artist_releases(artist['id'])
    # 1. find all releases of this artist with a matching name
    # will return the matchin release with the oldest release date, avoid reissues and such
    # we also want to prioritize CD release against Vinyl ones to avoid track numbering issues
    choice, certainty = find_minimum_cost_match(results, album.title, 'title', 'date')
    if not choice:
        album.rename()
        pretty_print(colorama.Fore.RED + 'couldn\'t find a release with matching title')
        return None
    results = list(filter(lambda x: x['title'] == choice['title'], results))
    # 2. among these releases find the one whose number of tracks matches the one at hand
    candidates = list(filter(lambda x: x['medium-track-count'] == album.get_num_tracks(), results))
    if candidates:
        for candidate in candidates:
            if not 'date' in candidate:
                candidate['date'] = '99999999'
        match = sorted(candidates, key = lambda x: x['date'])[0]
        #pretty_print(colorama.Fore.RED + 'couldn\'t find a release with matching rack count, closest match: ', magenta(match['title']),\
        #    white('with'), magenta(match['medium-track-count']), white('tracks'))
        pretty_print('matched against', green(match['title']), white('with'), green(match['medium-track-count']), white('tracks'))
        return match
    # 3. couldn't find an exact match, but try to get as much as of the tracks done as possible
    else:
        pretty_print(colorama.Fore.RED + 'couldn\'t find a release with a matching number of tracks, proceeding with arbitarry one')
        match = results[0] 
        pretty_print('matched against', green(match['title']), white('with'), green(match['medium-track-count']), white('tracks'))
        return match

def find_tracks_in_recording(artist, album, release):
    results = musicbrainzngs.search_recordings(reid = release['id'])['recording-list']
    for disc in album.discs:
        for track in disc.tracks:
            choice, certainty = find_minimum_cost_match(results, track, 'title')
            if not choice or not certainty:
                pretty_print('couldn\'t find a recording with a matching title for', red(track))
                continue
            r = list(filter(lambda x: x['id'] == release['id'], choice['release-list']))[0]
            # print(release['id'])
            # json_print(r)
            # exit()
            # if choice['title'].find('Mine') != -1:
                # json_print(choice)
            r = r['medium-list'][0]['track-list'][0]['number']
            disc.tracks[track].recording = choice
            disc.tracks[track].number = r
            results.pop(results.index(choice))
            pretty_print('matched', blue(track), white('to'),
                green(r + '.' , choice['title']) if certainty else red(r + '.' , choice['title']))

def download_cover_art(album, release):
    try:
        if os.path.isfile(os.path.join(album.path, 'Cover.jpg')):
            pretty_print(cyan('high-res cover photo available'))
            with open(os.path.join(album.path, 'Cover.jpg'), 'rb') as cover_file:
                album.front = cover_file.read()
        else:
            front = musicbrainzngs.get_release_group_image_front(release['release-group']['id'])
            for disc in album.discs:
                with open(os.path.join(disc.dir, 'Cover.jpg'), 'wb') as cover_file:
                    cover_file.write(front)
                    album.front = front
    except:
        traceback.print_exc()
        pretty_print(colorama.Fore.RED + 'couldn\'t find a front cover')

def get_album_track_list(artist, album):
    print(colorama.Fore.CYAN + '=============================================================================')
    a = find_closest_artist(artist)
    if not a:
        return
    artist.artist = a
    artist = artist.artist
    release = find_closest_release(artist, album)
    if not release:
        return
    download_cover_art(album, release)
    album.release = release
    find_tracks_in_recording(artist, album, release)
    album.fix_tags(artist)

if not __name__  == '__main__':
    musicbrainzngs.set_useragent(app = 'tagvaganza', version = '0.0.1')