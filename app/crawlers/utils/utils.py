"""爬虫通用工具函数

提供URL提取、验证等通用功能。
"""

import re
from typing import List
from urllib.parse import urlparse


def extract_valid_urls(text: str) -> List[str]:
    """从文本中提取有效的URL
    
    Args:
        text: 包含URL的文本
        
    Returns:
        List[str]: 提取到的有效URL列表
    """
    # URL正则表达式模式
    url_pattern = r'https?://[^\s<>"\[\]{}|\\^`]+'
    
    # 提取所有匹配的URL
    urls = re.findall(url_pattern, text)
    
    # 验证和清理URL
    valid_urls = []
    for url in urls:
        try:
            # 解析URL
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                # 移除末尾的标点符号
                cleaned_url = url.rstrip('.,;:!?')
                valid_urls.append(cleaned_url)
        except Exception:
            continue
    
    return valid_urls


def is_valid_url(url: str) -> bool:
    """验证URL是否有效
    
    Args:
        url: 要验证的URL
        
    Returns:
        bool: URL是否有效
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def extract_domain(url: str) -> str:
    """从URL中提取域名
    
    Args:
        url: URL地址
        
    Returns:
        str: 域名
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ''


def is_douyin_url(url: str) -> bool:
    """判断是否为抖音URL
    
    Args:
        url: URL地址
        
    Returns:
        bool: 是否为抖音URL
    """
    domain = extract_domain(url)
    douyin_domains = ['douyin.com', 'iesdouyin.com', 'v.douyin.com']
    return any(domain.endswith(d) for d in douyin_domains)


def is_tiktok_url(url: str) -> bool:
    """判断是否为TikTok URL
    
    Args:
        url: URL地址
        
    Returns:
        bool: 是否为TikTok URL
    """
    domain = extract_domain(url)
    tiktok_domains = ['tiktok.com', 'vm.tiktok.com', 't.tiktok.com']
    return any(domain.endswith(d) for d in tiktok_domains)


def is_bilibili_url(url: str) -> bool:
    """判断是否为B站URL
    
    Args:
        url: URL地址
        
    Returns:
        bool: 是否为B站URL
    """
    domain = extract_domain(url)
    bilibili_domains = ['bilibili.com', 'b23.tv']
    return any(domain.endswith(d) for d in bilibili_domains)