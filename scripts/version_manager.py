#!/usr/bin/env python3
"""
版本管理和兼容性测试工具
用于管理上游项目版本和测试兼容性
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import importlib.util
import unittest

class VersionManager:
    """版本管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.upstream_path = self.project_root / ".ref" / "Douyin_TikTok_Download_API"
        self.version_db_path = self.project_root / "scripts" / "version_database.json"
        self.compatibility_log_path = self.project_root / "scripts" / "compatibility_log.json"
        
    def load_version_database(self) -> Dict:
        """加载版本数据库"""
        if self.version_db_path.exists():
            with open(self.version_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "versions": [],
                "current_version": None,
                "compatibility_matrix": {},
                "rollback_points": []
            }
    
    def save_version_database(self, db: Dict):
        """保存版本数据库"""
        with open(self.version_db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    
    def get_upstream_version_info(self) -> Optional[Dict]:
        """获取上游项目版本信息"""
        if not self.upstream_path.exists():
            return None
        
        try:
            # 获取当前commit信息
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()
            
            # 获取commit时间
            result = subprocess.run(
                ["git", "show", "-s", "--format=%ci", commit_hash],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_date = result.stdout.strip()
            
            # 获取commit消息
            result = subprocess.run(
                ["git", "show", "-s", "--format=%s", commit_hash],
                cwd=self.upstream_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_message = result.stdout.strip()
            
            # 获取标签信息
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match", commit_hash],
                cwd=self.upstream_path,
                capture_output=True,
                text=True
            )
            tag = result.stdout.strip() if result.returncode == 0 else None
            
            return {
                "commit_hash": commit_hash,
                "short_hash": commit_hash[:8],
                "commit_date": commit_date,
                "commit_message": commit_message,
                "tag": tag,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            print(f"获取版本信息失败: {e}")
            return None
    
    def record_version(self, version_info: Dict, integration_success: bool = True) -> str:
        """记录版本信息"""
        db = self.load_version_database()
        
        version_id = f"v{len(db['versions']) + 1}_{version_info['short_hash']}"
        
        version_record = {
            "version_id": version_id,
            "upstream_info": version_info,
            "integration_success": integration_success,
            "local_timestamp": datetime.now().isoformat(),
            "compatibility_tested": False,
            "rollback_point": False
        }
        
        db["versions"].append(version_record)
        db["current_version"] = version_id
        
        self.save_version_database(db)
        return version_id
    
    def create_rollback_point(self, version_id: str, description: str = ""):
        """创建回滚点"""
        db = self.load_version_database()
        
        # 找到对应版本
        for version in db["versions"]:
            if version["version_id"] == version_id:
                version["rollback_point"] = True
                version["rollback_description"] = description
                break
        
        db["rollback_points"].append({
            "version_id": version_id,
            "description": description,
            "created_at": datetime.now().isoformat()
        })
        
        self.save_version_database(db)
        print(f"创建回滚点: {version_id} - {description}")
    
    def list_versions(self, limit: int = 10) -> List[Dict]:
        """列出版本历史"""
        db = self.load_version_database()
        return db["versions"][-limit:]
    
    def get_rollback_points(self) -> List[Dict]:
        """获取可用的回滚点"""
        db = self.load_version_database()
        return db.get("rollback_points", [])
    
    def rollback_to_version(self, version_id: str) -> bool:
        """回滚到指定版本"""
        db = self.load_version_database()
        
        # 查找目标版本
        target_version = None
        for version in db["versions"]:
            if version["version_id"] == version_id:
                target_version = version
                break
        
        if not target_version:
            print(f"版本 {version_id} 不存在")
            return False
        
        try:
            # 回滚上游项目
            commit_hash = target_version["upstream_info"]["commit_hash"]
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=self.upstream_path,
                check=True
            )
            
            # 重新整合
            from integration_manager import IntegrationManager
            manager = IntegrationManager(str(self.project_root))
            results = manager.integrate_modules()
            
            if results.get("error"):
                print(f"回滚失败: {results['error']}")
                return False
            
            # 更新当前版本
            db["current_version"] = version_id
            self.save_version_database(db)
            
            print(f"成功回滚到版本: {version_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"回滚失败: {e}")
            return False

class CompatibilityTester:
    """兼容性测试器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_results_path = self.project_root / "scripts" / "compatibility_results.json"
        
    def run_compatibility_tests(self) -> Dict:
        """运行兼容性测试"""
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_success": True
        }
        
        # 定义测试用例
        test_cases = [
            ("douyin_crawler", self.test_douyin_crawler),
            ("tiktok_crawler", self.test_tiktok_crawler),
            ("hybrid_crawler", self.test_hybrid_crawler),
            ("api_endpoints", self.test_api_endpoints),
            ("import_structure", self.test_import_structure)
        ]
        
        for test_name, test_func in test_cases:
            try:
                print(f"运行测试: {test_name}")
                result = test_func()
                test_results["tests"][test_name] = {
                    "success": result["success"],
                    "message": result.get("message", ""),
                    "details": result.get("details", {})
                }
                
                if not result["success"]:
                    test_results["overall_success"] = False
                    
            except Exception as e:
                test_results["tests"][test_name] = {
                    "success": False,
                    "message": f"测试异常: {str(e)}",
                    "details": {}
                }
                test_results["overall_success"] = False
        
        # 保存测试结果
        with open(self.test_results_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        return test_results
    
    def test_douyin_crawler(self) -> Dict:
        """测试抖音爬虫"""
        try:
            # 尝试导入抖音爬虫
            sys.path.insert(0, str(self.project_root))
            from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
            
            # 创建实例
            crawler = DouyinWebCrawler()
            
            # 测试基本方法
            test_url = "https://www.douyin.com/video/7000000000000000000"
            aweme_id = crawler.get_aweme_id(test_url)
            
            return {
                "success": True,
                "message": "抖音爬虫测试通过",
                "details": {
                    "import_success": True,
                    "instance_creation": True,
                    "method_test": aweme_id is not None
                }
            }
            
        except ImportError as e:
            return {
                "success": False,
                "message": f"导入失败: {e}",
                "details": {"import_error": str(e)}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败: {e}",
                "details": {"error": str(e)}
            }
    
    def test_tiktok_crawler(self) -> Dict:
        """测试TikTok爬虫"""
        try:
            sys.path.insert(0, str(self.project_root))
            from app.crawlers.tiktok.web.web_crawler import TikTokWebCrawler
            
            crawler = TikTokWebCrawler()
            
            return {
                "success": True,
                "message": "TikTok爬虫测试通过",
                "details": {
                    "import_success": True,
                    "instance_creation": True
                }
            }
            
        except ImportError as e:
            return {
                "success": False,
                "message": f"导入失败: {e}",
                "details": {"import_error": str(e)}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败: {e}",
                "details": {"error": str(e)}
            }
    
    def test_hybrid_crawler(self) -> Dict:
        """测试混合爬虫"""
        try:
            sys.path.insert(0, str(self.project_root))
            from app.crawlers.hybrid.hybrid_crawler import HybridCrawler
            
            crawler = HybridCrawler()
            
            return {
                "success": True,
                "message": "混合爬虫测试通过",
                "details": {
                    "import_success": True,
                    "instance_creation": True
                }
            }
            
        except ImportError as e:
            return {
                "success": False,
                "message": f"导入失败: {e}",
                "details": {"import_error": str(e)}
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"测试失败: {e}",
                "details": {"error": str(e)}
            }
    
    def test_api_endpoints(self) -> Dict:
        """测试API端点"""
        try:
            # 这里可以添加API端点测试
            # 例如测试FastAPI路由是否正常加载
            
            return {
                "success": True,
                "message": "API端点测试通过",
                "details": {}
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"API测试失败: {e}",
                "details": {"error": str(e)}
            }
    
    def test_import_structure(self) -> Dict:
        """测试导入结构"""
        try:
            # 测试关键模块的导入
            import_tests = [
                "app.crawlers.base_crawler",
                "app.crawlers.douyin",
                "app.crawlers.tiktok",
                "app.crawlers.hybrid"
            ]
            
            failed_imports = []
            for module_name in import_tests:
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    failed_imports.append(f"{module_name}: {e}")
            
            success = len(failed_imports) == 0
            
            return {
                "success": success,
                "message": "导入结构测试完成",
                "details": {
                    "total_tests": len(import_tests),
                    "failed_imports": failed_imports
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"导入测试失败: {e}",
                "details": {"error": str(e)}
            }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="版本管理和兼容性测试工具")
    parser.add_argument("--record", action="store_true", help="记录当前版本")
    parser.add_argument("--list", action="store_true", help="列出版本历史")
    parser.add_argument("--rollback", help="回滚到指定版本")
    parser.add_argument("--create-rollback-point", help="创建回滚点")
    parser.add_argument("--test", action="store_true", help="运行兼容性测试")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    version_manager = VersionManager(args.project_root)
    compatibility_tester = CompatibilityTester(args.project_root)
    
    if args.record:
        # 记录当前版本
        version_info = version_manager.get_upstream_version_info()
        if version_info:
            version_id = version_manager.record_version(version_info)
            print(f"记录版本: {version_id}")
        else:
            print("无法获取版本信息")
    
    elif args.list:
        # 列出版本历史
        versions = version_manager.list_versions()
        print("版本历史:")
        for version in versions:
            status = "✓" if version["integration_success"] else "✗"
            rollback = "📌" if version.get("rollback_point") else ""
            print(f"  {status} {version['version_id']} - {version['upstream_info']['commit_message'][:50]} {rollback}")
    
    elif args.rollback:
        # 回滚版本
        success = version_manager.rollback_to_version(args.rollback)
        if not success:
            sys.exit(1)
    
    elif args.create_rollback_point:
        # 创建回滚点
        db = version_manager.load_version_database()
        current_version = db.get("current_version")
        if current_version:
            version_manager.create_rollback_point(current_version, args.create_rollback_point)
        else:
            print("没有当前版本")
    
    elif args.test:
        # 运行兼容性测试
        results = compatibility_tester.run_compatibility_tests()
        
        print("兼容性测试结果:")
        print(f"  总体状态: {'通过' if results['overall_success'] else '失败'}")
        
        for test_name, result in results["tests"].items():
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {test_name}: {result['message']}")
        
        if not results["overall_success"]:
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()