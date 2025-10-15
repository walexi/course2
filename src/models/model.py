#!/usr/bin/env python3
from flask import Flask
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, List
from src.models.extensions import Base, db
from sqlalchemy.types import TypeDecorator, Text
import json
from dataclasses import dataclass


class StringListType(TypeDecorator):
    impl = Text  # Store as TEXT in the database
    cache_ok = True
    def process_bind_param(self, value: List[str], dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value: str, dialect):
        if value is not None:
            return json.loads(value)
        return None

'''
A word can have multiple phonetics and same phonetics can be shared by multiple words (Homophones)
so it's a many-to-many relationship
'''
word_phonetic_assoociation = db.Table(
    'word_phonetic_association',
    Base.metadata,
    db.Column('word_id', db.Integer, db.ForeignKey('word.id')),
    db.Column('phonetic_id', db.Integer, db.ForeignKey('phonetic.id'))
)

class Word(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # each word in the dictionary is unique, length of longest word in english dictionary is 45
    word: Mapped[str] = mapped_column(db.String(45), unique=True)
    phonetic: Mapped[str] = mapped_column() # the phonetic representation can be empty, the primary phonetic representation
    phonetics: Mapped[Optional[List["Phonetic"]]] = db.relationship("Phonetic", secondary='word_phonetic_association', back_populates="words", cascade="all, delete")
    meanings: Mapped[Optional[List["Meaning"]]] = db.relationship("Meaning", back_populates="word", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Word(id={self.id!r}, word={self.word!r}, phonetic={self.phonetic!r})"
    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'phonetic': self.phonetic,
            'phonetics': [phonetic.to_dict() for phonetic in self.phonetics],
            'meanings': [meaning.to_dict() for meaning in self.meanings]
        }

class Phonetic(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phonetic: Mapped[str] = mapped_column()
    audio_url: Mapped[Optional[str]] = mapped_column(nullable=True) # the url to the audio file can be empty
    words: Mapped[Optional[List["Word"]]] = db.relationship("Word", secondary='word_phonetic_association', back_populates="phonetics", cascade="all, delete")

    def to_dict(self):
        return {
            'id': self.id,
            'phonetic': self.phonetic,
            'audio_url': self.audio_url
        }
    

class Meaning(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    partOfSpeech: Mapped[str] = mapped_column(db.String(30))
    definitions: Mapped[List["Definition"]] = db.relationship("Definition", back_populates="meaning", cascade="all, delete-orphan")
    # the synonyms and antonyms are stored as lists of strings for easy access, rather than referencing other words in the dictionary
    synonyms: Mapped[Optional[List[str]]] = mapped_column(StringListType, nullable=True)
    antonyms: Mapped[Optional[List[str]]] = mapped_column(StringListType, nullable=True)
    word_id: Mapped[int] = mapped_column(db.ForeignKey('word.id'))
    word: Mapped["Word"] = db.relationship(back_populates="meanings")

    def to_dict(self):
        return {
            'id': self.id,
            'partOfSpeech': self.partOfSpeech,
            'synonyms': self.synonyms,
            'antonyms': self.antonyms,
            'definitions': [definition.to_dict() for definition in self.definitions]
        }

class Definition(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    definition: Mapped[str] = mapped_column()
    example: Mapped[Optional[str]] = mapped_column(nullable=True)
    synonyms: Mapped[Optional[List[str]]] = mapped_column(StringListType, nullable=True)
    antonyms: Mapped[Optional[List[str]]] = mapped_column(StringListType, nullable=True)
    meaning_id: Mapped[int] = mapped_column(db.ForeignKey('meaning.id'))
    meaning: Mapped["Meaning"] = db.relationship(back_populates="definitions")

    def to_dict(self):
        return {
            'id': self.id,
            'definition': self.definition,
            'example': self.example,
            'synonyms': self.synonyms,
            'antonyms': self.antonyms
        }