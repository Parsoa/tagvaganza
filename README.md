# What does this do?

I'm an audiophile, or at least I'm trying to be one. But one thing that I sure as hell am is a very obsessive person (OCD and stuff). I keep a huge and ever-expanding library of songs and I want all of them to have clean and correct id3 tags, filenames and more important than all, high-resolution cover arts. This codebase tries to help me (or you, if you share my concerns about your own library) achieve that.

# The problem we are trying to solve

*tagvaganza* makes a number of assumptions about the data fed into it. It is rather simple:

1. Music needs to have a hiearchial structure. What does this mean? There is a folder for each artist inside which there are a number of folders for each of the releases you have and inside those folders could either be a set of folders corresponding to discs/volumes. Finally there are audio files themselves (mp3, ALAC, FLAC).

2. File and folder should somehow resemble the correct values they are supposed to have. So lets say you have a folder for the artist `Procupine Tree`. This folder could be named `Porcupine Tree discography 2001 - 2008`, `PorcupineTree`, `PORCUPINEtree`, `Porcufickingpinetree`, `procupine_tree`. It has to somewhat include the correct name of the artists. Downloads or ripped CDs usually adhere to that. The names might be ugly but they include the correct name of the artist (capitalization doesn't matter). Same shold apply to album folders and audio files. This might sound much but it is pretty much guaranteed no matter how you get those files. This script is probably of no use to you if your current files lack this minimal structure.

# How to use it?

* Clone this repository
* `pip install -r requirments.txt`
* `cd src`
* python -m vaganza --path <Where your library is>