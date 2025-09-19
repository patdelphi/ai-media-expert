#!/usr/bin/env python3
"""数据库自动配置脚本

独立运行的数据库配置脚本，用于初始化和检查数据库环境。
可以在应用启动前运行，确保数据库环境正确配置。
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.db_manager import db_manager, ensure_database_ready, get_database_status
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_database_status():
    """打印数据库状态信息"""
    print("\n" + "="*60)
    print("数据库状态检查")
    print("="*60)
    
    status = get_database_status()
    
    print(f"数据库类型: {status['database_type']}")
    print(f"数据库URL: {status['database_url']}")
    print(f"数据库存在: {'✅' if status['database_exists'] else '❌'}")
    
    if 'database_file' in status:
        print(f"数据库文件: {status['database_file']}")
        print(f"文件大小: {status['file_size']} 字节")
    
    print("\n表结构状态:")
    for table, exists in status['tables'].items():
        status_icon = "✅" if exists else "❌"
        print(f"  {table}: {status_icon}")
    
    print("="*60)


def setup_database():
    """设置数据库"""
    print("\n🚀 开始数据库自动配置...")
    
    try:
        success = ensure_database_ready()
        
        if success:
            print("✅ 数据库配置完成!")
            print("\n默认管理员账户:")
            print("  邮箱: admin@example.com")
            print("  密码: admin123")
            print("\n⚠️  请在生产环境中修改默认密码!")
        else:
            print("❌ 数据库配置失败!")
            return False
            
    except Exception as e:
        print(f"❌ 数据库配置过程中发生错误: {e}")
        logger.exception("数据库配置失败")
        return False
    
    return True


def check_environment():
    """检查环境配置"""
    print("\n🔍 检查环境配置...")
    
    # 检查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 未找到.env配置文件")
        print("请复制.env.example为.env并配置相关参数")
        return False
    
    print("✅ .env文件存在")
    
    # 检查必要的环境变量
    required_vars = [
        "DATABASE_URL", "SECRET_KEY", "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        return False
    
    print("✅ 环境变量配置正确")
    return True


def backup_database():
    """备份数据库"""
    print("\n💾 备份数据库...")
    
    if db_manager.backup_database():
        print("✅ 数据库备份完成")
        return True
    else:
        print("❌ 数据库备份失败")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库自动配置工具")
    parser.add_argument(
        "--action", 
        choices=["setup", "status", "check", "backup"],
        default="setup",
        help="执行的操作 (默认: setup)"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="强制执行操作，跳过确认"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🎯 AI新媒体专家系统 - 数据库配置工具")
    print(f"环境: {settings.environment}")
    
    try:
        if args.action == "status":
            print_database_status()
            
        elif args.action == "check":
            env_ok = check_environment()
            print_database_status()
            
            if env_ok and get_database_status()['database_exists']:
                print("\n✅ 环境检查通过")
                sys.exit(0)
            else:
                print("\n❌ 环境检查失败")
                sys.exit(1)
                
        elif args.action == "backup":
            if backup_database():
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.action == "setup":
            # 检查环境
            if not check_environment():
                print("\n请先修复环境配置问题")
                sys.exit(1)
            
            # 显示当前状态
            print_database_status()
            
            # 确认执行
            if not args.force:
                response = input("\n是否继续数据库配置? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("操作已取消")
                    sys.exit(0)
            
            # 执行配置
            if setup_database():
                print_database_status()
                print("\n🎉 数据库配置完成! 现在可以启动应用了。")
                sys.exit(0)
            else:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        logger.exception("脚本执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()