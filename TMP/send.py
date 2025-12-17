#!/usr/bin/env python3
"""
主动从源仓库推送文件到目标仓库
部署在源仓库中执行
"""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def run_cmd(cmd, cwd=None, check=True, verbose=True):
    """执行命令并打印输出"""
    if verbose:
        print(f"💻 执行: {cmd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if verbose:
        if result.stdout:
            print(f"📤 输出: {result.stdout[:500]}")
        if result.stderr:
            print(f"⚠️  错误: {result.stderr[:500]}")
    
    if check and result.returncode != 0:
        raise Exception(f"❌ 命令执行失败 (code: {result.returncode}): {cmd}\n{result.stderr}")
    
    return result

def main():
    print("🚀 开始主动同步文件流程")
    print("=" * 50)
    
    # 从环境变量获取token（在源仓库中执行，需要目标仓库的token）
    target_token = os.getenv('TARGET_REPO_TOKEN')
    
    if not target_token:
        print("❌ 错误: 需要设置 TARGET_REPO_TOKEN 环境变量")
        sys.exit(1)
    
    # 仓库配置
    source_repo = "https://github.com/jack2713/my.git"  # 当前仓库
    target_repo = "https://github.com/jack2713/mynew.git"  # 目标仓库
    source_file = "myq.txt"  # 源文件
    target_file = "my.txt"    # 目标文件
    branch = "main"          # 分支
    
    print(f"📁 源仓库: {source_repo}")
    print(f"🎯 目标仓库: {target_repo}")
    print(f"📄 源文件: {source_file}")
    print(f"📄 目标文件: {target_file}")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📂 临时工作目录: {temp_path}")
        
        try:
            # 1. 配置Git
            print("\n1. 🔧 配置Git...")
            run_cmd('git config --global user.email "github-actions@github.com"')
            run_cmd('git config --global user.name "GitHub Actions Bot"')
            
            # 2. 克隆目标仓库（需要目标仓库的token）
            print(f"\n2. 📥 克隆目标仓库...")
            target_dir = temp_path / "target"
            
            # 使用token认证克隆目标仓库
            target_auth = target_repo.replace('https://', f'https://{target_token}@')
            run_cmd(f'git clone --depth 1 --branch {branch} {target_auth} {target_dir}')
            
            # 3. 复制当前仓库的文件（直接从工作目录复制）
            print(f"\n3. 📋 复制源文件...")
            
            # 获取当前脚本所在目录（源仓库的工作目录）
            script_dir = Path(__file__).parent.absolute()
            source_file_path = script_dir / source_file
            
            if not source_file_path.exists():
                # 尝试从当前工作目录查找
                source_file_path = Path.cwd() / source_file
                if not source_file_path.exists():
                    # 在源仓库中查找文件
                    for root, dirs, files in os.walk('.'):
                        if source_file in files:
                            source_file_path = Path(root) / source_file
                            break
                    
                    if not source_file_path.exists():
                        print(f"❌ 错误: 找不到源文件 {source_file}")
                        print(f"当前目录内容: {os.listdir('.')}")
                        sys.exit(1)
            
            print(f"找到源文件: {source_file_path}")
            print(f"文件大小: {source_file_path.stat().st_size} 字节")
            
            # 读取源文件内容
            with open(source_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件内容预览 (前200字符):")
                print("-" * 40)
                print(content[:200])
                if len(content) > 200:
                    print("...")
                print("-" * 40)
            
            # 4. 写入目标仓库
            target_file_path = target_dir / target_file
            
            # 确保目标目录存在
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_file_path, target_file_path)
            print(f"✅ 文件已复制到: {target_file_path}")
            
            # 5. 提交更改到目标仓库
            print(f"\n4. 💾 提交更改到目标仓库...")
            os.chdir(target_dir)
            
            # 检查是否有更改
            result = run_cmd('git status --porcelain', check=False, verbose=False)
            
            if result.stdout.strip():
                print(f"检测到更改: {result.stdout}")
                
                # 添加文件
                run_cmd(f'git add {target_file}')
                
                # 提交
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                commit_msg = f"🔄 从源仓库同步 {source_file} -> {target_file} ({timestamp})"
                run_cmd(f'git commit -m "{commit_msg}"')
                
                # 推送
                print(f"5. 📤 推送到目标仓库...")
                run_cmd(f'git push origin {branch}')
                
                print("✅ 同步完成并已推送到目标仓库!")
            else:
                print("ℹ️  没有检测到文件更改，无需推送")
            
            print("\n" + "=" * 50)
            print("🎉 主动同步流程完成!")
            
        except Exception as e:
            print(f"\n❌ 同步过程中发生错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()
