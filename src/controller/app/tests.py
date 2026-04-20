import unittest
from unittest.mock import patch, MagicMock
import app


class TestMainScript(unittest.TestCase):

    @patch('app.MongoClient')
    def test_connMongo_success(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {"ok": 1}
        
        client = app.connMongo()
        self.assertIsNotNone(client)
        mock_instance.admin.command.assert_called_once_with('ping')

    @patch('app.requests.get')
    def test_dataBio_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"total": 100}]}
        mock_get.return_value = mock_response

        data = app.dataBio()
        self.assertIsNotNone(data)
        self.assertIn("messages", data)
        self.assertEqual(data["messages"][0]["total"], 100)

    @patch('app.MongoClient')
    def test_retrieveData_returns_docs(self, mock_client):
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find.return_value = [{"jobId": 123, "pageSize": 10, "sleep": 5}]
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_client.return_value.admin.command.return_value = {"ok": 1}

        result = app.retrieveData()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["jobId"], 123)

    @patch('app.pika.BlockingConnection')
    def test_connect_to_rabbitmq_success(self, mock_connection):
        mock_channel = MagicMock()
        mock_conn_instance = MagicMock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_connection.return_value = mock_conn_instance

        connection, channel = app.connect_to_rabbitmq()
        self.assertIsNotNone(connection)
        self.assertIsNotNone(channel)
        mock_channel.queue_declare.assert_called_once()

    @patch('app.messageRabbitmq')
    @patch('app.connect_to_rabbitmq')
    @patch('app.dataBio')
    @patch('app.retrieveData')
    def test_main_generates_messages(
        self, mock_retrieve, mock_data, mock_connect, mock_send_msg
    ):
        mock_retrieve.return_value = [{
            "jobId": "abc123",
            "pageSize": 10,
            "sleep": 0
        }]
        mock_data.return_value = {"messages": [{"total": 100}]}
        mock_channel = MagicMock()
        mock_connection = MagicMock()
        mock_connect.return_value = (mock_connection, mock_channel)

        app.numDocs = 0
        app.main()

        self.assertEqual(mock_send_msg.call_count, 10)
        mock_channel.close.assert_called_once()
        mock_connection.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
