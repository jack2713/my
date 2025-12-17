#!/usr/bin/env python3
"""
同步两个GitHub私有仓库的文件内容
将源仓库的文件覆盖到目标仓库
支持多种认证方式
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import argparse
import base64
from urllib.parse import urlparse

def run_command(cmd, cwd=None, env=None, input_text=None):
    """执行shell命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            input=input_text
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误输出: {e.stderr}")
        print(f"标准输出: {e.stdout}")
        raise

def setup_git_config():
    """配置Git用户信息"""
    run_command("git config --global user.email 'github-actions@github.com'")
    run_command("git config --global user.name 'GitHub Actions Bot'")
    # 禁用终端提示
    run_command("git config --global credential.helper 'cache --timeout=300'")

def create_auth_url(repo_url, token):
    """创建带认证的仓库URL"""
    parsed_url = urlparse(repo_url)
    if token:
        # 方法1: 将token插入URL中
        return f"https://{token}@{parsed_url.netloc}{parsed_url.path}"
    return repo_url

def clone_repo_with_token(repo_url, token, target_dir, branch="main"):
    """使用token克隆私有仓库"""
    auth_url = create_auth_url(repo_url, token)
    
    print(f"正在克隆仓库: {repo_url}")
    print(f"目标目录: {target_dir}")
    
    # 设置环境变量（备用方法）
    env = os.environ.copy()
    if token:
        # 方法2: 设置GITHUB_TOKEN环境变量
        env['GITHUB_TOKEN'] = token
        
        # 方法3: 为这个URL设置credential helper
        parsed_url = urlparse(repo_url)
        credential_url = f"https://{parsed_url.netloc}"
        run_command(f'git config --global credential.{credential_url}.helper "!f() {{ echo username=token; echo password={token}; }}; f"')
    
    # 克隆命令
    clone_cmd = f"git clone --depth 1 --branch {branch} {auth_url} {target_dir}"
    
    try:
        output = run_command(clone_cmd, env=env)
        print(f"克隆成功: {output}")
        return target_dir
    except Exception as e:
        print(f"标准克隆方法失败，尝试备用方法...")
        
        # 备用方法：使用git credential store
        try:
            # 先创建目录
            Path(target_dir).parent.mkdir(parents=True, exist_ok=True)
            
            # 初始化并设置远程
            run_command("git init", cwd=target_dir)
            run_command(f"git remote add origin {repo_url}", cwd=target_dir)
            
            # 设置credential
            if token:
                credential_cmd = f'echo "https://token:{token}@{repo_url.split("https://")[1]}" | git credential approve'
                run_command(credential_cmd)
            
            # 拉取指定分支
            run_command(f"git pull origin {branch}", cwd=target_dir)
            print("备用克隆方法成功")
            return target_dir
        except Exception as e2:
            print(f"所有克隆方法都失败: {e2}")
            raise

def clone_repo_with_ssh(repo_url, ssh_key_path, target_dir, branch="main"):
    """使用SSH密钥克隆私有仓库"""
    # 将HTTPS URL转换为SSH格式
    if repo_url.startswith("https://"):
        repo_url = repo_url.replace("https://", "git@").replace("/", ":", 1)
    
    print(f"使用SSH克隆: {repo_url}")
    
    # 设置SSH环境
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    
    # 复制SSH密钥
    shutil.copy2(ssh_key_path, ssh_dir / "id_rsa")
    run_command(f"chmod 600 {ssh_dir / 'id_rsa'}")
    
    # 设置SSH配置
    ssh_config = """
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    User git
"""
    (ssh_dir / "config").write_text(ssh_config)
    run_command("chmod 600 ~/.ssh/config")
    
    # 克隆
    run_command(f"git clone --depth 1 --branch {branch} {repo_url} {target_dir}")
    return target_dir

def sync_files(source_repo_dir, source_file, target_repo_dir, target_file):
    """同步文件内容"""
    source_path = Path(source_repo_dir) / source_file
    target_path = Path(target_repo_dir) / target_file
    
    if not source_path.exists():
        raise FileNotFoundError(f"源文件不存在: {source_path}")
    
    print(f"正在同步文件:")
    print(f"  从: {source_path}")
    print(f"  到: {target_path}")
    
    # 读取源文件内容
    source_content = source_path.read_text(encoding='utf-8')
    print(f"源文件内容预览 (前100字符): {source_content[:100]}...")
    
    # 确保目标目录存在
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入目标文件（覆盖式）
    target_path.write_text(source_content, encoding='utf-8')
    
    # 验证文件是否相同
    target_content = target_path.read_text(encoding='utf-8')
    if source_content == target_content:
        print("✅ 文件内容同步成功")
    else:
        print("⚠️  警告：文件内容不完全相同")
    
    return str(target_path)

def commit_and_push(repo_dir, token, repo_url, commit_message="Sync files from source repository"):
    """提交更改并推送到远程仓库"""
    os.chdir(repo_dir)
    
    # 检查是否有更改
    run_command("git status")
    
    # 添加所有更改
    run_command("git add .")
    
    # 检查是否有更改需要提交
    status = run_command("git status --porcelain")
    if not status:
        print("没有检测到文件更改，跳过提交")
        return False
    
    # 显示具体的更改
    diff_output = run_command("git diff --cached --stat")
    print(f"检测到更改:\n{diff_output}")
    
    # 提交更改
    run_command(f'git commit -m "{commit_message}"')
    
    # 配置推送URL（包含token）
    if token:
        parsed_url = urlparse(repo_url)
        repo_name = parsed_url.path.strip('/').replace('.git', '')
        push_url = f"https://{token}@{parsed_url.netloc}{parsed_url.path}"
        
        print(f"使用推送URL: {push_url.split('@')[0]}@...")
    else:
        push_url = repo_url
    
    # 推送到远程仓库
    print("正在推送到远程仓库...")
    try:
        run_command(f"git push {push_url} main")
        print("✅ 推送成功")
    except Exception as e:
        print(f"推送失败，尝试使用token作为密码的方式...")
        # 备用推送方法
        run_command(f"git push {repo_url} main", input_text=f"token\n{token}\n")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="同步GitHub私有仓库文件")
    parser.add_argument("--source-token", required=True, help="源仓库的GitHub Token")
    parser.add_argument("--target-token", required=True, help="目标仓库的GitHub Token")
    parser.add_argument("--source-repo", default="https://github.com/jack2713/my.git", 
                       help="源仓库URL")
    parser.add_argument("--target-repo", default="https://github.com/jack2713/mynew.git", 
                       help="目标仓库URL")
    parser.add_argument("--source-file", default="myq.txt", help="源文件路径")
    parser.add_argument("--target-file", default="my.txt", help="目标文件路径")
    parser.add_argument("--branch", default="main", help="分支名称")
    parser.add_argument("--use-ssh", action="store_true", help="使用SSH密钥替代token")
    parser.add_argument("--ssh-key", help="SSH私钥路径（当使用SSH时）")
    
    args = parser.parse_args()
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"工作目录: {temp_dir}")
        
        # 设置Git配置
        setup_git_config()
        
        try:
            if args.use_ssh and args.ssh_key:
                # 使用SSH方式
                # 克隆源仓库
                source_dir = Path(temp_dir) / "source"
                clone_repo_with_ssh(args.source_repo, args.ssh_key, source_dir, args.branch)
                
                # 克隆目标仓库（SSH方式需要不同的密钥或配置）
                target_dir = Path(temp_dir) / "target"
                clone_repo_with_ssh(args.target_repo, args.ssh_key, target_dir, args.branch)
            else:
                # 使用HTTPS+Token方式
                # 克隆源仓库
                source_dir = Path(temp_dir) / "source"
                clone_repo_with_token(args.source_repo, args.source_token, source_dir, args.branch)
                
                # 克隆目标仓库
                target_dir = Path(temp_dir) / "target"
                clone_repo_with_token(args.target_repo, args.target_token, target_dir, args.branch)
            
            # 同步文件
            synced_file = sync_files(source_dir, args.source_file, target_dir, args.target_file)
            
            # 提交并推送更改
            if commit_and_push(target_dir, args.target_token, args.target_repo):
                print("✅ 文件同步完成并已推送到远程仓库")
            else:
                print("ℹ️  没有需要同步的更改")
                
        except Exception as e:
            print(f"❌ 同步过程中发生错误: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
