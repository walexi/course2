from src.models.model import Word, Phonetic, Meaning, Definition
from src.models.extensions import db


def test_new_word():
    """
    GIVEN a Word model
    WHEN a new Word is created
    THEN check the word and phonetic fields are defined correctly
    """
    word = Word(id=None, word='example', phonetic='/ɪɡˈzɑːmpəl/', phonetics=[], meanings=[])
    assert word.word == 'example'
    assert word.phonetic == '/ɪɡˈzɑːmpəl/'

def test_new_phonetic():
    """
    GIVEN a Phonetic model
    WHEN a new Phonetic is created
    THEN check the phonetic and audio_url fields are defined correctly
    """
    phonetic = Phonetic(id=None, phonetic='/ɪɡˈzɑːmpəl/', audio_url='http://example.com/audio.mp3', words=[])
    assert phonetic.phonetic == '/ɪɡˈzɑːmpəl/'
    assert phonetic.audio_url == 'http://example.com/audio.mp3'


def test_new_meaning():
    """
    GIVEN a Meaning model
    WHEN a new Meaning is created
    THEN check the partOfSpeech, synonyms, and antonyms fields are defined correctly
    """
    meaning = Meaning(id=None, partOfSpeech='noun', definitions=[], synonyms=['instance', 'case'], antonyms=['counterexample'], word_id=1, word=None)
    assert meaning.partOfSpeech == 'noun'
    assert meaning.synonyms == ['instance', 'case']
    assert meaning.antonyms == ['counterexample']

def test_new_definition():
    """
    GIVEN a Definition model
    WHEN a new Definition is created
    THEN check the definition field is defined correctly
    """
    definition = Definition(id=None, definition='A thing characteristic of its kind or illustrating a general rule.',
                             meaning=None, meaning_id=None, example=None,
                             synonyms=None, antonyms=None)
    assert definition.definition == 'A thing characteristic of its kind or illustrating a general rule.'