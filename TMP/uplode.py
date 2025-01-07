import paramiko

# SFTP 服务器信息
sftp_host = 'ftpupload.net'  # SFTP 服务器地址
sftp_user = 'fr3t_37389457'     # SFTP 用户名
sftp_password = 'Grouapam2010'  # SFTP 密码

# 本地文件路径和远程文件路径
local_file_path = 'myq.txt'  # 本地文件路径
remote_file_path = 'myq.txt'  # 远程文件路径

# 连接到 SFTP 服务器
try:
    # 创建 SSH 客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(sftp_host, username=sftp_user, password=sftp_password)

    # 创建 SFTP 客户端
    sftp = ssh.open_sftp()
    print("成功连接到 SFTP 服务器")

    # 上传文件
    sftp.put(local_file_path, remote_file_path)
    print(f"文件 {local_file_path} 已成功上传到 {remote_file_path}")

except Exception as e:
    print(f"发生错误: {e}")

finally:
    # 关闭 SFTP 连接
    if 'sftp' in locals():
        sftp.close()
    if 'ssh' in locals():
        ssh.close()
    print("SFTP 连接已关闭")
