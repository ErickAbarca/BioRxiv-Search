import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
from app import saveData, dataBio, connect_to_rabbitmq, messageRabbitmq

class TestMainScript(unittest.TestCase):

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_data_creates_file(self, mock_open_func, mock_makedirs):
        test_data = {"jobId": "test123", "splitNumber": 1}
        output_data = [{"dummy": "value"}]

        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp/test_output"}):
            global output_dir
            output_dir = os.getenv("OUTPUT_DIR")
            saveData(output_data, test_data)

        mock_makedirs.assert_called_once_with("/tmp/test_output", exist_ok=True)
        mock_open_func.assert_called_once_with("/tmp/test_output/test123_1.json", "w")
        mock_open_func().write.assert_called()

    @patch("requests.get")
    def test_data_bio_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"collection": [{"id": 1}]}
        mock_get.return_value = mock_response

        url = "http://example.com"
        result = dataBio(url)
        self.assertIsInstance(result, dict)
        self.assertIn("collection", result)

    @patch("requests.get")
    def test_data_bio_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "http://invalid-url.com"
        result = dataBio(url)
        self.assertIsNone(result)

    @patch("pika.BlockingConnection")
    def test_connect_to_rabbitmq_success(self, mock_blocking_connection):
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_blocking_connection.return_value = mock_conn

        with patch.dict(os.environ, {
            "RABBITMQ": "localhost",
            "RABBITMQ_USER": "user",
            "RABBITMQ_PASS": "pass"
        }):
            global RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
            RABBITMQ_HOST = os.getenv('RABBITMQ')
            RABBITMQ_USER = os.getenv('RABBITMQ_USER')
            RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')

            conn, channel = connect_to_rabbitmq("test_queue")
            self.assertIsNotNone(conn)
            self.assertIsNotNone(channel)

    def test_message_rabbitmq_success(self):
        mock_channel = MagicMock()
        message = json.dumps({"status": "test"})

        try:
            messageRabbitmq(mock_channel, message, "test_queue")
        except Exception:
            self.fail("messageRabbitmq raised Exception unexpectedly!")

if __name__ == '__main__':
    unittest.main()
