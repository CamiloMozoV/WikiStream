import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StringType
from sparkApps.src.kafka_spark_consumer import read_kafka_stream

@pytest.mark.usefixtures("spark_session")
def test_read_kafka_stream(spark_session: SparkSession):
    df = read_kafka_stream(spark_session)
    assert type(df).__name__ == "DataFrame"
    assert df.columns == ["key", "value", "topic", "partition", "offset", "timestamp", "timestampType"] 
    assert df.schema["key"].dataType == StringType()
    assert df.schema["value"].dataType == StringType()