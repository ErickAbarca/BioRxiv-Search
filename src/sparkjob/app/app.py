import logging, os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, to_date, trim, initcap, explode, struct, collect_list
from pyspark.sql.types import StringType, ArrayType
from datetime import datetime
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SparkProcessorJob")

#UDF necesarios para el procesamiento de datos
def format_author_name(name):
    if name is None:
        return None
    parts = name.strip().split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else name

def split_institution(inst):
    if inst is None:
        return []
    return [x.strip() for x in inst.split(",")]

def format_date(date_str):
    try:
        return datetime.strptime(date_str.replace("'", ""), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception as e:
        logger.warning(f"Fecha inválida: '{date_str}' – {e}")
        return None

# Inicializar Spark
logger.info("SparkSession...")
spark = SparkSession.builder \
    .appName("SparkProcessorJob") \
    .getOrCreate()

# Registrar UDFs
logger.info("Registrando funciones UDF...")
format_author_udf = udf(format_author_name, StringType())
split_inst_udf = udf(split_institution, ArrayType(StringType()))
format_date_udf = udf(format_date, StringType())

# Leer archivos JSON
INPUT_DIR = os.getenv("INPUT_DIR")
logger.info(f"Leyendo archivos desde {INPUT_DIR}...")
df = spark.read.json(INPUT_DIR)

# Aplicar formatos
logger.info("Aplicando Formatos")
df = df.withColumn("rel_date", format_date_udf("date"))
df = df.withColumn("category", initcap(trim(col("category"))))

authors_df = df.select(
    col("title"), col("abstract"), col("link"), col("doi"),
    col("category"), col("rel_date"), col("entities"), col("type"),
    explode("authors").alias("author")
).withColumn(
    "author_name", format_author_udf(col("author.author_name"))
).withColumn(
    "author_inst", split_inst_udf(col("author.author_inst"))
).drop("author")

# Agrupar por artículo
final_df = authors_df.groupBy("title", "abstract", "link", "doi", "category", "rel_date", "entities", "type") \
    .agg(collect_list(struct("author_name", "author_inst")).alias("authors"))

# Convertir a JSON y recolectar
logger.info("Convirtiendo a JSON y recolectando documentos...")
documents = final_df.toJSON().map(lambda j: eval(j)).collect()

# Conexión a MongoDB
MONGO_URI = os.getenv("MONGO_STR")
if not MONGO_URI:
    logger.error("No se encontró la variable de entorno 'MONGO_STR'. Terminando proceso.")
    exit(1)

logger.info("Conectando a MongoDB Atlas...")
client = MongoClient(MONGO_URI)
collection = client["prueba_proyecto"]["documents"]

if documents:
    logger.info(f"Procesando {len(documents)} documentos para MongoDB...")
    for doc in documents:
        try:
            #sobreescribir o insertar el documento
            result = collection.replace_one(
                {"doi": doc["doi"]},  # Criterio de búsqueda
                doc,                  # Doc
                upsert=True           # Inserta si no existe, reemplaza si existe
            )
            if result.matched_count > 0:
                logger.info(f"Documento con doi {doc['doi']} actualizado.")
            else:
                logger.info(f"Documento con doi {doc['doi']} insertado.")
        except Exception as e:
            logger.error(f"Error al procesar documento con doi {doc.get('doi', 'desconocido')}: {e}")
else:
    logger.warning("No se encontraron documentos para insertar.")
