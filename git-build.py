#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import json, urllib, urllib2
import Queue
import time, os, sys, popen2
from threading import Thread

PORT_NUMBER = 5909
CLIENT_IPS = set(['207.97.227.253', '50.57.128.197', '108.171.174.178', '127.0.0.1','1.202.198.123']) 
REPO_NAME = 'autobuild_tester'
LOCAL_REPO = 'test_clone/autobuild_tester'
REPORT_DIR =  os.path.join(os.getcwd(), "report")
LOG_FILENAME = os.path.join(REPORT_DIR, "list.txt")
LOG_FILE = open(LOG_FILENAME, "a+")

def currentTimeString():
  s = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
  return s

def reportDir():
  s = time.strftime('%YT%mT%dT%HT%MT%S', time.localtime())
  return s

def reportWriteHeader(f, jobj):
  url = jobj['repository']['url']
  header = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Autobuild System: %s</title>
</head>
<body>
<h1>Autobuild and Test: <a href="%s">%s</a></h1>
<p>%s</p>
<hr />
  ''' % (REPO_NAME, url, REPO_NAME, currentTimeString())
  f.write(header)

def reportWriteFooter(f):
  footer = '''
<p>Powered by Git-Build, Chen Yuheng 2012 (chyh1990@gmail.com)</p>
</body>
</html>
  '''
  f.write(footer)

def reportWriteSection(fname, cmd):
  f = open(fname, 'w')
  p = popen2.Popen4(cmd)
  while True:
    line = p.fromchild.readline()
    if not line:
      break
    f.write(line)
  exitcode = p.wait()
  f.close()
  return exitcode
  

def reportWriteLogToReport(f, logname):
  try:
    fin = open(logname, 'r')
  except:
    f.write('No log file<br />\n')
    return
  while True:
    line = fin.readline()
    if not line:
      break
    f.write(line+'<br />\n')
  fin.close()

def reportWriteCommits(f, jobj):
  commits = jobj['commits']
  f.write('<p>Commits: %s</p>\n' % (len(commits)))
  f.write('<table border="1">\n')
  f.write('<tr><td>ID</td><td>User</td><td>Log</td></tr>')
  for x in commits:
    f.write('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td></tr>' % (x['url'], x['id'], x['author']['name'], x['message']))
  f.write('</table><br />\n')

work_queue = Queue.Queue()
ongoing_task = None
def worker():
  global work_queue, ongoing_task
  phrases = [('fetch.log','Fetch', 'git pull'), ('build.log', 'Build', './autobuild.sh'),
            ('autotest.log', 'AutoTest', './autotest.sh')]
  while True:
    item = work_queue.get(True)
    ongoing_task = {'status': 'Ready', 'info': item}
    reportDirName = reportDir()
    curTestDir = os.path.join(REPORT_DIR, reportDirName)
    os.mkdir(curTestDir)
    reportFile = open(os.path.join(curTestDir,'report.html'),'w')
    reportWriteHeader(reportFile, item)
    print '['+currentTimeString()+']', 'New Job from', item['pusher']

    status = [-1] * len(phrases)
    pcnt = 0
    badstep = "OK"
    for x in phrases:
      ongoing_task['status'] = x[1]
      exitcode = reportWriteSection(os.path.join(curTestDir, x[0]), x[2])
      status[pcnt] = exitcode
      pcnt += 1
      if exitcode != 0:
        print 'Failed to build', x[1], ':', exitcode
        badstep = x[1]
        break

    #status section
    reportFile.write('<h2>Status</h2>\n')
    reportFile.write('<table border="1">\n')
    reportFile.write('<tr><td>Phrase</td><td>Status</td></tr>')
    for i in xrange(len(phrases)):
      if status[i] == 0:
        col = 'green'
      else:
        col = 'red'
      phText = '<a href="#%s"><font color=%s>%s</font></a>' % (phrases[i][1], col, phrases[i][1])
      reportFile.write('<tr><td>%s</td><td>%d</td></tr>' % (phText, status[i]))
      
    reportFile.write('</table>\n')
    reportFile.write('<hr />\n')
    #commit info
    reportFile.write('<h2>Commit Info</h2>\n')
    reportWriteCommits(reportFile, item)
    reportFile.write('<hr />\n')

    for x in phrases:
      reportFile.write('<h2>%s</h2><a name="%s"></a>\n' % (x[1],x[1]))
      reportWriteLogToReport(reportFile, os.path.join(curTestDir, x[0]))
      reportFile.write('<hr />\n')

    reportWriteFooter(reportFile)
    reportFile.close()
    print '['+currentTimeString()+']', 'Job Done'
    LOG_FILE.write(badstep + ' ' + reportDirName + '\n')
    LOG_FILE.flush()
    ongoing_task = None
    time.sleep(2)
    work_queue.task_done()

worker_thread = Thread(target = worker)
worker_thread.daemon = True

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
  #Handler for the GET requests
  def do_GET(self):
    if self.path == '/' or self.path == '/index.html':
      self.writeStatus()
    elif self.path == '/log.html':
      self.writeLog()
    elif self.path.startswith('/report/'):
      self.writeDetails(self.path[8:])
    else:
      self.send_response(404)

  def writeDetails(self, ver):
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    try:
      f = open(os.path.join(REPORT_DIR, ver, 'report.html'))
      while True:
        line = f.readline()
        if not line:
          break
        self.wfile.write(line)
      f.close()
    except:
      self.wfile.write('Error: failed to open file')

  def writeLog(self):
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    page = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Git-build Autobuild System Log</title>
</head>
<body>
<h1>Git-build Autobuild System Log</h1>
<h2>Repo: %s</h2>
''' % (REPO_NAME)
    self.wfile.write(page)

    f = open(LOG_FILENAME, 'r')
    l = []
    while True:
      line = f.readline()
      if not line:
        break
      l.append(line.split(' '))
    l.reverse()
    for x in l:
      if x[0] == 'OK':
        col = 'green'
      else:
        col = 'red'
      m = x[1].split('T')
      s = '%s-%s-%s %s:%s:%s' % (m[0],m[1],m[2],m[3],m[4],m[5])
      self.wfile.write('<a href="%s">%s</a>' % ('report/'+x[1], s))
      self.wfile.write('&nbsp;<font color=%s>%s</font>' % (col, x[0]))
      self.wfile.write('<br />\n')
    f.close()

    page = '''
</body>
</html>
    '''
    self.wfile.write(page)

  def writeStatus(self):
    global ongoing_task
    self.send_response(200)
    self.send_header('Content-type','text/html')
    self.end_headers()
    page = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<!-- no cache headers -->
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="no-cache">
<meta http-equiv="Expires" content="-1">
<meta http-equiv="Cache-Control" content="no-cache">
<!-- end no cache headers -->
<meta http-equiv="refresh" content="5">
<head>
<title>Git-build Autobuild System</title>
</head>
<body>
<h1>Git-build Autobuild System: %s</h1>
<h2><a href="/log.html">Logger</a></h2>
<p>%s</p>
<hr />
<h2>Pending Tasks: %d</h2>
<ul>
<li></li>
</ul>
''' % (REPO_NAME, currentTimeString(), work_queue.qsize())
    self.wfile.write(page)

    if ongoing_task:
      page = '''
<h2>Ongoing Tasks: </h2>
<p>Status: %s</p>
''' % (ongoing_task['status'])
      self.wfile.write(page)
      reportWriteCommits(self.wfile, ongoing_task['info'])

    page = '''
<hr />
<p>by Chen Yuheng 2012</p>
</body>
</html>
'''
    # Send the html message
    self.wfile.write(page)
    return

  def do_POST(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/pain')
    self.end_headers()
    if self.client_address[0] not in CLIENT_IPS:
      self.wfile.write('DENIED');
      return
    content_len = int(self.headers.getheader('content-length'))
    content = self.rfile.read(content_len)
    info = urllib.unquote(content)
    print self.client_address
    jobj = json.loads(info[8:])
    if jobj['repository']['name'] != REPO_NAME:
      self.wfile.write('WRONG_REPO')
      return
    commits = jobj['commits']
    print 'Commits:', len(commits)
    for x in commits:
      print '\t', x['author']['name'], '[' + x['author']['email'] + ']'
    work_queue.put(jobj);
    self.wfile.write("OK");
    return

try:
  #Create a web server and define the handler to manage the
  #incoming request
  os.chdir(LOCAL_REPO)
  server = HTTPServer(('', PORT_NUMBER), myHandler)
  print 'Started httpserver on port ' , PORT_NUMBER

  worker_thread.start()
  #Wait forever for incoming htto requests
  server.serve_forever()

except KeyboardInterrupt:
  print 'Ctrl-C received, shutting down the web server'
  server.socket.close()
  LOG_FILE.close()
