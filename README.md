# ubuntuUploadByPython
* 功能：将指定文件夹的文件夹打包压缩上传至linux。可后台常驻，支持出错log排查  
* 本地文件说明 
  * config.json-----配置文件，updir-上传文件路径，compress-本机压缩文件路径，ip-上传地址，user-用户名，passwd-密码 
  * list.json-----本地上传列表，只保存文件夹 
* 启动 
  * 启动checkUpdown.py会一直启动上传程序，用来防止上传程序出错崩溃退出 
  * 启动__init__.py会遍历配置文件中的compress目录文件夹后上传
