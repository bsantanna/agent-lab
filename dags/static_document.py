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
def process_pptx_files():
    import os
    import subprocess
    pptx_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "pptx":
                pptx_files.append(os.path.join(root, filename))

    input_data = '\n'.join(pptx_files) + '\n'
    try:
        result = subprocess.run(
            ['convert_to_pdf'],
            input=input_data,
            text=True,
            capture_output=True,
            check=True
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_docx_files():
    import os
    import subprocess
    docx_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "docx":
                docx_files.append(os.path.join(root, filename))

    input_data = '\n'.join(docx_files) + '\n'
    try:
        result = subprocess.run(
            ['convert_to_pdf'],
            input=input_data,
            text=True,
            capture_output=True,
            check=True
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)



@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_pdf_files():
    import os
    import subprocess
    pdf_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "pdf":
                pdf_files.append(os.path.join(root, filename))

    input_data = '\n'.join(pdf_files) + '\n'
    try:
        result = subprocess.run(
            ['extract_images'],
            input=input_data,
            text=True,
            capture_output=True,
            check=True
        )
        print("Result:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e.stderr)


@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
    volumes=[volume],
    volume_mounts=[volume_mount],
)
def process_jpg_files():
    import os
    jpg_files = []
    for root, _, filenames in os.walk("/mnt/data"):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext == "jpg":
                jpg_files.append(os.path.join(root, filename))
    print(f"Processing the following jpg files: {jpg_files}")


with dag:
    pptx_task = process_pptx_files()
    docx_task = process_docx_files()
    pdf_task = process_pdf_files()
    jpg_task = process_jpg_files()

    [pptx_task, docx_task] >> pdf_task >> jpg_task
