
import datetime
import email.utils
import logging
import requests
import json
import operator
import os.path
import smtplib
import subprocess
import sys
import traceback
import threading

from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


# subprocess with thread, so we have timeout and this work in python2 and python3
class Command(object):
    def __init__(self, cmd, res):
        self.cmd = cmd
        self.res = res
        self.process = None

    def run(self, timeout):
        def target(res):
            self.process = subprocess.Popen(self.cmd,stdout=subprocess.PIPE, shell=True)
            stdout, stderr = self.process.communicate()
            res[0] = stdout

        thread = threading.Thread(target=target, args=(self.res,))
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
        #print self.process.returncode


def update_state_file(stateFile, key, value):
    """
    update the stateFile based on the key and value specified

    :param stateFile: the state file where the key and value should be written to
    :param key: the key to write into the stateFile
    :param value: the value that belong to the key to write into the stateFile
    :returns: None

    """
    try:
        with open(stateFile, 'r') as f:
            data = json.load(f)

        with open(stateFile, 'w') as f:
            data[key] = value
            json.dump(data, f, indent=3, sort_keys=True)
            f.write("\n")
    except:
        logger.exception('unable to read or write file %s', stateFile)
        # py2 does not allow message in raising new error
        raise
        

def get_current_value(stateFile, key):
    """
    return the value associated with the key in the specified stateFile

    :param stateFile: the state file where the key and value present
    :param key: the key where the value is associated with
    :returns: 0 if there is not key found in the stateFile. else return the 
              value associated with the key

    """
    try:
        count = 0
        with open(stateFile, 'r') as f:
            data = json.load(f)

            if key not in data:
                return count
            count = data[key]
        return count
    except:
        logger.exception('unable to read file %s', stateFile)
        # py2 does not allow message in raising new error
        raise


def create_state_file(stateFile, template='conf/pristine.json'):
    """
    automatically create state file if it does not found in the directory temp/

    :param stateFile: the state file about to be create
    :param template: the template use to create stateFile. template file can be found at conf/pristine.json
    :returns: None

    """
    try:
        with open(template, 'r') as f:
            data = json.load(f)

            with open(stateFile, 'w') as sf:
                json.dump(data, sf, indent=3, sort_keys=True)
                sf.write("\n")
    except:
        logger.exception('unable to read file %s or write file %s', template, stateFile)
        raise

ops = {
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '>': operator.gt
}

def cmp(arg1, op, arg2):
    operation = ops.get(op)
    return operation(arg1, arg2)

def alert(email_subject, message, arguments):
    msg = MIMEText(message)
    msg['To'] = email.utils.formataddr(('monitoring', arguments.alert_email_recipient))
    msg['From'] = email.utils.formataddr(('SMTPD', arguments.alert_email_from))
    msg['Subject'] = email_subject

    server = smtplib.SMTP(arguments.alert_email_smtp_host, arguments.alert_email_smtp_port)
    #server.set_debuglevel(True)
    try:
        server.sendmail(arguments.alert_email_from, [arguments.alert_email_recipient], msg.as_string())
    finally:
        server.quit()


def check1(check_config, ssh_host, arguments, ops_timeout=60):
    #logger.info("hi, this is check1 " + ssh_host + " " + str(check_config));
    stateFile='{0}/{1}-alert-threshold.json'.format(arguments.state_file_dir, ssh_host.replace('.', '-'))

    if not os.path.isfile(stateFile):
        logger.warn('state file %s not exists, creating...', stateFile)
        create_state_file(stateFile, template='conf/pristine.json')

    r = None
    why_trace_back = None
    why_type = None
    why_value = None

    try:
        result=[None]
        scripts=[]
        cmd = 'ssh -q -o StrictHostKeyChecking=no -p{0} -i {1} {2}@{3} "cd {4};'.format(arguments.ssh_port, arguments.ssh_private_key, arguments.ssh_username, ssh_host, arguments.ssh_host_script_dir)
        for config in check_config:
            #logger.info(config)
            cmd += './{0}; echo ""; '.format(config.script)
            scripts.append(config.script)
        cmd += '"'
        #logger.info(cmd)
        #logger.debug(cmd)
        command = Command(cmd, result)
        command.run(timeout=ops_timeout)
    except: 
        why_type, why_value, why_trace_back = sys.exc_info()
    #logger.info(result[0].decode('UTF-8'))
    results = result[0].decode('UTF-8').strip().split('\n')
    #logger.info(results)
    results = filter(None, results)
    #logger.info(len(results))
    script_results = dict(zip(scripts, results))
    #logger.info(tuple(script_results))
    #for key,value in script_results.items():
    #    logger.info("key " + key)
    #    logger.info("value " + value)

    for config in check_config:
        #logger.info("hi " + config.script)
        #logger.info(script_results[config.script])
        jsonString = '{{ {0} }}'.format(script_results[config.script])
        #logger.info(jsonString)
        jsonObj = json.loads(jsonString)

        if config.metric not in jsonObj:
            logger.error('metric {0} not found in {1} ?!'.format(config.metric, jsonString))
            return

        current_value = float(jsonObj[config.metric])
        count_metric = float(get_current_value(stateFile, config.metric))
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        if cmp(current_value, config.operator, config.value):
            count_metric += 1
            update_state_file(stateFile, config.metric, count_metric)
        else:
            update_state_file(stateFile, config.metric, 0)
        
        update_state_file(stateFile, 'timestamp', current_datetime)

        # read again
        count_metric = int(get_current_value(stateFile, config.metric))

        if cmp(count_metric, config.threshold_operator, config.alert_value):
            email_subject = 'alertThreshold - {0} - {1}:{2}/{3}'.format(ssh_host, config.metric, count_metric, config.alert_value)
            email_content = 'host         : {0}\nmetric       : {1}\nscript : {2}\ncount_metric : {3}\nalert_value  : {4}\ntimestamp    : {5}\n'.format(ssh_host, config.metric, config.script, count_metric, config.alert_value, current_datetime)
            alert(email_subject, email_content, arguments)
        else:
            pass
    return threading.current_thread().name + ": done"

if __name__ == '__main__':
    logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
      stream=sys.stdout,
    )

    logger.info('see unit test for usage')
