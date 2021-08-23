import os

def execmd(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text

def restart():
    RunnngCmd = 'python3 __init__.py'
    os.system(RunnngCmd)

if __name__ == '__main__':
    while 1:
        programeIsRunnngCmd='ps -ef|grep python\ __init__.py|grep -v grep'
        programeIsRunnngCmdAns=execmd(programeIsRunnngCmd)
        ansLine=programeIsRunnngCmdAns.split('\n')
        if len(ansLine) > 2:
            print("__init__.py is running")
        else :
            if len(ansLine) == 1:
                restart()
