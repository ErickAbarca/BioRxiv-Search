import json, os, logging, pika, requests, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

output_dir = os.getenv("OUTPUT_DIR")

RABBITMQ_HOST = os.environ.get('RABBITMQ')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE')
RABBITMQ_QUEUE_DST = os.environ.get('RABBITMQ_QUEUE_DST')



def saveData (save,data):
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{data['jobId']}_{data['splitNumber']}.json")
    with open(file_path, "w") as f: 
        json.dump(save, f)

    f.close()
    logging.info(f"data saved to {file_path}")

def dataBio(currentUrl):
    response = requests.get(currentUrl)
    logging.info("Request URL: %s", currentUrl)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error:", response.status_code)
        return None

def connect_to_rabbitmq(queue_name):
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
        channel.queue_declare(queue=queue_name, durable=True)
        
        logging.info("Connected to RabbitMQ on queue: %s", queue_name)
        return connection, channel
    except Exception as e:
        logging.error("Failed to connect to RabbitMQ: %s", e)
        raise

def messageRabbitmq(channel, message, queue_name):
    """Publica un mensaje en la cola de RabbitMQ"""
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        logging.info("Message sent to RabbitMQ: %s", message)
    except Exception as e:
        logging.error("Failed to send message to RabbitMQ: %s", e)
        raise


if __name__ == "__main__":
    connection, channel = connect_to_rabbitmq(RABBITMQ_QUEUE)
    connection_dst, channel_dst = connect_to_rabbitmq(RABBITMQ_QUEUE_DST)
    urlBio = os.environ.get('URL_BIO')
    currentSplit = 0

    def callback(ch, method, properties, body):
        global currentSplit
        global urlBio
        data = json.loads(body)
        logging.info("Current split: %s", currentSplit)
        time.sleep(data['sleep'])
        currentURL = urlBio+str(currentSplit*data['pageSize'])
        currentSplit += 1
        response = dataBio(currentURL)
        if response is None:
            logging.error("Failed to retrieve data from URL: %s", urlBio)
            return
        raw_data = response['collection'][:data['pageSize']]
        saveData(raw_data,data)
        formated_data = {
            "jobId": data['jobId'],
            "pageSize": data['pageSize'],
            "sleep": data['sleep'],
            "splitNumber": currentSplit-1,
            "status": "DOWNLOADED",
        }
        logging.info("Received message: %s", data)
        messageRabbitmq(channel_dst, json.dumps(formated_data), RABBITMQ_QUEUE_DST)


    time.sleep(20)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)
    logging.info('Waiting for messages. To exit press CTRL+C')
    currentSplit = 0
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info('Exiting...')
    finally:
        connection.close()
        connection_dst.close()