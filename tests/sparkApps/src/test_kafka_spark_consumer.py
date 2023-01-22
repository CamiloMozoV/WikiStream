import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType
from sparkApps.src.kafka_spark_consumer import (
    read_kafka_stream, 
    data_schema_stream,
    performs_model_transformation
)

@pytest.mark.usefixtures("spark_session")
def test_read_kafka_stream(spark_session: SparkSession):
    df = read_kafka_stream(spark_session)
    assert type(df).__name__ == "DataFrame"
    assert df.columns == ["key", "value", "topic", "partition", "offset", "timestamp", "timestampType"] 
    assert df.schema["key"].dataType == StringType()
    assert df.schema["value"].dataType == StringType()

@pytest.mark.usefixtures("spark_session")
def test_data_schema_stream(spark_session: SparkSession):
    raw_df = read_kafka_stream(spark_session)
    df_wikiStream = data_schema_stream(raw_df)

    data = df_wikiStream.schema.fields[1].jsonValue()["type"]["fields"]
    assert len(data) == 19

@pytest.mark.usefixtures("spark_session")
def test_performs_model_transformation(spark_session: SparkSession):
    raw_df = read_kafka_stream(spark_session)
    df_wikiStream = data_schema_stream(raw_df)
    df_formatted = performs_model_transformation(df_wikiStream)

    assert len(df_formatted.schema) == 30
    fields = [
        "schema", "bot", "comment", "id", "length_new", "length_old", "minor",
        "namespace", "parsedcomment", "patrolled", "revesion_new", "revesion_old",
        "server_name", "server_script_path", "server_url", "change_timestamp",
        "change_timestamp_date", "title", "type", "user", "wiki", "meta_domain",
        "meta_dt", "meta_id", "meta_offset", "meta_partition", "meta_request_id",
        "meta_stream", "meta_topic", "meta_uri"
    ]
    assert df_formatted.schema.fieldNames() == fields