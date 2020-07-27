import time

import redis
r = redis.Redis(host='192.168.0.31', port=30078, password='d2VsY29tZTEK')

r.set('foo', 'bar')

for i in range(100):
    print(r.get('foo'))
    time.sleep(5)
    