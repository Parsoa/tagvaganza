# What does this do?

I might be an audiophile, or at least I like the idea of caring a lot about the sound you hear. But one thing that I sure as hell am is a very obsessive person (OCD and stuff). I keep a huge and ever-expanding library of songs and I want all of them to have clean and correct id3 tags and filenames and most importantly high-resolution cover arts. This codebase tries to help me (or you, if we share similar concerns) achieve that. This is a process that cannot be fully automated anyway, but *tagvaganza* tries to handle much of the dirt work regarding the naming and tagging of files. *Tagvaganza* currently retrievs the needed metadata from the musicbrainz database. It is a reliable source for most stuff but when it comes to cover arts the offering is lackluster; you can usually find covers of much higher quality and resolution on Google. I have plans to fix that as well but the code is currently limited to what musicbrainz has to offer.

# How does it do so?

*tagvaganza* makes a number of assumptions about the data fed into it. It is rather simple:

1. Music needs to have a hiearchial structure. What does this mean? There is a folder for each artist inside which there are a number of folders for each of the releases you have and inside those folders could be a set of folders corresponding to discs/volumes. Finally, at the bottom level, there are the audio files themselves (mp3, ALAC, FLAC).

2. File and folder names should somehow resemble the correct values they are supposed to have. So lets say you have a folder for the artist `Procupine Tree`. This folder could be named `Porcupine Tree discography 2001 - 2008`, `PorcupineTree`, `PORCUPINEtree`, `Porcuf*ckingpinetree`, `procupine_tree`. You get the idea. It has to somewhat include the correct name of the thing it is representing. Downloads or ripped CDs usually satisfy this requirement, the names might be ugly but they more or less include what they are expected to. Same should apply to album folders and audio files. This might sound like a deal-breaker but it is pretty much guaranteed unless you have fetched your files from a paranoid android who relies on hash functions and pseudo-random uuids to organize his stuff. This script is probably of no interest to you if your files lack this minimal structure.

*tagvaganza* does its magic through a couple of heuristics and some fundamental string processing algorithms. It should be able to devour whatever you throw at it provided the structure requirements are satisfied. It may sometimes fail to tag certain songs in a release, but will fill up as much information as possible.

# How do I use it?

* Clone this repository
* `pip install -r requirments.txt`
* `cd src`
* python -m vaganza --path <Where your library is>