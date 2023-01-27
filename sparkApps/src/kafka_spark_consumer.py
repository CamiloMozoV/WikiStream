import os
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
    from_json,
    col,
    from_unixtime,
    to_date,
    to_timestamp
)
from sparkApps import config

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

def performs_model_transformation(df: DataFrame) -> DataFrame:
    """Some transformation like, column renaming, and column conversion
    unix timestamp to timestamp
    """
    df_formatted = df.select(
        col("value.$schema").alias("schema"),
        "value.bot",
        "value.comment",
        "value.id",
        col("value.length.new").alias("length_new"),
        col("value.length.old").alias("length_old"),
        "value.minor",
        "value.namespace",
        "value.parsedcomment",
        "value.patrolled",
        col("value.revision.new").alias("revesion_new"),
        col("value.revision.old").alias("revesion_old"),
        "value.server_name",
        "value.server_script_path",
        "value.server_url",
        to_timestamp(from_unixtime(col("value.timestamp"))).alias("change_timestamp"),
        to_date(from_unixtime(col("value.timestamp"))).alias("change_timestamp_date"),
        "value.title",
        "value.type",
        "value.user",
        "value.wiki",
        col("value.meta.domain").alias("meta_domain"),
        col("value.meta.dt").alias("meta_dt"),
        col("value.meta.id").alias("meta_id"),
        col("value.meta.offset").alias("meta_offset"),
        col("value.meta.partition").alias("meta_partition"),
        col("value.meta.request_id").alias("meta_request_id"),
        col("value.meta.stream").alias("meta_stream"),
        col("value.meta.topic").alias("meta_topic"),
        col("value.meta.uri").alias("meta_uri")
    ) 

    return df_formatted

def upload_to_minio(df: DataFrame) -> None:
    
    df.writeStream\
        .format("parquet")\
        .option("path", "s3a://wikistream/stream/")\
        .option("checkpointLocation", "/opt/bitnami/spark/tmp/checkpoint")\
        .partitionBy("change_timestamp_date", "server_name")\
        .outputMode("append")\
        .start()\
        .awaitTermination()

def kafka_spark_consumer(spark_session: SparkSession) -> None:
    df_raw = read_kafka_stream(spark_session)
    df_wikiStream = data_schema_stream(df_raw)
 
    df_final = performs_model_transformation(df_wikiStream)
    upload_to_minio(df_final)

if __name__=="__main__":
    # Create a session
    spark_sesion = SparkSession.builder\
                    .appName("WikiStream")\
                    .master("spark://spark-master:7077")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.3.0.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/spark-streaming-kafka-0-10_2.12-3.3.0.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/hadoop-aws-3.3.4.jar") \
                    .config("spark.jars", "/opt/bitnami/spark/jars/aws-java-sdk-1.12.319.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/hadoop-common-3.3.4.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/hadoop-client-3.3.4.jar")\
                    .config("spark.jars", "/opt/bitnami/spark/jars/aws-java-sdk-s3-1.12.319.jar")\
                    .config("spark.sql.adaptive.enable", False)\
                    .getOrCreate()
    
    spark_sesion.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.access.key", config.MINIO_ACCESS_KEY)
    spark_sesion.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.secret.key", config.MINIO_SECRET_KEY)
    spark_sesion.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", config.MINIO_ENDPOY)

    spark_sesion.sparkContext.setLogLevel("WARN")
    kafka_spark_consumer(spark_sesion)
    spark_sesion.stop()