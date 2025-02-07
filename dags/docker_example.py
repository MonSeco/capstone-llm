from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "airflow",
    "description": "Use of the DockerOperator",
    "depend_on_past": False,
    "start_date": datetime(2021, 5, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "docker_operator_dag",
    default_args=default_args,
    schedule_interval="5 * * * *",
    catchup=False,
) as dag:

    t1 = DockerOperator(
        task_id="docker_command_hello",
        image="capstone_img",
        #container_name="task___command_hello",
        api_version="auto",
        auto_remove=True,
        #command="/bin/sleep 40",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
    )
