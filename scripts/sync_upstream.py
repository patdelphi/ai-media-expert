#!/usr/bin/env python3
"""
上游项目同步脚本
用于跟踪和同步 Douyin_TikTok_Download_API 项目的更新
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class UpstreamSyncManager:
    """上游项目同步管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.upstream_path = self.project_root / ".ref" / "Douyin_TikTok_Download_API"
        self.sync_config_path = self.project_root / "scripts" / "sync_config.json"
        self.version_log_path = self.project_root / "scripts" / "upstream_versions.json"
        
    def load_sync_config(self) -> Dict:
        """加载同步配置"""
        default_config = {
            "upstream_repo": "https://github.com/Evil0ctal/Douyin_TikTok_Download_API.git",
            "sync_branch": "main",
            "watch_files": [
                "crawlers/",
                "app/api/endpoints/",
                "requirements.txt",
                "config.yaml"
            ],
            "ignore_patterns": [
                "*.pyc",
                "__pycache__/",
                ".git/",
                "logs/",
                "temp/"
            ]
        }
        
        if self.sync_config_path.exists():
            with open(self.sync_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # 创建默认配置文件
            with open(self.sync_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def get_current_version(self) -> Optional[str]:
        """获取当前上游项目版本"""
        if not self.upstream_path.exists():
            return None
            
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def check_for_updates(self) -> Dict:
        """检查上游项目更新"""
        config = self.load_sync_config()
        
        # 确保上游项目存在
        if not self.upstream_path.exists():
            print("上游项目不存在，正在克隆...")
            self.clone_upstream()
        
        # 获取当前版本
        current_version = self.get_current_version()
        
        # 拉取最新更新
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.upstream_path,
                check=True
            )
            
            # 获取远程最新版本
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{config['sync_branch']}"],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            latest_version = result.stdout.strip()
            
            # 检查是否有更新
            has_updates = current_version != latest_version
            
            # 获取更新日志
            update_log = []
            if has_updates and current_version:
                try:
                    result = subprocess.run(
                        ["git", "log", f"{current_version}..{latest_version}", "--oneline"],
                        cwd=self.upstream_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    update_log = result.stdout.strip().split('\n') if result.stdout.strip() else []
                except subprocess.CalledProcessError:
                    update_log = ["无法获取更新日志"]
            
            return {
                "has_updates": has_updates,
                "current_version": current_version,
                "latest_version": latest_version,
                "update_log": update_log,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "error": f"检查更新失败: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def clone_upstream(self):
        """克隆上游项目"""
        config = self.load_sync_config()
        
        # 确保.ref目录存在
        self.upstream_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            subprocess.run(
                ["git", "clone", config["upstream_repo"], str(self.upstream_path)],
                check=True
            )
            print(f"成功克隆上游项目到 {self.upstream_path}")
        except subprocess.CalledProcessError as e:
            print(f"克隆上游项目失败: {e}")
            sys.exit(1)
    
    def sync_upstream(self, auto_merge: bool = False) -> Dict:
        """同步上游项目更新"""
        update_info = self.check_for_updates()
        
        if update_info.get("error"):
            return update_info
        
        if not update_info["has_updates"]:
            print("上游项目无更新")
            return update_info
        
        print(f"发现上游项目更新:")
        for log_entry in update_info["update_log"]:
            print(f"  - {log_entry}")
        
        if not auto_merge:
            response = input("是否继续同步更新? (y/N): ")
            if response.lower() != 'y':
                print("取消同步")
                return update_info
        
        try:
            # 拉取并合并更新
            config = self.load_sync_config()
            subprocess.run(
                ["git", "pull", "origin", config["sync_branch"]],
                cwd=self.upstream_path,
                check=True
            )
            
            # 记录版本信息
            self.log_version_update(update_info)
            
            print("上游项目同步完成")
            update_info["sync_success"] = True
            
            return update_info
            
        except subprocess.CalledProcessError as e:
            error_msg = f"同步失败: {e}"
            print(error_msg)
            update_info["sync_error"] = error_msg
            return update_info
    
    def log_version_update(self, update_info: Dict):
        """记录版本更新日志"""
        version_log = []
        
        if self.version_log_path.exists():
            with open(self.version_log_path, 'r', encoding='utf-8') as f:
                version_log = json.load(f)
        
        version_log.append({
            "timestamp": update_info["timestamp"],
            "from_version": update_info["current_version"],
            "to_version": update_info["latest_version"],
            "update_log": update_info["update_log"]
        })
        
        # 只保留最近50次更新记录
        version_log = version_log[-50:]
        
        with open(self.version_log_path, 'w', encoding='utf-8') as f:
            json.dump(version_log, f, indent=2, ensure_ascii=False)
    
    def get_changed_files(self, from_version: str, to_version: str) -> List[str]:
        """获取版本间变更的文件列表"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", from_version, to_version],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="上游项目同步工具")
    parser.add_argument("--check", action="store_true", help="仅检查更新，不同步")
    parser.add_argument("--auto", action="store_true", help="自动同步，无需确认")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    sync_manager = UpstreamSyncManager(args.project_root)
    
    if args.check:
        # 仅检查更新
        update_info = sync_manager.check_for_updates()
        if update_info.get("error"):
            print(f"错误: {update_info['error']}")
            sys.exit(1)
        
        if update_info["has_updates"]:
            print("发现上游项目更新:")
            for log_entry in update_info["update_log"]:
                print(f"  - {log_entry}")
        else:
            print("上游项目无更新")
    else:
        # 同步更新
        result = sync_manager.sync_upstream(auto_merge=args.auto)
        if result.get("error") or result.get("sync_error"):
            sys.exit(1)

if __name__ == "__main__":
    main()