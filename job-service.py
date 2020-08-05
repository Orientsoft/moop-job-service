from __future__ import print_function
import traceback
import time
import logging
import logging.handlers
import sys
import uuid
import copy
import pprint

from kubernetes import config
import kubernetes.client
from kubernetes.client.rest import ApiException

from celery import Celery
from kombu import Queue

from celery_config import broker_url, result_backend, enable_utc
import yaml

pp = pprint.PrettyPrinter(indent=4)

# consts
CONFIG_PATH = './config.yaml'

template = {
    "kind": "Job",
    'spec': {
        "template": {
            'spec': {
                'volumes': [],
                'restartPolicy': 'Never',
                # 'ttlSecondsAfterFinished': 0,
                'containers': [
                    {
                        "image": "{}",
                        'args': [
                            '/bin/sh',
                            '-c',
                            '{}'
                        ],
                        'volumeMounts': [],
                        'name': 'copy',
                        'imagePullPolicy': 'IfNotPresent'
                    }
                ]
            }
        }
    },
    'apiVersion': 'batch/v1',
    'metadata': {
        "name": "job-{}"  # name template - "job-{hash}"
    }
}

with open(CONFIG_PATH) as config_file:
    config_str = config_file.read()
    configs = yaml.load(config_str)

    LOG_LEVEL = configs['log_level']

    DEBUG = configs['debug']
    IN_CLUSTER = configs['in_cluster']

    NAMESPACE = configs['job_namespace']

    PENDING_TIMEOUT = configs['pending_timeout']
    PENDING_INTERVAL = configs['pending_interval']

# logger
LOG_NAME = 'Job-Service'
LOG_FORMAT = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s:%(funcName)s - [%(levelname)s] %(message)s'


def setup_logger(level):
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)

    logger = logging.getLogger(LOG_NAME)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


logger = setup_logger(int(LOG_LEVEL))

if IN_CLUSTER:
    config.load_incluster_config()
else:
    # load kube config from .kube
    config.load_kube_config()

# create an instance of the API class
# api_instance = kubernetes.client.CoreV1Api()
api_instance = kubernetes.client.BatchV1Api()

# read config & init objects
celery = Celery()


# in docker load config  method
class Config:
    broker_url = broker_url
    result_backend = result_backend
    enable_utc = enable_utc


celery.config_from_object(Config)

celery.conf.task_queues = (
    Queue('moop-job', routing_key='moop-job'),
)


def create_body(cmd, image, vols):
    body = copy.deepcopy(template)

    body['metadata']['name'] = body['metadata']['name'].format(uuid.uuid4())
    body['spec']['template']['spec']['containers'][0]['args'][2] = cmd
    body['spec']['template']['spec']['containers'][0]['image'] = image

    vol_names = [str(uuid.uuid4()) for vol in vols]
    volumes = []
    volumeMounts = []

    for i, vol in enumerate(vols):
        if vol['type'] == 0:
            # pvc
            volumes.append({
                'name': vol_names[i],
                'persistentVolumeClaim': {'claimName': vol['name']}
            })
        else:
            # configmap
            volumes.append({
                'name': vol_names[i],
                'configMap': {
                    'name': vol['name'],
                    'defaultMode': 420
                }
            })

        volumeMounts.append(
            {
                'name': vol_names[i],
                'mountPath': vol['mount'],
                'subPath': vol['subpath']
            }
        )

    body['spec']['template']['spec']['containers'][0]['volumeMounts'] = volumeMounts
    body['spec']['template']['spec']['volumes'] = volumes

    return body


@celery.task(max_retries=3, name='job-service:run')
def run(cmd, image, vols):
    body = create_body(cmd, image, vols)
    # print(body)

    try:
        job = api_instance.create_namespaced_job(
            body=body,
            namespace=NAMESPACE
        ).to_dict()

        timeout = 0

        # poll result
        while True:
            job = api_instance.read_namespaced_job_status(
                name=body['metadata']['name'],
                namespace=NAMESPACE
            ).to_dict()

            # pp.pprint(job)

            succeeded = job['status']['succeeded']
            failed = job['status']['failed']
            delete_body = kubernetes.client.V1DeleteOptions(propagation_policy='Background')

            if (succeeded is not None) and (succeeded == 1):
                # delete
                job = api_instance.delete_namespaced_job(
                    name=body['metadata']['name'],
                    namespace=NAMESPACE,
                    body=delete_body
                ).to_dict()

                return True
            elif (failed is not None) and (failed == 1):
                # delete
                job = api_instance.delete_namespaced_job(
                    name=body['metadata']['name'],
                    namespace=NAMESPACE,
                    body=delete_body
                ).to_dict()

                return False

            time.sleep(PENDING_INTERVAL)
            timeout += PENDING_INTERVAL

            if timeout > PENDING_TIMEOUT:
                logger.error('Job Expired: {}\n'.format(job))

                job = api_instance.delete_namespaced_job(
                    name=body['metadata']['name'],
                    namespace=NAMESPACE,
                    body=delete_body
                ).to_dict()

                return False
    except ApiException as e:
        logger.error('Request Error: {}\nStack: {}\n'.format(e, traceback.format_exc()))

        return False
    except Exception as e:
        # this might be a bug
        logger.critical('Program Error: {}\nStack: {}\n'.format(e, traceback.format_exc()))

        return False
