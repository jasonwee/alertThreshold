from setuptools import setup, find_packages

# see https://github.com/pytorch/vision/blob/master/setup.py
setup(name='alert_threshold',
      version='0.1',
      description='app to alert if threshold is reached',
      url='https://github.com/jasonwee/alertThreshold',
      author='Jason Wee',
      author_email='peichieh@gmail.com',
      license='apache v2',
      packages=find_packages(),
      include_package_data=True,
      test_suite='nose.collector',
      tests_require=['nose'],
      install_requires=[])

