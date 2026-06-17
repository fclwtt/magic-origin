#!/usr/bin/env python3
"""
文件操作工具 - 跨平台兼容

从 Hermes file_tools.py 精简，保留核心功能：
- 读取文件
- 写入文件
- 列出目录
- 跨平台路径处理
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def read_file(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    读取文件内容
    
    Args:
        path: 文件路径
        encoding: 文件编码
    
    Returns:
        {
            "success": bool,
            "content": str,
            "error": str (if failed)
        }
    """
    """Read content from a file."""
    
    try:
        file_path = Path(path).expanduser().resolve()
        
        if not file_path.exists():
            return {
                "success": False,
                "content": "",
                "error": f"文件不存在: {path}"
            }
        
        if not file_path.is_file():
            return {
                "success": False,
                "content": "",
                "error": f"不是文件: {path}"
            }
        
        content = file_path.read_text(encoding=encoding)
        
        return {
            "success": True,
            "content": content,
            "error": None
        }
    
    except UnicodeDecodeError:
        return {
            "success": False,
            "content": "",
            "error": f"编码错误，尝试使用 {encoding} 读取"
        }
    
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def write_file(path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    写入文件
    
    Args:
        path: 文件路径
        content: 文件内容
        encoding: 文件编码
    
    Returns:
        {
            "success": bool,
            "error": str (if failed)
        }
    """
    """Write content to a file."""
    
    try:
        file_path = Path(path).expanduser().resolve()
        
        # 创建父目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        file_path.write_text(content, encoding=encoding)
        
        return {
            "success": True,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def list_files(
    path: str = ".",
    pattern: str = "*",
    recursive: bool = False
) -> Dict[str, Any]:
    """
    列出目录内容
    
    Args:
        path: 目录路径
        pattern: 匹配模式（如 *.txt）
        recursive: 是否递归
    
    Returns:
        {
            "success": bool,
            "files": list,
            "error": str (if failed)
        }
    """
    """List files in a directory."""
    
    try:
        dir_path = Path(path).expanduser().resolve()
        
        if not dir_path.exists():
            return {
                "success": False,
                "files": [],
                "error": f"目录不存在: {path}"
            }
        
        if not dir_path.is_dir():
            return {
                "success": False,
                "files": [],
                "error": f"不是目录: {path}"
            }
        
        # 列出文件
        if recursive:
            files = [str(p) for p in dir_path.rglob(pattern)]
        else:
            files = [str(p) for p in dir_path.glob(pattern)]
        
        # 排序并限制数量
        files = sorted(files)[:100]
        
        return {
            "success": True,
            "files": files,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        return {
            "success": False,
            "files": [],
            "error": str(e)
        }


def get_file_info(path: str) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        path: 文件路径
    
    Returns:
        文件信息字典
    """
    try:
        file_path = Path(path).expanduser().resolve()
        
        if not file_path.exists():
            return {"exists": False}
        
        stat = file_path.stat()
        
        return {
            "exists": True,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime
        }
    
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }


# 测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("文件操作工具测试")
    print("=" * 40)
    
    # 测试写入
    test_content = "Hello MagicOrigin!\n这是一个测试文件。"
    result = write_file("./test_magic-origin.txt", test_content)
    print(f"\n写入文件: {result['success']}")
    
    # 测试读取
    result = read_file("./test_magic-origin.txt")
    print(f"读取文件: {result['success']}")
    print(f"内容: {result['content']}")
    
    # 测试列出
    result = list_files(".", "*.txt")
    print(f"\n列出 txt 文件: {result['success']}")
    print(f"文件列表: {result['files']}")
    
    # 清理测试文件
    Path("./test_magic-origin.txt").unlink(missing_ok=True)
    print("\n测试完成，已清理")
