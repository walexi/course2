"""
Integration tests for the word API processing module.
Tests the entire flow from API calls to database storage.
"""

import pytest
import requests
from unittest.mock import patch, Mock, MagicMock
import logging
from src.util.api import process_request, fetch_word, parse_word
from src.models.model import Word, Phonetic, Meaning, Definition
from src.models.extensions import db


class TestWordProcessorIntegration:
    """Integration tests for word processing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database for each test"""
        with app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def sample_api_response(self):
        """Sample response from dictionary API"""
        return [
            {
                "word": "hello",
                "phonetic": "/həˈloʊ/",
                "phonetics": [
                    {
                        "text": "/həˈloʊ/",
                        "audio": "https://api.dictionaryapi.dev/media/pronunciations/en/hello-us.mp3"
                    },
                    {
                        "text": "/hɛˈloʊ/"
                    }
                ],
                "meanings": [
                    {
                        "partOfSpeech": "exclamation",
                        "synonyms": ["hi", "hey"],
                        "antonyms": ["goodbye"],
                        "definitions": [
                            {
                                "definition": "Used as a greeting or to begin a phone conversation.",
                                "example": "hello there, Katie!",
                                "synonyms": ["hi"],
                                "antonyms": []
                            }
                        ]
                    },
                    {
                        "partOfSpeech": "noun",
                        "synonyms": [],
                        "antonyms": [],
                        "definitions": [
                            {
                                "definition": "An utterance of 'hello'; a greeting.",
                                "example": "she was getting polite nods and hellos from people",
                                "synonyms": [],
                                "antonyms": []
                            }
                        ]
                    }
                ]
            }
        ]
    
    @pytest.fixture
    def minimal_api_response(self):
        """Minimal valid API response"""
        return [
            {
                "word": "test",
                "phonetic": "/test/",
                "phonetics": [],
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {
                                "definition": "A test definition"
                            }
                        ]
                    }
                ]
            }
        ]

    # Test fetch_word function
    
    def test_fetch_word_success(self, app, sample_api_response):
        """Test successful API call"""
        with app.app_context():
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = sample_api_response
                mock_response.__bool__ = lambda x: True  # Make response truthy
                mock_get.return_value = mock_response
                
                result = fetch_word("hello")
                
                mock_get.assert_called_once_with(
                    "https://api.dictionaryapi.dev/api/v2/entries/en/hello"
                )
                assert result == sample_api_response
    
    def test_fetch_word_api_failure(self, app):
        """Test API call failure"""
        with app.app_context():
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.__bool__ = lambda x: False  # Make response falsy
                mock_get.return_value = mock_response
                
                result = fetch_word("nonexistentword")
                
                assert result is None
    
    def test_fetch_word_network_error(self, app):
        """Test network error during API call"""
        with app.app_context():
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException("Network error")
                
                with pytest.raises(requests.exceptions.RequestException):
                    fetch_word("hello")

    # Test parse_word function
    
    def test_parse_word_new_word(self, app, sample_api_response):
        """Test parsing and storing a new word"""
        with app.app_context():
            result = parse_word(sample_api_response)
            
            assert isinstance(result, Word)
            assert result.word == "hello"
            assert result.phonetic == "/həˈloʊ/"
            assert len(result.phonetics) == 2
            assert len(result.meanings) == 2
            
            # Check phonetics
            phonetic_texts = [p.phonetic for p in result.phonetics]
            assert "/həˈloʊ/" in phonetic_texts
            assert "/hɛˈloʊ/" in phonetic_texts
            
            # Check meanings
            parts_of_speech = [m.partOfSpeech for m in result.meanings]
            assert "exclamation" in parts_of_speech
            assert "noun" in parts_of_speech
            
            # Check definitions
            exclamation_meaning = next(m for m in result.meanings if m.partOfSpeech == "exclamation")
            assert len(exclamation_meaning.definitions) == 1
            assert "Used as a greeting" in exclamation_meaning.definitions[0].definition
            
            # Verify data was saved to database
            saved_word = Word.query.filter_by(word="hello").first()
            assert saved_word is not None
            assert saved_word.word == "hello"
    
    def test_parse_word_existing_word(self, app, sample_api_response):
        """Test parsing when word already exists in database"""
        with app.app_context():
            # First, create the word
            first_result = parse_word(sample_api_response)
            first_id = first_result.id
            
            # Try to parse the same word again
            second_result = parse_word(sample_api_response)
            
            assert second_result.id == first_id
            assert second_result.word == "hello"
            
            # Verify only one word exists in database
            word_count = Word.query.filter_by(word="hello").count()
            assert word_count == 1
    
    def test_parse_word_minimal_response(self, app, minimal_api_response):
        """Test parsing with minimal valid response"""
        with app.app_context():
            result = parse_word(minimal_api_response)
            
            assert isinstance(result, Word)
            assert result.word == "test"
            assert result.phonetic == "/test/"
            assert len(result.phonetics) == 0  # No phonetics in minimal response
            assert len(result.meanings) == 1
            
            # Check the single meaning
            meaning = result.meanings[0]
            assert meaning.partOfSpeech == "noun"
            assert len(meaning.definitions) == 1
            assert meaning.definitions[0].definition == "A test definition"

    # Test process_request function (end-to-end)
    
    def test_process_request_success(self, app, sample_api_response):
        """Test successful end-to-end word processing"""
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                mock_fetch.return_value = sample_api_response
                
                result = process_request("hello")
                
                mock_fetch.assert_called_once_with("hello")
                assert isinstance(result, Word)
                assert result.word == "hello"
                
                # Verify word was saved to database
                saved_word = Word.query.filter_by(word="hello").first()
                assert saved_word is not None
    
    def test_process_request_api_failure(self, app):
        """Test process_request when API returns no data"""
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                mock_fetch.return_value = None
                
                with pytest.raises(RuntimeWarning, match="No data found for the given word: nonexistent"):
                    process_request("nonexistent")
    
    def test_process_request_database_error(self, app, sample_api_response):
        """Test process_request when database operation fails"""
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                with patch.object(db.session, 'commit') as mock_commit:
                    mock_fetch.return_value = sample_api_response
                    mock_commit.side_effect = Exception("Database error")
                    
                    with pytest.raises(Exception, match="Database error"):
                        process_request("hello")

    # Test complex scenarios
    
    def test_process_multiple_words_with_shared_phonetics(self, app):
        """Test processing multiple words that share phonetic representations"""
        word1_response = [
            {
                "word": "read",
                "phonetic": "/riːd/",
                "phonetics": [{"text": "/riːd/", "audio": "audio1.mp3"}],
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [{"definition": "Look at and comprehend"}]
                    }
                ]
            }
        ]
        
        word2_response = [
            {
                "word": "reed",
                "phonetic": "/riːd/",
                "phonetics": [{"text": "/riːd/", "audio": "audio2.mp3"}],
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [{"definition": "A tall, slender-leaved plant"}]
                    }
                ]
            }
        ]
        
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                # Process first word
                mock_fetch.return_value = word1_response
                word1 = process_request("read")
                
                # Process second word with same phonetic
                mock_fetch.return_value = word2_response
                word2 = process_request("reed")
                
                # Both words should exist
                assert word1.word == "read"
                assert word2.word == "reed"
                
                # They should share the same phonetic object
                phonetic1 = word1.phonetics[0]
                phonetic2 = word2.phonetics[0]
                assert phonetic1.id == phonetic2.id
                assert phonetic1.phonetic == "/riːd/"
                
                # Verify both words are associated with the phonetic
                shared_phonetic = Phonetic.query.filter_by(phonetic="/riːd/").first()
                assert len(shared_phonetic.words) == 2
    
    def test_process_word_with_multiple_meanings_same_part_of_speech(self, app):
        """Test word with multiple meanings for the same part of speech"""
        response = [
            {
                "word": "bank",
                "phonetic": "/bæŋk/",
                "phonetics": [{"text": "/bæŋk/"}],
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "A financial institution"},
                            {"definition": "The land alongside a river"}
                        ]
                    }
                ]
            }
        ]
        
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                mock_fetch.return_value = response
                
                result = process_request("bank")
                
                assert len(result.meanings) == 1
                meaning = result.meanings[0]
                assert meaning.partOfSpeech == "noun"
                assert len(meaning.definitions) == 2
                
                definitions = [d.definition for d in meaning.definitions]
                assert "A financial institution" in definitions
                assert "The land alongside a river" in definitions

    # Test edge cases
    
    def test_process_word_empty_phonetics_list(self, app):
        """Test processing word with empty phonetics list"""
        response = [
            {
                "word": "test",
                "phonetic": "/test/",
                "phonetics": [],  # Empty phonetics list
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [{"definition": "A test"}]
                    }
                ]
            }
        ]
        
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                mock_fetch.return_value = response
                
                result = process_request("test")
                
                assert result.word == "test"
                assert len(result.phonetics) == 0
    
    def test_process_word_malformed_response(self, app):
        """Test processing malformed API response"""
        malformed_response = [
            {
                "word": "test",
                # Missing required fields
            }
        ]
        
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                mock_fetch.return_value = malformed_response
                
                with pytest.raises(KeyError):
                    process_request("test")


# Performance and stress tests
class TestWordProcessorPerformance:
    """Performance tests for word processing"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database"""
        with app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()
    
    def test_process_multiple_words_batch(self, app):
        """Test processing multiple words in batch"""
        words_responses = {
            "hello": [{"word": "hello", "phonetic": "/həˈloʊ/", "phonetics": [], "meanings": [{"partOfSpeech": "exclamation", "definitions": [{"definition": "A greeting"}]}]}],
            "world": [{"word": "world", "phonetic": "/wɜːrld/", "phonetics": [], "meanings": [{"partOfSpeech": "noun", "definitions": [{"definition": "The earth"}]}]}],
            "test": [{"word": "test", "phonetic": "/test/", "phonetics": [], "meanings": [{"partOfSpeech": "noun", "definitions": [{"definition": "An examination"}]}]}]
        }
        
        with app.app_context():
            with patch('src.util.api.fetch_word') as mock_fetch:
                def side_effect(word):
                    return words_responses.get(word)
                
                mock_fetch.side_effect = side_effect
                
                results = []
                for word in words_responses.keys():
                    result = process_request(word)
                    results.append(result)
                
                assert len(results) == 3
                assert all(isinstance(r, Word) for r in results)
                
                # Verify all words are in database
                saved_words = Word.query.all()
                assert len(saved_words) == 3

# Generated with the help of Cursor
# Run tests with:
"""
# Install required packages
pip install pytest pytest-mock pytest-cov

# Run all tests
pytest tests/test_word_processor_integration.py -v

# Run with coverage
pytest tests/test_word_processor_integration.py --cov=src.util.api --cov-report=html

# Run specific test class
pytest tests/test_word_processor_integration.py::TestWordProcessorIntegration -v

# Run specific test
pytest tests/test_word_processor_integration.py::TestWordProcessorIntegration::test_process_request_success -v
"""