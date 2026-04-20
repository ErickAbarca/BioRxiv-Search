import unittest
from unittest.mock import patch, MagicMock
import json

import app

class TestHandleMessage(unittest.TestCase):
    @patch('app.spacy.load')
    @patch('app.extractEntities')
    @patch('app.extractDate')
    @patch('app.extractAuthors')
    @patch('app.saveData')
    @patch('app.getDataFromDisk')
    def test_handle_message_success(self, mock_getDataFromDisk, mock_saveData, mock_extractAuthors, mock_extractDate, mock_extractEntities, mock_spacy_load):
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp
        app.nlp = mock_nlp 

        fake_message = {
            "jobId": "testjob",
            "splitNumber": "001"
        }
        fake_body = json.dumps(fake_message)

        fake_data = [{
            "rel_authors": [{"author_name": "John Doe", "author_inst": "MIT"}],
            "rel_date": "2023-01-01",
            "rel_abs": "This paper discusses artificial intelligence.",
            "rel_link": "http://example.com",
            "rel_title": "AI Research",
            "rel_doi": "10.1234/ai.paper",
            "category": "AI",
            "type": "research"
        }]
        mock_getDataFromDisk.return_value = fake_data
        mock_extractAuthors.return_value = [{"author_name": "John Doe", "author_inst": "MIT"}]
        mock_extractDate.return_value = "2023"
        mock_extractEntities.return_value = ["artificial intelligence"]

        # Mock del canal y método
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 'abc'

        # Ejecutar
        app.handleMessage(mock_ch, mock_method, None, fake_body.encode('utf-8'))

        # Verificar
        mock_ch.basic_ack.assert_called_once_with(delivery_tag='abc')
        mock_saveData.assert_called_once()
        mock_extractAuthors.assert_called_once()
        mock_extractDate.assert_called_once()
        mock_extractEntities.assert_called_once()

if __name__ == '__main__':
    unittest.main()
