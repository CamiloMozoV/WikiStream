from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StringType
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

def kafka_spark_consumer(spark_session: SparkSession) -> None:
    read_kafka_stream(spark_session)

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