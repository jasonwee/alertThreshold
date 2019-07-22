# http://elliothallmark.com/2016/12/23/requests-with-concurrent-futures-in-python-2-7/
# https://pythonadventures.wordpress.com/tag/threadpoolexecutor/

import requests
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from time import time
urls = ['google.com','cnn.com','reddit.com','imgur.com','yahoo.com']
urls = ["http://"+url for url in urls]
# Time requests running synchronously
then = time()
sync_results = map(requests.get, urls)
print "Synchronous done in %s" % (time()-then)
# Time requests running in threads
then = time()
pool = ThreadPoolExecutor(len(urls))  # for many urls, this should probably be capped at some value.

futures = [pool.submit(requests.get,url) for url in urls]
results = [r.result() for r in as_completed(futures)]
print "Threadpool done in %s" % (time()-then)

