from pyspark.sql import SparkSession

# 初始化 SparkSession
spark = SparkSession.builder \
    .appName("PythonSparkSQLExample") \
    .master("yarn") \
    .config("spark.ui.port", "4040")\
    .getOrCreate()
# .master("192.168.208.41")\

# 打印 Spark 版本
print("Spark version:", spark.version)
