import os
import re
import json
import string
import functools
import traceback

from vaganza import(
    commons,
    capitalization
)

import colorama
import musicbrainzngs

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

def remove_non_ascii_characters(s):
    printable = set(string.printable) #removes non-ascii characters
    s = ''.join(filter(lambda x: x in printable, s))
    return s

def remove_whitespaces(s):
    s = re.sub('\s', '', s) #removes whitespaces
    return s

def remove_punctuation(s):
    s = re.sub(r'[^\w\s]','',s)
    return s

def remove_ambiguous_characters(s):
    return remove_non_ascii_characters(
                remove_whitespaces(
                    remove_punctuation(
                        s
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

def edit_distance(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
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

def find_minimum_cost_match(results, target, key):
    distance = {}
    for result in results:
        t = remove_ambiguous_characters(result[key])
        s = remove_ambiguous_characters(target)
        if is_subsequence(t, s):
            distance[result['id']] = edit_distance(target, result[key])
    if not distance:
        return None
    m = min(distance, key = distance.get)
    choice = list(filter(lambda x: x['id'] == m, results))[0]
    return choice

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
    pretty_print('searching for closest artist to', colorama.Fore.GREEN, artist.name)
    results = musicbrainzngs.search_artists(artist = artist.name)['artist-list']
    choice = find_minimum_cost_match(results, artist.name, 'name')
    if not choice:
        pretty_print(colorama.Fore.RED + 'couldn\'t find an artist with a matching name')
        return None
    pretty_print('matched against', colorama.Fore.GREEN, choice['name'])
    return choice

def find_closest_release(artist, album):
    pretty_print('searching for closest album to', green(album.title), white('with'), green(album.get_num_tracks()), white('tracks'))
    results = get_all_artist_releases(artist['id'])
    # 1. find all releases of this artist with a matching name
    choice = find_minimum_cost_match(results, album.title, 'title')
    if not choice:
        album.rename()
        pretty_print(colorama.Fore.RED + 'couldn\'t find a release with matching title')
        return None
    results = list(filter(lambda x: x['title'] == choice['title'], results))
    # 2. among these releases find the one whose number of tracks matches the one at hand
    choice = list(filter(lambda x: x['medium-track-count'] == album.get_num_tracks(), results))
    if choice:
        match = choice[0]
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
    # numbers = {}
    # for i in range(1, album.get_num_tracks() + 1):
    #     numbers[i] = True
    for disc in album.discs:
        for track in disc.tracks:
            choice = find_minimum_cost_match(results, track, 'title')
            if not choice:
                pretty_print('couldn\'t find a recording with a matching title for', red(track))
                    #white(', closest match: '), magenta(choice['title']))
                continue
            r = list(filter(lambda x: choice['release-list'][x]['id'] == release['id'],\
                range(len(choice['release-list']))))[0]
            r = choice['release-list'][r]
            r = r['medium-list'][0]['track-list'][0]['number']
            disc.tracks[track].recording = choice
            disc.tracks[track].number = r
            results.pop(results.index(choice))
            # try:
            #     numbers.pop(int(r), None)
            # except:
            #     pretty_print('number', magenta(r))
            pretty_print('matched', blue(track), white('to'), green(r + '.' , choice['title']))

def download_cover_art(album, release):
    try:
        # print(release['id'])
        front = musicbrainzngs.get_release_group_image_front(release['release-group']['id'])
        for disc in album.discs:
            try:
                os.remove(os.path.join(disc.dir, 'cover.jpg'))
                os.remove(os.path.join(disc.dir, 'Cover.jpg'))
            except:
                pass
            with open(os.path.join(disc.dir, 'Cover.jpg'), 'wb') as cover_file:
                cover_file.write(front)
                album.front = front
    except:
        pretty_print(colorama.Fore.RED + 'couldn\'t find a front cover')
        # traceback.print_exc()
        pass

def get_album_track_list(artist, album):
    print(colorama.Fore.CYAN + '=============================================================================')
    artist = find_closest_artist(artist)
    release = find_closest_release(artist, album)
    if not release:
        return
    download_cover_art(album, release)
    album.release = release
    find_tracks_in_recording(artist, album, release)
    album.fix_tags(artist)

if not __name__  == '__main__':
    musicbrainzngs.set_useragent(app = 'tagvaganza', version = '0.0.1')