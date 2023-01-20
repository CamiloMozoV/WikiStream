from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StringType, 
    StructField,
    StructType,
    BooleanType,
    IntegerType,
    LongType
)
from pyspark.sql.functions import (
    from_json
)

def read_kafka_stream(spark_session: SparkSession) -> DataFrame:
    """Read the kafka topic `wikistream`."""
    df_raw = spark_session.readStream\
                         .format("kafka")\
                         .option("kafka.bootstrap.servers", "kafka:9092")\
                         .option("subscribe", "wikistream")\
                         .load()
    # The key and value [both binary] received by the kafka topic are converted to string
    df_raw = df_raw.withColumn("key", df_raw["key"].cast(StringType()))\
                    .withColumn("value", df_raw["value"].cast(StringType()))
    
    return df_raw

def data_schema_stream(df: DataFrame) -> DataFrame:
    # Event data Schema
    schema = StructType([
        StructField("$schema", StringType(), True),
        StructField("bot", BooleanType(), True),
        StructField("comment", StringType(), True),
        StructField("id", StringType(), True),
        StructField("length", StructType([ 
                                            StructField("new", IntegerType(), True),
                                            StructField("old", IntegerType(), True)
                                        ]), True),
        StructField("meta", StructType([
                                            StructField("domain", StringType(), True),
                                            StructField("dt", StringType(), True),
                                            StructField("id", StringType(), True),
                                            StructField("offset", LongType(), True),
                                            StructField("partition", LongType(), True),
                                            StructField("request_id", StringType(), True),
                                            StructField("stream", StringType(), True),
                                            StructField("topic", StringType(), True),
                                            StructField("uri", StringType(), True),
                                       ]), True),
        StructField("minor", BooleanType(), True),
        StructField("namespace", IntegerType(), True),
        StructField("parsedcomment", StringType(), True),
        StructField("patrolled", BooleanType(), True),
        StructField("revision", StructType([
                                            StructField("new", IntegerType(), True),
                                            StructField("old", IntegerType(), True)
                                        ]), True),
        StructField("server_name", StringType(), True),
        StructField("server_script_path", StringType(), True),
        StructField("server_url", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("title", StringType(), True),
        StructField("type", StringType(), True),
        StructField("user", StringType(), True),
        StructField("wiki", StringType(), True)
    ])
    
    # Create DataFrame setting schema for event data
    df_wikiStream = df.withColumn("value", from_json("value", schema))
    return df_wikiStream

def kafka_spark_consumer(spark_session: SparkSession) -> None:
    df_raw = read_kafka_stream(spark_session)
    df_wikiStream = data_schema_stream(df_raw)
    
    

if __name__=="__main__":
    # Create a session
    spark_sesion = SparkSession.builder\
                    .appName("WikiStream")\
                    .master("spark://spark-master:7077")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.3.0.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/spark-streaming-kafka-0-10_2.12-3.3.0.jar")\
                    .config("spark.sql.adaptive.enable", False)\
                    .getOrCreate()
    
    spark_sesion.sparkContext.setLogLevel("WARN")
    kafka_spark_consumer(spark_sesion)
    spark_sesion.stop()