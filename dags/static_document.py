from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup


import os
from datetime import datetime, timedelta
import base64
import json
from kubernetes.client import models as k8s


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(default_args=default_args, schedule_interval="@daily", catchup=False)
def etl_load_dag():
    @task.kubernetes(
        image="bsantanna/compute-document-utils",
        namespace="default",  # Replace with your namespace
        image_pull_policy="Always",
        name="fetch-files",
        is_delete_operator_pod=True,
        in_cluster=True,
        volume_mounts=[
            k8s.V1VolumeMount(
                name="nfs-volume",
                mount_path="/mnt/network-data"
            )
        ],
        volumes=[
            k8s.V1Volume(
                name="nfs-volume",
                nfs=k8s.V1NFSVolumeSource(
                    server="venus.btech.software",
                    path="/mnt/network-data"
                )
            )
        ],
    )
    def fetch_files():
        root_dir = "/mnt/network-data/storage/projects/"
        return [
            f for f in os.listdir(root_dir) if os.path.isfile(os.path.join(root_dir, f))
        ]

    @task.kubernetes(
        image="bsantanna/compute-document-utils",
        namespace="compute",
        image_pull_policy="Always",
        name="filter-files",
        is_delete_operator_pod=True,
        in_cluster=True,
    )
    def filter_files(files):
        # Split files by extension
        queues = {}
        for file in files:
            ext = file.split(".")[-1]
            if ext not in queues:
                queues[ext] = []
            queues[ext].append(file)
        return queues

    @task.kubernetes(
        image="bsantanna/compute-document-utils",
        namespace="compute",
        image_pull_policy="Always",
        name="task-{{ params.file_type }}",
        is_delete_operator_pod=True,
        in_cluster=True,
    )
    def process_file(file_path, file_type):
        if file_type in ["pptx", "docx"]:
            return BashOperator(
                task_id=f"convert_{file_type}_to_pdf",
                bash_command=f"echo processing {file_path}",
            ).execute(context={})

        elif file_type == "pdf":
            return BashOperator(
                task_id="export_pdf_to_jpg", bash_command=f"echo processing {file_path}"
            ).execute(context={})

        elif file_type == "jpg":
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return PythonOperator(
                task_id="process_jpg",
                python_callable=lambda: print(f"Processing JPG: {encoded_string}"),
                op_args=[encoded_string],
            ).execute(context={})

        elif file_type == "json":
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
            return PythonOperator(
                task_id="process_json",
                python_callable=lambda: print(f"Processing JSON: {data}"),
                op_args=[data],
            ).execute(context={})

    # Define the workflow
    files = fetch_files()
    queues = filter_files(files)

    with TaskGroup("process_files_group") as process_files_group:
        for file_type, file_list in queues:
            for file in file_list:
                process_file(file_path=f'/mnt/network-data/{file}', file_type=file_type)


etl_load_dag = etl_load_dag()
