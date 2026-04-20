import requests, logging, os, pika, time, json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

numDocs = 0

urlMongo = os.environ.get('MONGO_STR')
urlBio = os.environ.get('URL_BIO')

RABBITMQ_HOST = os.environ.get('RABBITMQ')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE')

def connMongo():
    client = MongoClient(urlMongo, server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        logging.info("MongoDB connection successful.")
        return client
    except Exception as e:
        logging.error("MongoDB connection failed: %s", e)
        return None

def connect_to_rabbitmq():
    """Establece conexión con RabbitMQ y retorna canal"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            credentials=credentials,
            heartbeat=600
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declarar la cola para asegurar que existe
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        logging.info("Connected to RabbitMQ")
        return connection, channel
    except Exception as e:
        logging.error("Failed to connect to RabbitMQ: %s", e)
        raise


def dataBio():
    response = requests.get(urlBio)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error:", response.status_code)
        return None
    
def retrieveData():
    client = connMongo()
    docs = []
    if client:
        db = client["prueba_proyecto"]
        collection = db["jobs"]
        documents = collection.find()
        for doc in documents:
            docs.append(doc)
        client.close()
        return docs[-1:]  
    else:
        logging.error("Failed to connect to MongoDB.")

def messageRabbitmq(channel, message):
    """Publica un mensaje en la cola de RabbitMQ"""
    try:
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        logging.info("Message sent to RabbitMQ: %s", message)
    except Exception as e:
        logging.error("Failed to send message to RabbitMQ: %s", e)
        raise
    
def main():
    docs=retrieveData()
    global numDocs
    if len(docs) == numDocs:
        logging.info("No new documents to process.")
        return
    numDocs = len(docs)
    data = dataBio()
    total = data['messages'][0]['total']
    pS = docs[0]['pageSize']
    jobId = docs[0]['jobId']
    sleep = docs[0]['sleep']

    splits = total // pS
    connection, channel = connect_to_rabbitmq()
    for i in range(splits):
        message = {
            'jobId': jobId,
            'pageSize': pS,
            'sleep': sleep,
            'splitNumber': i
        }
        messageRabbitmq(channel, json.dumps(message))

    channel.close()
    connection.close()        
    logging.info("RabbitMQ connection closed, Number of splits: %d", splits)



if __name__ == "__main__":
    while True:
        main()
        logging.info("Waiting for 24 hours...")
        time.sleep(86400)  
    