# coding=utf-8

import web
import os
import urllib
import urllib2
import json
import time
from settings import *
from collections import namedtuple, deque
from sae.taskqueue import Task, TaskQueue

DEBUG = False


urls = (
    '/', 'Hello',
    '/log', 'Log',
    '/task', 'MyTask',
    '/taskfail', 'TaskFail',
    '/submit_result', 'SubmitResult'
)

app_root = os.path.dirname(__file__)
templates_root = os.path.join(app_root, 'templates')
render = web.template.render(templates_root)

SegResult = namedtuple('SegResult', 'word word_tag index')

# log messages queue
logs = deque()

def log_message(s):
    if len(logs) > 200:
        logs.popleft()

    try:
        if type(s) is unicode:
            logs.append(time.ctime() + '\t' + s.encode('utf-8'))
        else:
            logs.append(time.ctime() + '\t' + str(s))

    except Exception, ex:
        log_message('errors when log: ' + str(ex.args))


log_message('Initializing')

def filter_result(result, keep_return=False):
    if DEBUG:
        result = '''
    [ {"word":"阿乌阿","word_tag":"96","index":"0"}, {"word":"、","word_tag":"151","index":"1"}, {"word":"【","word_tag":"154","index":"2"}, {"word":"附","word_tag":"170","index":"3"}, {"word":"】","word_tag":"155","index":"4"}, {"word":"…","word_tag":"150","index":"5"}, {"word":"…","word_tag":"150","index":"6"} ]
        '''

    # log_message('json result: ' + result)

    data = json.loads(result)
    seg_results = [SegResult(**k) for k in data]

    filtered_result = []
    for seg_result in seg_results:
        word_tag = int(seg_result.word_tag)

        # keep '\t' or '\t\t', and make sure ' \t' is handled
        word = seg_result.word.strip(' ')
        if keep_return and len(word) > 0 and word[0] == '\t':
            for a in word:
                filtered_result.append(a)
            continue

        if word_tag < 141 or word_tag > 160:
            filtered_result.append(word)

    return filtered_result

def get_seg_result(context, keep_return=False):
    # log_message('Segmentation content: ' + context)

    if DEBUG:
        return {
            'result': 'test result',
            'url': '',
            'response': '',
            'filtered_result': filter_result('') or ''
        }

    result = url = response= ''
    filtered_result = None
    try:
        payload = urllib.urlencode([('context', context),])
        req = urllib2.urlopen(SEGMENT_BASE_URL, payload)
        url = req.geturl()
        response = str(req.info())
        result = req.read()

        filtered_result = filter_result(result, keep_return=keep_return)

    except Exception, ex:
        print ex
        error_message = 'Encounter an error when get segmentation result: ' + type(ex).__name__ + ' ' + str(ex.args)
        log_message(error_message)
        log_message('context: ' + context)
        log_message('returned result: ' + result)

    return {
        'result': result or '',
        'url': url,
        'response': response,
        'filtered_result': filtered_result or ''
    }

class Log:
    def GET(self):
        web.header('Content-type','text/html; charset=utf-8')
        return '<br/>'.join(logs)

class SubmitResult:
    def GET(self):
        return 'only accept POST data'

    def POST(self):
        seg_result = web.input().seg_result.encode('utf-8')
        taskid = web.input().taskid
        file_name = web.input.file_name

        dir_path = os.path.join(PATH_PREFIX, file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        f = open(os.path.join(dir_path, str(taskid)), 'w')
        f.write(seg_result)
        f.close()

        return 'Got it'

def assemble_result(context, filtered_result, taskid=0, file_name=''):
    # Only segement the title and keyword
    newcontent = []
    try:
        result = deque(filtered_result)

        def get_valid_result():
            ar = []
            while True:
                if len(result) == 0:
                    break

                # make sure ' \t' is handled
                r = result.popleft().strip(' ')
                if r == '\t':
                    break

                ar.append(r)

            return ' '.join(ar)

        # compose the url and segemented title/keywords with the category as the new result
        handled_num = 0
        lines = context.split('\r')
        for line in lines:
            if len(result) < 1:
                log_message('There must be something wrong, handled_num ' + str(handled_num) + ', total ' + str(len(lines)) + ', taskid: ' + str(taskid) + ', file_name' + file_name)
                log_message('filtered results: ' + ' '.join(filtered_result))
                break

            handled_num += 1

            tmp = line.split('\t')
            if len(tmp) != 4:
                continue

            tmp[1] = get_valid_result()
            tmp[2] = get_valid_result()

            newcontent.append('\t'.join(tmp))
    except Exception, ex:
        result = 'Encounter an error when dequeue: ' + type(ex).__name__ + ' ' + str(ex.args)
        print ex
        log_message(result)

    return newcontent

class MyTask:
    def GET(self):
        log_message('Task is excecuted')
        return ''

    def POST(self):
        context = web.input().context.encode('utf-8')
        taskid = web.input().taskid
        file_name = web.input().file_name

        # Only segement the title and keyword
        seg_content = []
        lines = context.split('\r')
        for line in lines:
            tmp = line.split('\t')
            seg_content.append(tmp[1])
            seg_content.append(tmp[2])

        results = get_seg_result('\t'.join(seg_content), keep_return=True)
        newcontent = assemble_result(context, results['filtered_result'], taskid=taskid, file_name=file_name)

        # log_message('Task ' + taskid + ' is excecuted (post), result: ' + '<br /> '.join(newcontent))

        # submit to server
        try:
            # payload = urllib.urlencode([('seg_result', ''.join(newcontent).encode('utf-8')), ('taskid', taskid), ])
            # req = urllib2.urlopen(SUBMIT_RESULT_URL, payload)
            # log_message('submit task ' + str(taskid) + ' to server' + req.read())
            from sae.storage import Bucket
            bucket = Bucket('mozillaup')
            bucket.put_object(file_name + '/' + str(taskid), ''.join(newcontent).encode('utf-8'))
            # log_message('submit task ' + str(taskid) + ' to bucket')
        except Exception, ex:
            print ex
            result = 'Encounter an error when submit task' + type(ex).__name__ + ' ' + str(ex.args)
            log_message(result)
        return ''

class TaskFail:
    def GET(self):
        log_message('Task is failed')
        return ''

# global task id
g_task_id = 0

seg_content = []
content_length = 0

def create_seg_task(f, file_name, zip_file=False):
    queue = TaskQueue('seg_queue')
    # reset task id, make sure it starts from 0 for every file
    global g_task_id
    g_task_id = 0

    def _process_line(line):
        # only segment the title and keyword
        # XXX bug: when content contains €, result is broken
        tmp = line.replace('€', '').split('\t')
        if len(tmp) < 4:
            log_message('content format error: ' + line)
            return

        global g_task_id
        global seg_content
        global content_length

        # the seg service is limited to 10k
        if content_length + len(tmp[1]) + len(tmp[2]) > 5000:
            # log_message('Add task ' + str(g_task_id))
            try:
                params = [
                    ('context', '\r'.join(seg_content)),
                    ('taskid', str(g_task_id)),
                    ('file_name', file_name),
                ]
                payload = urllib.urlencode(params)
                queue.add(Task('/task', payload))
            except Exception, ex:
                result = 'Encounter an error when executing queue: ' + type(ex).__name__ + ' ' + str(ex.args)
                log_message(result)

            seg_content = []
            content_length = 0
            g_task_id += 1
        else:
            seg_content.append(line)
            content_length += len(tmp[1]) + len(tmp[2])

    if not zip_file:
        for line in f:
            _process_line(line)
    else:
        import zipfile
        zf = zipfile.ZipFile(f)
        for name in zf.namelist():
            # skip dir
            if name.endswith('/'):
                continue

            log_message('Process file: ' + name)
            for line in zf.read(name).split('\n'):
                _process_line(line)

class Hello:
    def GET(self):
        return render.hello()

    def POST(self):
        context = web.input().context
        f = web.input(myfile={})

        # type(context) is <unicode>
        if context is not None and context.encode('utf-8') is not '':
          r = get_seg_result(context.encode('utf-8'))
          return render.hello(context=context, result=r['result'], url=r['url'], response=r['response'], seg_results=' '.join(r['filtered_result']))

        elif f is not None:
            log_message('Get uploaded file')

            web.header('Content-type','text/html')
            web.header('Transfer-Encoding','chunked')

            if f.myfile.filename.endswith('.zip'):
                create_seg_task(f.myfile.file, f.myfile.filename, True)
                return 'ZIP File is accepted'
            else:
                create_seg_task(f.myfile.file, f.myfile.filename)
                return 'File is accepted'
        else:
            return render.hello()

# try:
#     req = urllib2.urlopen(SUBMIT_RESULT_URL)
#     log_message(req.read())
# except Exception, ex:
#     result = 'Encounter an error when executing queue: ' + type(ex).__name__ + ' ' + str(ex.args)
#     log_message(result)

# try:
#     from sampleresult import *
#     from sampledata import *
#     print assemble_result(sample_data, sample_result)
# except Exception, ex:
#     print ex
#     result = 'Encounter an error when executing queue: ' + type(ex).__name__ + ' ' + str(ex.args)
#     log_message(result)

