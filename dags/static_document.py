from airflow import DAG
from airflow.decorators import task
from kubernetes.client import (
    V1Volume,
    V1VolumeMount,
    V1PersistentVolumeClaimVolumeSource,
)
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
}

dag = DAG(
    "static_document_data",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
)

volume = V1Volume(
    name="network-data",
    persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
        claim_name="nfs-data-claim"
    ),
)

volume_mount = V1VolumeMount(
    name="network-data",
    mount_path="/mnt/data",
    sub_path=None,
    read_only=False
)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def map_files():
    import os

    files = {"pptx": [], "docx": [], "pdf": [], "jpg": []}
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext in files:
                files[ext].append(os.path.join(root, filename))

    return files


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pptx_files(ti=None):
    files_dict = ti.xcom_pull(task_ids='map_files')
    pptx_files = files_dict['pptx']
    print(f"Processing the following pptx files: {pptx_files}")


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_docx_files(ti=None):
    files_dict = ti.xcom_pull(task_ids='map_files')
    docx_files = files_dict['docx']
    print(f"Processing the following docx files: {docx_files}")


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pdf_files(ti=None):
    files_dict = ti.xcom_pull(task_ids='map_files')
    pdf_files = files_dict['pdf']
    print(f"Processing the following pdf files: {pdf_files}")


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_jpg_files(ti=None):
    files_dict = ti.xcom_pull(task_ids='map_files')
    jpg_files = files_dict['jpg']
    print(f"Processing the following jpg files: {jpg_files}")


with dag:
    mapped_files = map_files()
    process_pptx_files(mapped_files)
    process_docx_files(mapped_files)
    process_pdf_files(mapped_files)
    process_jpg_files(mapped_files)
