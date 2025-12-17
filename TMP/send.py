#!/usr/bin/env python3
"""
同步两个GitHub私有仓库的文件内容
将源仓库的文件覆盖到目标仓库
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import argparse

def run_command(cmd, cwd=None, env=None):
    """执行shell命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误信息: {e.stderr}")
        raise

def setup_git_config(temp_dir):
    """配置Git用户信息"""
    run_command("git config --global user.email 'github-actions@github.com'", cwd=temp_dir)
    run_command("git config --global user.name 'GitHub Actions Bot'", cwd=temp_dir)

def clone_repo(repo_url, token, target_dir, branch="main"):
    """克隆仓库（支持私有仓库）"""
    # 将token插入到URL中进行认证
    auth_url = repo_url.replace("https://", f"https://{token}@")
    
    print(f"正在克隆仓库到: {target_dir}")
    run_command(f"git clone --depth 1 --branch {branch} {auth_url} {target_dir}")
    
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
    
    # 确保目标目录存在
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 复制文件（覆盖式）
    shutil.copy2(source_path, target_path)
    
    return str(target_path)

def commit_and_push(repo_dir, token, repo_url, commit_message="Sync files from source repository"):
    """提交更改并推送到远程仓库"""
    # 切换到目标仓库目录
    os.chdir(repo_dir)
    
    # 添加所有更改
    run_command("git add .")
    
    # 检查是否有更改需要提交
    status = run_command("git status --porcelain")
    if not status:
        print("没有检测到文件更改，跳过提交")
        return False
    
    # 提交更改
    run_command(f'git commit -m "{commit_message}"')
    
    # 配置推送URL（包含token）
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    push_url = f"https://{token}@github.com/{repo_url.split('/')[-2]}/{repo_name}.git"
    
    # 推送到远程仓库
    print("正在推送到远程仓库...")
    run_command(f"git push {push_url} main")
    
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
    
    args = parser.parse_args()
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"工作目录: {temp_dir}")
        
        # 设置Git配置
        setup_git_config(temp_dir)
        
        # 克隆源仓库
        source_dir = Path(temp_dir) / "source"
        clone_repo(args.source_repo, args.source_token, source_dir, args.branch)
        
        # 克隆目标仓库
        target_dir = Path(temp_dir) / "target"
        clone_repo(args.target_repo, args.target_token, target_dir, args.branch)
        
        # 同步文件
        synced_file = sync_files(source_dir, args.source_file, target_dir, args.target_file)
        
        # 提交并推送更改
        if commit_and_push(target_dir, args.target_token, args.target_repo):
            print("✅ 文件同步完成并已推送到远程仓库")
        else:
            print("ℹ️  没有需要同步的更改")

if __name__ == "__main__":
    main()
