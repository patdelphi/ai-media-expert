#!/usr/bin/env python3
"""
代码整合管理器
用于管理 Douyin_TikTok_Download_API 项目的模块化集成
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
import importlib.util

class IntegrationManager:
    """代码整合管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.upstream_path = self.project_root / ".ref" / "Douyin_TikTok_Download_API"
        self.target_crawlers_path = self.project_root / "app" / "crawlers"
        self.integration_config_path = self.project_root / "scripts" / "integration_config.json"
        self.mapping_log_path = self.project_root / "scripts" / "integration_mapping.json"
        
    def load_integration_config(self) -> Dict:
        """加载整合配置"""
        default_config = {
            "module_mappings": {
                # 上游路径 -> 本地路径的映射
                "crawlers/douyin/web/web_crawler.py": "app/crawlers/douyin/web/web_crawler.py",
                "crawlers/tiktok/web/web_crawler.py": "app/crawlers/tiktok/web/web_crawler.py",
                "crawlers/tiktok/app/app_crawler.py": "app/crawlers/tiktok/app/app_crawler.py",
                "crawlers/hybrid/hybrid_crawler.py": "app/crawlers/hybrid/hybrid_crawler.py",
                "crawlers/base_crawler.py": "app/crawlers/base_crawler.py",
                "crawlers/utils/": "app/crawlers/utils/"
            },
            "namespace_mapping": {
                # 命名空间重映射，避免冲突
                "crawlers": "app.crawlers"
            },
            "dependency_overrides": {
                # 依赖覆盖，使用本地版本
                "config": "app.core.config",
                "utils": "app.utils"
            },
            "exclude_files": [
                # 排除不需要的文件
                "__pycache__/",
                "*.pyc",
                ".git/",
                "logs/",
                "temp/",
                "start.py",
                "config.yaml"
            ],
            "custom_adapters": {
                # 自定义适配器，处理接口差异
                "DouyinWebCrawler": "app.crawlers.douyin.web.web_crawler.DouyinWebCrawler",
                "TikTokWebCrawler": "app.crawlers.tiktok.web.web_crawler.TikTokWebCrawler"
            }
        }
        
        if self.integration_config_path.exists():
            with open(self.integration_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # 创建默认配置文件
            with open(self.integration_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def analyze_dependencies(self, file_path: Path) -> Dict:
        """分析文件依赖关系"""
        dependencies = {
            "imports": [],
            "from_imports": [],
            "relative_imports": [],
            "external_deps": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # 分析import语句
                if line.startswith('import '):
                    module = line[7:].split(' as ')[0].split('.')[0]
                    dependencies["imports"].append(module)
                
                elif line.startswith('from '):
                    if ' import ' in line:
                        module_part = line.split(' import ')[0][5:]
                        if module_part.startswith('.'):
                            dependencies["relative_imports"].append(module_part)
                        else:
                            dependencies["from_imports"].append(module_part.split('.')[0])
            
            return dependencies
            
        except Exception as e:
            print(f"分析依赖失败 {file_path}: {e}")
            return dependencies
    
    def create_adapter_wrapper(self, source_file: Path, target_file: Path, config: Dict):
        """创建适配器包装器"""
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_content = f.read()
            
            # 分析依赖
            deps = self.analyze_dependencies(source_file)
            
            # 生成适配后的代码
            adapted_content = self.adapt_imports(source_content, config)
            adapted_content = self.adapt_namespaces(adapted_content, config)
            
            # 确保目标目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入适配后的代码
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(f'"""\n适配自上游项目: {source_file.relative_to(self.upstream_path)}\n"""\n\n')
                f.write(adapted_content)
            
            print(f"创建适配器: {source_file} -> {target_file}")
            return True
            
        except Exception as e:
            print(f"创建适配器失败: {e}")
            return False
    
    def adapt_imports(self, content: str, config: Dict) -> str:
        """适配import语句"""
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            original_line = line
            
            # 处理from imports
            if line.strip().startswith('from '):
                for old_ns, new_ns in config.get("namespace_mapping", {}).items():
                    if f'from {old_ns}' in line:
                        line = line.replace(f'from {old_ns}', f'from {new_ns}')
                
                # 处理依赖覆盖
                for old_dep, new_dep in config.get("dependency_overrides", {}).items():
                    if f'from {old_dep}' in line:
                        line = line.replace(f'from {old_dep}', f'from {new_dep}')
            
            # 处理import语句
            elif line.strip().startswith('import '):
                for old_ns, new_ns in config.get("namespace_mapping", {}).items():
                    if f'import {old_ns}' in line:
                        line = line.replace(f'import {old_ns}', f'import {new_ns}')
            
            adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)
    
    def adapt_namespaces(self, content: str, config: Dict) -> str:
        """适配命名空间引用"""
        # 这里可以添加更复杂的命名空间适配逻辑
        # 例如替换类名、函数名等
        
        for old_adapter, new_adapter in config.get("custom_adapters", {}).items():
            # 简单的类名替换示例
            if old_adapter in content:
                content = content.replace(
                    f'class {old_adapter}',
                    f'class {old_adapter}Adapted'
                )
        
        return content
    
    def should_exclude_file(self, file_path: Path, config: Dict) -> bool:
        """检查文件是否应该被排除"""
        exclude_patterns = config.get("exclude_files", [])
        
        for pattern in exclude_patterns:
            if pattern.endswith('/'):
                # 目录模式
                if pattern[:-1] in str(file_path):
                    return True
            elif '*' in pattern:
                # 通配符模式
                import fnmatch
                if fnmatch.fnmatch(file_path.name, pattern):
                    return True
            else:
                # 精确匹配
                if pattern in str(file_path):
                    return True
        
        return False
    
    def integrate_modules(self, dry_run: bool = False) -> Dict:
        """整合模块"""
        config = self.load_integration_config()
        results = {
            "success": [],
            "failed": [],
            "skipped": [],
            "conflicts": []
        }
        
        if not self.upstream_path.exists():
            return {"error": "上游项目不存在，请先运行同步脚本"}
        
        # 处理模块映射
        for upstream_path, local_path in config["module_mappings"].items():
            source_path = self.upstream_path / upstream_path
            target_path = self.project_root / local_path
            
            if not source_path.exists():
                results["skipped"].append(f"源文件不存在: {upstream_path}")
                continue
            
            # 检查是否排除
            if self.should_exclude_file(source_path, config):
                results["skipped"].append(f"文件被排除: {upstream_path}")
                continue
            
            # 检查冲突
            if target_path.exists() and not dry_run:
                # 备份现有文件
                backup_path = target_path.with_suffix(f"{target_path.suffix}.backup")
                shutil.copy2(target_path, backup_path)
                results["conflicts"].append(f"备份冲突文件: {local_path}")
            
            if dry_run:
                print(f"[DRY RUN] 将整合: {upstream_path} -> {local_path}")
                results["success"].append(f"[DRY RUN] {upstream_path}")
            else:
                # 执行整合
                if source_path.is_dir():
                    success = self.integrate_directory(source_path, target_path, config)
                else:
                    success = self.create_adapter_wrapper(source_path, target_path, config)
                
                if success:
                    results["success"].append(upstream_path)
                else:
                    results["failed"].append(upstream_path)
        
        # 记录整合映射
        if not dry_run:
            self.log_integration_mapping(results)
        
        return results
    
    def integrate_directory(self, source_dir: Path, target_dir: Path, config: Dict) -> bool:
        """整合目录"""
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for item in source_dir.rglob('*'):
                if item.is_file() and not self.should_exclude_file(item, config):
                    relative_path = item.relative_to(source_dir)
                    target_file = target_dir / relative_path
                    
                    if item.suffix == '.py':
                        # Python文件需要适配
                        self.create_adapter_wrapper(item, target_file, config)
                    else:
                        # 其他文件直接复制
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_file)
            
            return True
            
        except Exception as e:
            print(f"整合目录失败: {e}")
            return False
    
    def log_integration_mapping(self, results: Dict):
        """记录整合映射"""
        mapping_data = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "results": results,
            "config_version": "1.0"
        }
        
        with open(self.mapping_log_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    
    def check_integration_status(self) -> Dict:
        """检查整合状态"""
        config = self.load_integration_config()
        status = {
            "integrated_modules": [],
            "missing_modules": [],
            "outdated_modules": []
        }
        
        for upstream_path, local_path in config["module_mappings"].items():
            target_path = self.project_root / local_path
            
            if target_path.exists():
                status["integrated_modules"].append(local_path)
            else:
                status["missing_modules"].append(local_path)
        
        return status

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="代码整合管理工具")
    parser.add_argument("--integrate", action="store_true", help="执行模块整合")
    parser.add_argument("--dry-run", action="store_true", help="预览整合操作，不实际执行")
    parser.add_argument("--status", action="store_true", help="检查整合状态")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    manager = IntegrationManager(args.project_root)
    
    if args.status:
        # 检查状态
        status = manager.check_integration_status()
        print("整合状态:")
        print(f"  已整合模块: {len(status['integrated_modules'])}")
        print(f"  缺失模块: {len(status['missing_modules'])}")
        
        if status['missing_modules']:
            print("  缺失的模块:")
            for module in status['missing_modules']:
                print(f"    - {module}")
    
    elif args.integrate or args.dry_run:
        # 执行整合
        results = manager.integrate_modules(dry_run=args.dry_run)
        
        if results.get("error"):
            print(f"错误: {results['error']}")
            sys.exit(1)
        
        print("整合结果:")
        print(f"  成功: {len(results['success'])}")
        print(f"  失败: {len(results['failed'])}")
        print(f"  跳过: {len(results['skipped'])}")
        print(f"  冲突: {len(results['conflicts'])}")
        
        if results['failed']:
            print("  失败的模块:")
            for module in results['failed']:
                print(f"    - {module}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()