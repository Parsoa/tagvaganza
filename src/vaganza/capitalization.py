import re

punctuations = ['.', ':', '-', ',', ';']

coordinating_conjunctions = ['and', 'but', 'or', 'nor', 'for', 'yet', 'and', 'so']

short_prepositions = ['as', 'at', 'by', 'for', 'in', 'of', 'on', 'to', 'from']

articles = ['a', 'an', 'the']

class Chunk(object):
    def __init__(self, content, delimiter):
        print('chunk: |', content, '|', delimiter, '|', sep="")
        self.content = content
        self.delimiter = delimiter

def capitalize_string(path):
    print(path)
    song = taglib.File(path)
    print('2')
    print(song.tags)
    # all uppercase would be easier
    a = 'a'
    b = 'b'
    c = a + b
    print(c)
    string = string.upper() + ' '
    # break into multiple parts
    chunks = []
    l = len(string)
    for j in range(0, l):
        # print('#', string, '#', sep="")
        for i in range(0, len(string)):
            found = False
            for punctuation in punctuations:
                if string[i] == punctuation:
                    chunks.append(Chunk(string[0:i], punctuation))
                    string = string[i + 1:]
                    found = True
                    break
            if found:
                break
    chunks.append(Chunk(string, ''))
    result = ''
    for chunk in chunks:
        result = result + capitalize_chunk(chunk.content.strip()) + chunk.delimiter 
    print('result: ', result, sep="")

def capitalize_chunk(track):

    # we can safely assume that no chunk would begin with a space
    words = re.split(r'\s+', string)
    for i in range(0, len(words)):
        word = words[i]
        word = word[0] + word[1:].lower()
        words[i] = word
    print(words)
    for i in range(0, len(words)):
        word = words[i]
        for conjunction in coordinating_conjunctions:
            if conjunction.upper() == word.upper():
                word = conjunction
        for preposition in short_prepositions:
            if preposition.upper() == word.upper():
                word = preposition
        for article in articles:
            if article.upper() == word.upper():
                word = article
        words[i] = word
    result = ''
    for word in words:
        result = result + word + ' '
    # get rid of the final space
    return result[:-1]
