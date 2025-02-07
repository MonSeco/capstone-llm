import argparse
import logging
from pyspark.sql import SparkSession
from capstonellm.common.catalog import llm_bucket
from capstonellm.common.spark import ClosableSparkSession
import pyspark.sql.functions as psf
import os

logger = logging.getLogger(__name__)

def clean(spark: SparkSession, environment: str, tag: str):
    df_questions = (spark.read.json(path="s3a://dataminded-academy-capstone-llm-data-us/input/airflow/questions.json")
    .select(psf.col("items"))
    .select(psf.explode(psf.col("items")).alias("item")).selectExpr("item.*")
        .filter(psf.col("accepted_answer_id") > 0)
    ).select(psf.col("title"), psf.col("body").alias("question"), psf.col("accepted_answer_id"), psf.col("link"))

    df_answers = (spark.read.json(path="s3a://dataminded-academy-capstone-llm-data-us/input/airflow/answers.json")
        .select(psf.col("items"))
        .select(psf.explode(psf.col("items")).alias("item")).selectExpr("item.*")
        .filter(psf.col("answer_id") > 0)
        .select(psf.col("answer_id").alias("accepted_answer_id"), psf.col("body"))
    )

    df_combined = df_questions.join(df_answers, how="inner", on="accepted_answer_id")
    
    #df_questions.show(truncate=True)
    #df_answers.show(truncate=False)
    #print(df_combined.count())
    #df_combined.show(truncate=False)

    df_combined.write.json("df_combined.json", mode="overwrite")

    for i, row in enumerate(df_combined.rdd.toLocalIterator()):
        row_df = spark.createDataFrame([row]) 
        row_df.write.json(path=f"s3a://dataminded-academy-capstone-llm-data-us/cleaned/mathieu/airflow/question_{i}.json", mode="overwrite")


def main():
    parser = argparse.ArgumentParser(description="capstone_llm")
    parser.add_argument(
        "-e", "--env", dest="env", help="environment we are executing in", required=False, default="local"
    )
    parser.add_argument(
        "-t", "--tag", dest="tag", help="the tag to process",
        default="python-polars", required=False
    )
    logger.info("starting the cleaning job")

    args = parser.parse_args()
    common_spark_config = {
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    }
    if args.env == "local":
        print("This is a local execution of the capestonellm project")
        session = (
            SparkSession.builder.appName("Spark S3 Integration")
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4")
            .getOrCreate()
        )
        clean(session, args.env, args.tag)
    else:
        with ClosableSparkSession("capstone_llm", spark_config=common_spark_config) as session:
            clean(session, args.env, args.tag)


if __name__ == "__main__":
    main()
