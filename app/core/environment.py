#!/usr/bin/env python3
"""环境检测和自动创建功能模块

提供环境配置检测、目录创建、依赖检查等功能。
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化环境管理器
        
        Args:
            project_root: 项目根目录，默认为当前文件的父目录
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.required_dirs = [
            "uploads", "downloads", "models", "logs", 
            "temp", "cache", "backups"
        ]
        self.required_packages = {
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'sqlalchemy': 'sqlalchemy',
            'alembic': 'alembic',
            'celery': 'celery',
            'redis': 'redis',
            'gradio': 'gradio',
            'yt-dlp': 'yt_dlp',
            'opencv-python': 'cv2',
            'pillow': 'PIL',
            'requests': 'requests',
            'python-multipart': 'multipart',
            'python-jose': 'jose',
            'passlib': 'passlib',
            'bcrypt': 'bcrypt'
        }
    
    def check_python_version(self) -> Tuple[bool, str]:
        """检查Python版本
        
        Returns:
            (是否满足要求, 版本信息)
        """
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            return True, f"Python {sys.version.split()[0]}"
        else:
            return False, f"需要Python {min_version[0]}.{min_version[1]}+，当前版本: {sys.version.split()[0]}"
    
    def check_dependencies(self) -> Tuple[bool, List[str], List[str]]:
        """检查依赖包
        
        Returns:
            (是否全部满足, 已安装包列表, 缺失包列表)
        """
        installed = []
        missing = []
        
        for package_name, import_name in self.required_packages.items():
            try:
                __import__(import_name)
                installed.append(package_name)
            except ImportError:
                missing.append(package_name)
        
        return len(missing) == 0, installed, missing
    
    def check_env_file(self) -> Tuple[bool, str]:
        """检查环境配置文件
        
        Returns:
            (是否存在, 状态信息)
        """
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            return True, "环境配置文件存在"
        elif env_example.exists():
            return False, "环境配置文件不存在，但找到示例文件"
        else:
            return False, "环境配置文件和示例文件都不存在"
    
    def create_env_file(self) -> bool:
        """创建环境配置文件
        
        Returns:
            是否创建成功
        """
        try:
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if env_file.exists():
                logger.info("环境配置文件已存在")
                return True
            
            if env_example.exists():
                # 复制示例文件
                shutil.copy2(env_example, env_file)
                logger.info("已从示例文件创建环境配置文件")
                return True
            else:
                # 创建基本的环境配置文件
                default_config = """# AI新媒体专家系统配置文件

# 应用配置
APP_NAME=AI新媒体专家系统
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./ai_media_expert.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件存储配置
UPLOAD_DIR=uploads
DOWNLOAD_DIR=downloads
MAX_FILE_SIZE=100MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
                env_file.write_text(default_config, encoding='utf-8')
                logger.info("已创建默认环境配置文件")
                return True
                
        except Exception as e:
            logger.error(f"创建环境配置文件失败: {e}")
            return False
    
    def create_directories(self) -> Tuple[bool, List[str], List[str]]:
        """创建必要的目录
        
        Returns:
            (是否全部创建成功, 成功创建的目录, 创建失败的目录)
        """
        created = []
        failed = []
        
        for dir_name in self.required_dirs:
            try:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(exist_ok=True)
                created.append(dir_name)
                logger.debug(f"目录创建成功: {dir_name}")
            except Exception as e:
                failed.append(dir_name)
                logger.error(f"目录创建失败 {dir_name}: {e}")
        
        return len(failed) == 0, created, failed
    
    def check_external_services(self) -> Dict[str, Tuple[bool, str]]:
        """检查外部服务状态
        
        Returns:
            服务状态字典 {服务名: (是否可用, 状态信息)}
        """
        services = {}
        
        # 检查Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
            r.ping()
            services['redis'] = (True, "Redis连接正常")
        except Exception as e:
            services['redis'] = (False, f"Redis连接失败: {e}")
        
        # 检查FFmpeg
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                services['ffmpeg'] = (True, f"FFmpeg可用: {version_line}")
            else:
                services['ffmpeg'] = (False, "FFmpeg不可用")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            services['ffmpeg'] = (False, f"FFmpeg检查失败: {e}")
        
        return services
    
    def install_dependencies(self, missing_packages: List[str]) -> Tuple[bool, str]:
        """安装缺失的依赖包
        
        Args:
            missing_packages: 缺失的包列表
            
        Returns:
            (是否安装成功, 安装信息)
        """
        if not missing_packages:
            return True, "无需安装依赖包"
        
        try:
            # 检查是否存在requirements.txt
            requirements_file = self.project_root / "requirements.txt"
            
            if requirements_file.exists():
                # 使用requirements.txt安装
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True, "依赖包安装成功"
                else:
                    return False, f"依赖包安装失败: {result.stderr}"
            else:
                # 直接安装缺失的包
                cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True, f"成功安装: {', '.join(missing_packages)}"
                else:
                    return False, f"安装失败: {result.stderr}"
                    
        except subprocess.TimeoutExpired:
            return False, "安装超时"
        except Exception as e:
            return False, f"安装异常: {e}"
    
    def setup_environment(self, auto_install: bool = False) -> Dict[str, any]:
        """设置完整环境
        
        Args:
            auto_install: 是否自动安装缺失的依赖
            
        Returns:
            环境设置结果字典
        """
        results = {
            'python_version': {'status': False, 'message': ''},
            'dependencies': {'status': False, 'installed': [], 'missing': []},
            'env_file': {'status': False, 'message': ''},
            'directories': {'status': False, 'created': [], 'failed': []},
            'external_services': {},
            'overall_status': False
        }
        
        # 1. 检查Python版本
        python_ok, python_msg = self.check_python_version()
        results['python_version'] = {'status': python_ok, 'message': python_msg}
        
        if not python_ok:
            results['overall_status'] = False
            return results
        
        # 2. 检查依赖包
        deps_ok, installed, missing = self.check_dependencies()
        results['dependencies'] = {
            'status': deps_ok, 
            'installed': installed, 
            'missing': missing
        }
        
        # 如果有缺失的依赖且允许自动安装
        if missing and auto_install:
            install_ok, install_msg = self.install_dependencies(missing)
            if install_ok:
                # 重新检查依赖
                deps_ok, installed, missing = self.check_dependencies()
                results['dependencies'] = {
                    'status': deps_ok, 
                    'installed': installed, 
                    'missing': missing,
                    'install_message': install_msg
                }
        
        # 3. 检查和创建环境配置文件
        env_ok, env_msg = self.check_env_file()
        if not env_ok:
            env_created = self.create_env_file()
            env_ok = env_created
            env_msg = "环境配置文件已创建" if env_created else "环境配置文件创建失败"
        
        results['env_file'] = {'status': env_ok, 'message': env_msg}
        
        # 4. 创建必要目录
        dirs_ok, created, failed = self.create_directories()
        results['directories'] = {
            'status': dirs_ok, 
            'created': created, 
            'failed': failed
        }
        
        # 5. 检查外部服务
        services = self.check_external_services()
        results['external_services'] = services
        
        # 6. 计算总体状态
        results['overall_status'] = (
            python_ok and 
            deps_ok and 
            env_ok and 
            dirs_ok
        )
        
        return results
    
    def print_environment_report(self, results: Dict[str, any]) -> None:
        """打印环境检查报告
        
        Args:
            results: setup_environment返回的结果字典
        """
        print("\n" + "="*60)
        print("🔍 环境检查报告")
        print("="*60)
        
        # Python版本
        python_status = "✅" if results['python_version']['status'] else "❌"
        print(f"{python_status} Python版本: {results['python_version']['message']}")
        
        # 依赖包
        deps = results['dependencies']
        deps_status = "✅" if deps['status'] else "❌"
        print(f"{deps_status} 依赖包检查: {len(deps['installed'])}个已安装")
        
        if deps['missing']:
            print(f"   ❌ 缺失包: {', '.join(deps['missing'])}")
        
        if 'install_message' in deps:
            print(f"   📦 安装结果: {deps['install_message']}")
        
        # 环境配置文件
        env_status = "✅" if results['env_file']['status'] else "❌"
        print(f"{env_status} 环境配置: {results['env_file']['message']}")
        
        # 目录创建
        dirs = results['directories']
        dirs_status = "✅" if dirs['status'] else "❌"
        print(f"{dirs_status} 目录创建: {len(dirs['created'])}个成功")
        
        if dirs['failed']:
            print(f"   ❌ 创建失败: {', '.join(dirs['failed'])}")
        
        # 外部服务
        print("\n🔗 外部服务状态:")
        for service, (status, message) in results['external_services'].items():
            service_status = "✅" if status else "⚠️"
            print(f"   {service_status} {service}: {message}")
        
        # 总体状态
        overall_status = "✅ 通过" if results['overall_status'] else "❌ 失败"
        print(f"\n🎯 总体状态: {overall_status}")
        print("="*60)


def ensure_environment_ready(auto_install: bool = False) -> bool:
    """确保环境准备就绪
    
    Args:
        auto_install: 是否自动安装缺失的依赖
        
    Returns:
        环境是否准备就绪
    """
    manager = EnvironmentManager()
    results = manager.setup_environment(auto_install=auto_install)
    manager.print_environment_report(results)
    
    return results['overall_status']


if __name__ == "__main__":
    # 命令行使用示例
    import argparse
    
    parser = argparse.ArgumentParser(description="环境检查和设置工具")
    parser.add_argument(
        "--auto-install", 
        action="store_true", 
        help="自动安装缺失的依赖包"
    )
    
    args = parser.parse_args()
    
    success = ensure_environment_ready(auto_install=args.auto_install)
    sys.exit(0 if success else 1)