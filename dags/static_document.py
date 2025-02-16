from airflow import DAG
from airflow.decorators import task
from kubernetes.client import V1Volume, V1VolumeMount, V1PersistentVolumeClaimVolumeSource
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

# pvc = V1PersistentVolumeClaim(
#     metadata={
#         "name": "nfs-data-claim",
#         "namespace": "compute"
#     },
#     spec={
#         "accessModes": ["ReadWriteMany"],
#         "resources": V1ResourceRequirements(
#             requests={"storage": "5Gi"}
#         ),
#         "storageClassName": "nfs-client"
#     }
# )

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
    # executor_config={
    #     "pod_override": {
    #         "spec": {
    #             "volumes": [volume.to_dict()],
    #             "persistentVolumeClaims": [pvc.to_dict()]
    #         }
    #     }
    # }
)
def process_files():
    import os
    files = {'pptx': [], 'docx': [], 'pdf': [], 'jpg': [], 'json': []}
    for root, _, filenames in os.walk('/mnt/data'):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()[1:]
            if ext in files:
                files[ext].append(os.path.join(root, filename))
    print(files)

with dag:
    process_files()
