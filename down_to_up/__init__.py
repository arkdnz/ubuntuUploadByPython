from typing import Any
import paramiko
import re
import os
import logging
import json
import zipfile
import time
from time import sleep

# 压缩文件，返回压缩文件名
def Compress(file, savename,dirpath='.'):
    kZip = zipfile.ZipFile(savename, 'a', zipfile.ZIP_DEFLATED)
    kZip.write(os.path.join(dirpath,file))  # 绝对路径
    kZip.close()

# ubantu连接
class ubantu(object):
    # 通过IP, 用户名，密码，超时时间初始化一个远程Linux主机
    def __init__(self, ip, username, password, timeout=30):
        self.ip = ip
        self.username = username
        # transport和chanel
        self.password = password
        self.timeout = timeout
        self.t = ''
        self.chan = ''
        # 链接失败的重试次数
        self.try_times = 3

    # 调用该方法连接远程主机
    def connect(self):
        while True:
            # 连接过程中可能会抛出异常，比如网络不通、链接超时
            try:
                self.t = paramiko.Transport(sock=(self.ip, 22))
                self.t.connect(username=self.username, password=self.password)
                self.chan = self.t.open_session()
                self.chan.settimeout(self.timeout)
                self.chan.get_pty()
                self.chan.invoke_shell()
                # 如果没有抛出异常说明连接成功，直接返回
                logging.info(u'连接成功')
                print(u'连接%s成功' % self.ip)
                # 接收到的网络数据解码为str
                print(self.chan.recv(65535).decode('utf-8'))
                return
            # 这里不对可能的异常如socket.error, socket.timeout细化，直接一网打尽
            except Exception:
                if self.try_times != 0:
                    logging.warning(u'连接%s失败，进行重试' % self.ip)
                    print(u'连接%s失败，进行重试' % self.ip)
                    self.try_times -= 1
                else:
                    print(u'重试3次失败，结束程序')
                    logging.error(u'重试失败，结束程序')
                    exit(1)

    # 断开连接
    def close(self):
        self.chan.close()
        self.t.close()

    # 发送要执行的命令
    def send(self, cmd, pattern=' '):
        cmd += '\n'
        # 通过命令执行提示符来判断命令是否执行完成
        patt = pattern
        p = re.compile(patt)
        result = ''
        # 发送要执行的命令
        self.chan.send(cmd)
        logging.info(u'发送指令%s' % cmd)
        # 回显很长的命令可能执行较久，通过循环分批次取回回显
        while True:
            sleep(0.5)
            ret = self.chan.recv(65535)
            ret = ret.decode('utf-8')
            result += ret
            if p.search(ret):
                print(result)
                return result

    # 查找文件
    def checkFile(self, filename):
        try:
            # 根据发送的ls命令查看ubuntu是否有文件
            dirls = self.send('ls')
            pattern = re.compile(filename)
            if(pattern.findall(dirls)): #文件存在告诉本地为1
                return 1
            else:                           #不存在返回0
                return 0
        except Exception:                   #出错
            logging.info(u'检查失败')
            print(u'检查失败')
            return -1

# 本地发送文件
def localSend(host,dir,file,remotedir):
    sftp = paramiko.sftp_client.SFTPClient.from_transport(host.t)
    try:
        if os.path.isfile(file):
            sftp.put(os.path.join(dir,file), os.path.join(remotedir,file))
            logging.info('上传成功')
    except Exception:
        logging.info(u'上传失败1')
        print(u'上传失败')
        return -1
    finally:
        sftp.close()
    return 1

# 本地遍历文件夹
def dirfile(dir):
    for root, dirs, files in os.walk(dir):
        return dirs

# 检查文件会否未被上传
def localCheck(host,lists,root,dirfiles,remotedir):
    while 1:
        compressname = 'file' + time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '.zip'  # 用当前时间命名
        if lists:   #list里面是上传过的文件夹，dirfiles用来检查是否有新文件夹
            i = 1
            for fileName in dirfiles:
                try:
                    if lists[fileName] == 0:  # 检查是否已上传
                        # 先压缩再上传
                        logging.info(u'压缩文件%s' % fileName)
                        for dirpath, dirname, filenames in os.walk(os.path.join(root,fileName)):

                            for filename in filenames:
                                Compress(filename, compressname, dirpath)
                        logging.info(u'压缩文件%s成功' % fileName)
                        if fileName == list(lists.items())[-1][0]:
                            try:
                                # isload = host.checkFile(fileName)  # 根据文件名查找远程主机是否有文件
                                # if isload == 0:  # 为0表示不存在，需要发送文件
                                logging.info(u'上传文件%s' % fileName)
                                # 先压缩再上传，可以记录上传文件名，用一个json文件维护是否上传过
                                i = localSend(host, './', compressname, remotedir)
                                if i == -1:
                                    logging.info(u'上传文件出错，请检查')
                                    print(u'上传文件出错，请检查')
                                    return
                                else:
                                    zip_file = zipfile.ZipFile(compressname)
                                    cmfiles = zip_file.namelist()
                                    zip_file.close()
                                    for cmfile in cmfiles:
                                        lists[cmfile.split('/')[0]] = 1 # 只保存文件夹名
                                    fp = open(r'./list.json', 'w')
                                    try:
                                        fp.write(json.dumps(lists, ensure_ascii=False, indent=2))
                                        fp.close()
                                    except:
                                        logging.info(u'写入json失败')
                                        fp.close()
                                        exit(1)
                                    try:
                                        os.remove(compressname)
                                    except:
                                        logging.info(u'删除文件出错，请检查')
                                    return
                            except:
                                logging.info(u'压缩文件%s失败' % fileName)
                    if i == len(dirfiles):
                        return
                    i = i + 1
                except:
                    lists[fileName] = 0
                    i = i -1
        else:
            for fileName in dirfiles:
                lists[fileName] = 0

# 测试
def main():
    logging.basicConfig(filename='log.log', level=logging.DEBUG, datefmt='[%Y-%m-%d %H:%M:%S]', format='%(asctime)s %(levelname)s %(filename)s [%(lineno)d] %(threadName)s : %(message)s')
    try:
        fp1 = open(r'./config.json', 'r')
        try:
            uploadconfig=json.load(fp1)
            fp1.close()
            logging.info(u'开始连接')
            host = ubantu(uploadconfig["ip"], uploadconfig["user"], uploadconfig["passwd"])  # ip地址，用户名，密码
            host.connect()
        except:
            fp1.close()
            logging.info('配置文件错误')
            exit(0)
    except:
        logging.info('打开配置文件错误')
        exit(0)
    # uploadconfig = {"updir": ".", "compress": ".", "ip": "192.168.203.128", "user": "123", "passwd": "123", "download":"."}

    host.send('ls')
    try:
        fp = open('./list.json', 'r')
        try:
            lists = json.load(fp)
        except:
            lists = {}
        fp.close()
        # host.send('cd ')    # 打开指定路径
        while 1:
            dirfiles = dirfile(uploadconfig["compress"])    # 遍历文件夹，需要发送的文件在子目录下都为文件夹
            localCheck(host, lists, uploadconfig["compress"], dirfiles, uploadconfig['updir'])   # 本地检查然后发送
            time.sleep(10)
    except:
        exit(1)

if __name__ == '__main__':
    main()
