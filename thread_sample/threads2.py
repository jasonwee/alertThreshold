"""
import concurrent.futures
import urllib.request

URLS = ['http://www.foxnews.com/',
   'http://www.cnn.com/',
   'http://europe.wsj.com/',
   'http://www.bbc.co.uk/',
   'http://some-made-up-domain.com/']

def load_url(url, timeout):
   with urllib.request.urlopen(url, timeout = timeout) as conn:
       return conn.read()

with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:

   future_to_url = {executor.submit(load_url, url, 60): url for url in URLS}
   for future in concurrent.futures.as_completed(future_to_url):
       url = future_to_url[future]
       try:
           data = future.result()
       except Exception as exc:
          print('%r generated an exception: %s' % (url, exc))
       else:
          print('%r page is %d bytes' % (url, len(data)))
"""

# https://www.tutorialspoint.com/concurrency_in_python/concurrency_in_python_pool_of_processes
from concurrent.futures import ProcessPoolExecutor
from time import sleep

def task(message):
   sleep(2)
   return message

def main():
    executor = ProcessPoolExecutor(5)
    future = executor.submit(task, ("Completed"))
    print(future.done())
    sleep(2)
    print(future.done())
    print(future.result())
    # https://cpython-test-docs.readthedocs.io/en/latest/library/concurrent.futures.html#future-objects
    #print(future.result(timeout=1))
    #executor.shutdown(wait=True)


if __name__ == '__main__':
    main()
