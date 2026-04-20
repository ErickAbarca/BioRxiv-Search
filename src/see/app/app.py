import os, json, time, logging
import spacy
import pika

nlp = spacy.load("en_core_web_lg")

output_dir = os.getenv("OUTPUT_DIR")
input_dir = os.getenv("INPUT_DIR")

RABBITMQ_HOST = os.environ.get('RABBITMQ')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

time.sleep(10)

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

def getDataFromDisk(message):
    """Carga datos desde el disco"""
    try:
        file_path = os.path.join(input_dir, f"{message['jobId']}_{message['splitNumber']}.json")
        with open(file_path, 'r') as f:
            data = json.load(f)
        logging.info("Data loaded from disk: %s", file_path)
        return data
    except Exception as e:
        logging.error("Error loading data from disk: %s", e)
        raise

def extractAuthors(rel_authors):
    author_pairs = []
    
    for author in rel_authors:
        name = author["author_name"]
        inst = author["author_inst"]
        sentence = f"{name} is affiliated with {inst}."
        doc = nlp(sentence)
        
        person = None
        org = None
        
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not person:
                person = ent.text
            elif ent.label_ == "ORG" and not org:
                org = ent.text

        if person and org:
            author_pairs.append({"author_name": person, "author_inst": org})
    
    return author_pairs

def extractDate(text):
    doc = nlp(text)
    entities = "x"
    for ent in doc.ents:
        if ent.label_ == 'DATE':
          entities= ent.text
    return entities

def extractEntities(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append(ent.text)
    return entities

def saveData (save,data):
    os.makedirs(output_dir, exist_ok=True)

    safe_doi = save["doi"].replace("/", "-")

    file_path = os.path.join(output_dir, f"{data['jobId']}_{data['splitNumber']}_{safe_doi}.json")

    with open(file_path, "w") as f: 
        json.dump(save, f)

    f.close()
    logging.info(f"data saved to {file_path}")




def handleMessage(ch, method, properties, body):
    """Maneja el mensaje recibido de RabbitMQ"""
    try:
        message = json.loads(body)
        logging.info("Received message: %s", message)
        
        data = getDataFromDisk(message)
        data[0]

        for item in data:
            saving = {
                "authors": extractAuthors(item['rel_authors']),
                "date" : extractDate(str(item['rel_date'])),
                "abstract" : str(item['rel_abs']),
                "link" : str(item['rel_link']),
                "title" : str(item['rel_title']),
                "doi" : str(item['rel_doi']),
                "category" : str(item['category']),
                "entities": extractEntities(str(item['rel_abs'])),
                "type": str(item['type'])
            }
            saveData(saving, message)
        
        logging.info("Message processed successfully")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error("Error processing message: %s", e)



if __name__ == "__main__":
    connection, channel = connect_to_rabbitmq(RABBITMQ_QUEUE)
    logging.info("Spacy model loaded")
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=handleMessage, auto_ack=False)
    logging.info("Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("Interrupted by user, stopping...")
    finally:
        channel.stop_consuming()
        connection.close()
        logging.info("Connection closed")
