from celery import Celery
from celery.result import AsyncResult

celery_app = Celery()


# celery 配置文件，此文件相对独立，尽量保持不从其他文件import
class Config:
    # broker_url = 'redis://:d2VsY29tZTEK@192.168.0.31:31739/0'
    broker_url = 'redis://:UmVkaXMK@192.168.0.116:6379/0'
    # result_backend = 'redis://:UmVkaXMK@192.168.0.116:6379/0'

celery_app.config_from_object(Config)

'''
example1:
    # # send_task(worker文件.函数名,args=[参数],queue='任务队列',routing_key='同queue')
    task = celery_app.send_task('job-worker.join_classroom', args=['/moop/cid/project', 'fadfsdf2123'], queue='moop-job', routing_key='moop-job')
    print(task.id)
    
example2:
    # 根据task.id 查询执行结果
    from celery.result import AsyncResult, allow_join_result
    res = AsyncResult(id=taskid)
    try:
        with allow_join_result():
            res.get(interval=0.1, callback=on_msg)
    except:
        on_fail(taskid, '网络异常，检测失败')
    finally:
        return ''
        
    on_msg为成功的回调，on_fail为失败的回调
    # print(task.get(on_message=on_raw_message, propagate=False))
'''

cmd = 'mc ls moop/moop-lab'
image = 'registry.mooplab.com:8443/tools/moop-tools:v1.0.0'  # optional, default: 'registry.mooplab.com:8443/tools/moop-tools:v1.0.0'
vols = [
    {
        "type": 1,  # 0 - pvc, 1 - configmap
        "name": 'moop-tools-configmap',  # pvc or configmap name
        "mount": '/root/.mc/config.json',  # mount point
        "subpath": 'config.json'  # mount sub path
    }
]

# kwargs={'cmd': cmd, 'image': image, 'vols': vols}

def on_raw_message(body):
    print(body)


task = celery_app.send_task('job-service:run', args=[cmd,image,vols], queue='moop-job',
                            routing_key='moop-job')
print(task.id)
