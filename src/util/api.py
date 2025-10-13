#!/usr/bin/env python3
import requests # typing: ignore
from flask import Blueprint
from typing import List, Any
from src.models.word import Word, Phonetic, Meaning, Definition
from src.models.extensions import db
import sys
import logging

root = logging.getLogger("root")


def process_request(word: str) -> None:
    response = fetch_word(word)
    if not response:
        raise RuntimeWarning(f"No data found for the given word: {word}")
    new_word = parse_word(response)
    if new_word:
        db.session.add(new_word)
        db.session.commit()
    else:
        raise RuntimeWarning(f"The word: {word} already exists in the database")
    
'''
Helper function to get word from 
using API
'''
def fetch_word(word: str) -> List[Any]:
    response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if not response:
        return None    
    return response.json()

def parse_word(response: List[Any]) -> Word:
    # parse the response to get the word, phonetic, phonetics, meanings, definitions, synonyms, antonyms
    # return a Word object
    assert len(response) > 0, "No data found"
    word_to_update = Word.query.filter_by(word=response[0]['word']).first()
    root.info(word_to_update)
    if word_to_update:
        return None
    new_word = Word(id=None, word=response[0]['word'], phonetic=response[0]['phonetic'], phonetics=[], meanings=[])
    for item in response:
        for phonetic in item['phonetics']:
            phonetics_to_update = Phonetic.query.filter_by(phonetic=phonetic['text']).first()
            if not phonetics_to_update:
                new_word.phonetics.append(Phonetic(id=None, phonetic=phonetic['text'], audio_url=phonetic.get('audio', None), words=[new_word]))
            else:
                phonetics_to_update.words.append(new_word)
                new_word.phonetics.append(phonetics_to_update)
        for meaning in item['meanings']:
            new_meaning = Meaning(id=None, partOfSpeech=meaning['partOfSpeech'], 
                                  synonyms=meaning.get('synonyms', None), 
                                  antonyms=meaning.get('antonyms', None), 
                                  word=new_word, definitions=[], word_id=new_word.id)
            for definition in meaning['definitions']:
                new_meaning.definitions.append(
                    Definition(id=None, definition=definition['definition'], 
                               example=definition.get('example', None), 
                               synonyms=definition.get('synonyms', None), 
                               antonyms=definition.get('antonyms', None),
                               meaning=new_meaning, meaning_id=new_meaning.id))
            new_word.meanings.append(new_meaning)
    return new_word

'''
the main function is implemented so it can be run as a script in isolation
Usage: python api.py <word>
'''
if __name__ == "__main__":
    response = None
    if len(sys.argv) > 1:
        input_word = sys.argv[1]  # The first argument after the script name
        root.info(f"The word received is: {input_word}")
        process_request(input_word)
    else:
        root.error("No word was passed to the script.")
        sys.exit(1)