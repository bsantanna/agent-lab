from airflow import DAG
from airflow.decorators import task
from airflow.utils.log.logging_mixin import LoggingMixin
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
    log = LoggingMixin().log

    try:
        files = {"pptx": [], "docx": [], "pdf": [], "jpg": []}
        for root, _, filenames in os.walk("/mnt/data"):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()[1:]
                if ext in files:
                    files[ext].append(os.path.join(root, filename))

        log.info(f"Found files: {files}")
        return files
    except Exception as e:
        log.error(f"Error mapping files: {str(e)}")
        raise


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pptx_files(ti=None):
    log = LoggingMixin().log
    try:
        files_dict = ti.xcom_pull(task_ids='map_files')
        if not files_dict:
            raise ValueError("No files dictionary received from map_files task")
        pptx_files = files_dict['pptx']
        log.info(f"Processing the following pptx files: {pptx_files}")
        # TODO PPTX processing logic
    except Exception as e:
        log.error(f"Error processing pptx files: {str(e)}")
        raise


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_docx_files(ti=None):
    log = LoggingMixin().log
    try:
        files_dict = ti.xcom_pull(task_ids='map_files')
        if not files_dict:
            raise ValueError("No files dictionary received from map_files task")
        docx_files = files_dict['docx']
        log.info(f"Processing the following docx files: {docx_files}")
        # TODO DOCX processing logic
    except Exception as e:
        log.error(f"Error processing docx files: {str(e)}")
        raise


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pdf_files(ti=None):
    log = LoggingMixin().log
    try:
        files_dict = ti.xcom_pull(task_ids='map_files')
        if not files_dict:
            raise ValueError("No files dictionary received from map_files task")
        pdf_files = files_dict['pdf']
        log.info(f"Processing the following pdf files: {pdf_files}")
        # TODO PDF processing logic
    except Exception as e:
        log.error(f"Error processing pdf files: {str(e)}")
        raise


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_jpg_files(ti=None):
    log = LoggingMixin().log
    try:
        files_dict = ti.xcom_pull(task_ids='map_files')
        if not files_dict:
            raise ValueError("No files dictionary received from map_files task")
        jpg_files = files_dict['jpg']
        log.info(f"Processing the following jpg files: {jpg_files}")
        # TODO JPG processing logic
    except Exception as e:
        log.error(f"Error processing jpg files: {str(e)}")
        raise


with dag:
    mapped_files = map_files()
    pptx_task = process_pptx_files()
    docx_task = process_docx_files()
    pdf_task = process_pdf_files()
    jpg_task = process_jpg_files()

    # Set task dependencies
    mapped_files >> [pptx_task, docx_task, pdf_task, jpg_task]
