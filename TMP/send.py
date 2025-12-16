
import os
import shutil
import subprocess
from pathlib import Path

def setup_git_config():
    """配置Git用户信息"""
    try:
        subprocess.run(['git', 'config', '--global', 'user.name', 'Auto Push Bot'], check=True)
        subprocess.run(['git', 'config', '--global', 'user.email', 'bot@example.com'], check=True)
        print("Git配置已完成")
    except subprocess.CalledProcessError as e:
        print(f"Git配置失败: {e}")

def push_file_between_repos():
    """将私有仓库文件推送到公共仓库"""
    # 定义路径
    private_file = "myq.txt"
    public_repo_dir = "mynew"
    public_file = os.path.join(public_repo_dir, "my.txt")
    
    try:
        # 检查源文件是否存在
        if not os.path.exists(private_file):
            print(f"错误: 源文件 {private_file} 不存在")
            return False
            
        # 确保目标目录存在
        os.makedirs(public_repo_dir, exist_ok=True)
        
        # 复制文件
        shutil.copy(private_file, public_file)
        print(f"文件已从 {private_file} 复制到 {public_file}")
        
        # 初始化公共仓库git（如果尚未初始化）
        if not os.path.exists(os.path.join(public_repo_dir, '.git')):
            subprocess.run(['git', '-C', public_repo_dir, 'init'], check=True)
            print("公共仓库Git已初始化")
        
        # 添加文件到git
        subprocess.run(['git', '-C', public_repo_dir, 'add', 'my.txt'], check=True)
        print("文件已添加到Git暂存区")
        
        # 提交更改
        try:
            subprocess.run([
                'git', '-C', public_repo_dir, 'commit', '-m', 'Auto-sync: Update my.txt from private repo'
            ], check=True)
            print("更改已提交")
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in str(e):
                print("无更改需要提交")
            else:
                raise e
        
        # 推送到远程仓库（假设已配置origin）
        try:
            subprocess.run(['git', '-C', public_repo_dir, 'push', 'origin', 'main'], check=True)
            print("文件已成功推送到远程仓库")
        except subprocess.CalledProcessError as e:
            print(f"推送失败，请确保已配置远程仓库: {e}")
            
        return True
        
    except Exception as e:
        print(f"推送过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    print("开始推送文件...")
    setup_git_config()
    success = push_file_between_repos()
    if success:
        print("文件推送完成!")
    else:
        print("文件推送失败!")

if __name__ == "__main__":
    main()
