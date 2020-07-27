# job-service

K8s job management service, customized for MOOP API Server.  

## images

During deployment, please build image with dockerfiles in the project root.  
Record image tag for further api requests.  

## config.yaml

Please place config.yaml under the root of pod service.  

config.yaml:  
```yaml
debug: true
# whether the service is running in a k8s cluster
in_cluster: false
# 10 - debug
log_level: 10
default_image: 'registry.mooplab.com:8443/tools/moop-tools:v1.0.0'
job_namespace: 'playfield'
pending_timeout: 60
pending_interval: 1
```

### celery-config.py

Place celery-config.py under the root of job service.

celery-config.py:
```py
broker_url = 'redis://:pass@a.b.c.d:6379/0'
result_backend = 'redis://:pass@a.b.c.d:6379/0'
```

## dev start

```sh
celery -A job-service worker -n job-service-dev
```

## stop all workers

```sh
ps -ef | grep job-service | grep -v grep | awk '{print $2}' | xargs kill -9
```

## API  

### job 

celery task:  

```python
exec(cmd, image, vols)
```

parameters:  

```python
cmd = String
image = String
vols = [
    {
        "type": Number, # 0 - pvc, 1 - configmap
        "name": String, # pvc or configmap name
        "mount": String, # mount point
        "subpath": String # mount sub path
    }
]
```

return:  
```py
True # job successed  
False # job failed or error  
```