import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark_session() -> SparkSession:
    spark = SparkSession.builder\
            .master("spark://172.28.0.8:7077")\
            .appName("Test")\
            .getOrCreate()
    return spark