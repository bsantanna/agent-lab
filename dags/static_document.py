from airflow import DAG
from airflow.decorators import task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from kubernetes.client import V1Volume, V1VolumeMount, V1PersistentVolumeClaimVolumeSource
from kubernetes.client import V1PersistentVolumeClaim, V1ResourceRequirements
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

pvc = V1PersistentVolumeClaim(
    metadata={
        "name": "nfs-data-claim",
        "namespace": "compute"
    },
    spec={
        "accessModes": ["ReadWriteOnce"],
        "resources": V1ResourceRequirements(
            requests={"storage": "5Gi"}
        ),
        "storageClassName": "nfs-client"
    }
)

volume = V1Volume(
    name='network-data',
    persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
        claim_name='nfs-data-claim'
    )
)

volume_mount = V1VolumeMount(
    name='network-data',
    mount_path='/mnt/data',
    sub_path=None,
    read_only=False
)

@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
    executor_config={
        "pod_override": {
            "spec": {
                "volumes": [volume.to_dict()],
                "persistentVolumeClaims": [pvc.to_dict()]
            }
        }
    }
)
def fetch_and_sort_files():
    import os
    files = {'pptx': [], 'docx': [], 'pdf': [], 'jpg': [], 'json': []}
    for root, _, filenames in os.walk('/mnt/data'):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext in files:
                files[ext].append(os.path.join(root, filename))
    return files

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def process_files(files_dict):
    for file_type, file_list in files_dict.items():
        for file in file_list:
            if file_type in ['pptx', 'docx']:
                convert_to_pdf(file)
            elif file_type == 'pdf':
                pdf_to_jpg(file)
            elif file_type == 'jpg':
                process_jpg(file)
            elif file_type == 'json':
                process_json(file)

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def convert_to_pdf(file_path):
    command = f"echo {file_path}"
    os.system(command)

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def pdf_to_jpg(pdf_path):
    command = f"echo {pdf_path}"
    os.system(command)

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def process_jpg(jpg_path):
    with open(jpg_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        print(f"Processing {jpg_path} with base64 content")

@task.kubernetes(image="bsantanna/compute-document-utils", volumes=[volume], volume_mounts=[volume_mount])
def process_json(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
        print(f"Processing JSON from {json_path}")

with dag:
    files = fetch_and_sort_files()
    process_files(files)
