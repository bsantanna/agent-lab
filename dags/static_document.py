from airflow import DAG
from airflow.decorators import task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from kubernetes.client import V1Volume, V1VolumeMount, V1NFSVolumeSource
import base64
import json
import os
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
}

dag = DAG(
    'static_document_data',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
)

volume = V1Volume(
    name='network-data',
    nfs=V1NFSVolumeSource(
        server='venus.btech.software',
        path='/mnt/network-data'
    )
)

volume_mount = V1VolumeMount(
    name='network-data',
    mount_path='/mnt/data',
    sub_path=None,
    read_only=True
)

@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="default",  # Adjust according to your Kubernetes setup
    volumes=[volume],
    volume_mounts=[volume_mount],
    executor_config={
        "pod_override": {}
    }
)
def fetch_and_sort_files():
    import os
    files = {'pptx': [], 'docx': [], 'pdf': [], 'jpg': [], 'json': []}
    for root, _, filenames in os.walk('/mnt/data'):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]  # Remove the dot
            if ext in files:
                files[ext].append(os.path.join(root, filename))
    return files

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def convert_to_pdf(file_path):
    # Example command to convert docx to pdf using libreoffice
    command = f"libreoffice --headless --convert-to pdf {file_path}"
    os.system(command)

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def pdf_to_jpg(pdf_path):
    # Example command to convert PDF to JPG, might require additional tools like pdftoppm
    command = f"pdftoppm -jpeg {pdf_path} {os.path.splitext(pdf_path)[0]}"
    os.system(command)

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def process_jpg(jpg_path):
    with open(jpg_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        # Here you would call your Python script with the base64 encoded string
        print(f"Processing {jpg_path} with base64 content")

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def process_json(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
        # Here you would call your Python script with the JSON data
        print(f"Processing JSON from {json_path}")

with dag:
    files = fetch_and_sort_files()
    print(files)
    #
    # # Process PPTX to PDF
    # for file in files['pptx']:
    #     convert_to_pdf(file)
    #
    # # Process DOCX to PDF
    # for file in files['docx']:
    #     convert_to_pdf(file)
    #
    # # Process PDF to JPG
    # for file in files['pdf']:
    #     pdf_to_jpg(file)
    #
    # # Process JPG
    # for file in files['jpg']:
    #     process_jpg(file)
    #
    # for file in files['json']:
    #     process_json(file)
