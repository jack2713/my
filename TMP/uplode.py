from ftplib import FTP

# FTP 服务器信息
ftp_host = 'ftp.tttttttttt.top'  # FTP 服务器地址
ftp_user = 'fr3t_37389457'    # FTP 用户名
ftp_password = 'Groupama2010'  # FTP 密码

# 本地文件路径和远程文件路径
local_file_path = 'myq.txt'  # 本地文件路径
remote_file_path = '/htdocs/myq.txt'  # 远程文件路径

# 连接到 FTP 服务器
try:
    ftp = FTP(ftp_host)  # 连接到 FTP 服务器
    ftp.login(ftp_user, ftp_password)  # 登录
    print("成功连接到 FTP 服务器")

    # 打开本地文件并上传
    with open(local_file_path, 'rb') as file:
        ftp.storbinary(f'STOR {remote_file_path}', file)  # 上传文件
    print(f"文件 {local_file_path} 已成功上传到 {remote_file_path}")

except Exception as e:
    print(f"发生错误: {e}")

finally:
    # 关闭 FTP 连接
    if 'ftp' in locals():
        ftp.quit()
        print("FTP 连接已关闭")
