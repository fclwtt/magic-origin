#!/usr/bin/env python3
"""
终端工具 - 跨平台命令执行

从 Hermes terminal_tool.py 精简，保留核心功能：
- 本地命令执行
- 超时控制
- 跨平台兼容（Windows/Mac/Linux）
"""

import subprocess
import platform
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def run_command(command: str, timeout: int = 30, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    执行终端命令
    
    Args:
        command: 要执行的命令
        timeout: 超时时间（秒）
        cwd: 工作目录
    
    Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "returncode": int
        }
    """
    """Execute a shell command and return the result."""
    
    # 跨平台 shell 设置
    is_windows = platform.system() == "Windows"
    shell = True
    
    try:
        # 执行命令
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding='utf-8',
            errors='replace'  # 处理编码问题
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        logger.warning(f"命令超时 ({timeout}s): {command}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"命令执行超时 ({timeout}秒)",
            "returncode": -1
        }
    
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def get_system_info() -> Dict[str, str]:
    """获取系统信息"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


# 测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("终端工具测试")
    print("=" * 40)
    
    # 测试命令
    test_commands = [
        "echo Hello MagicOrigin",
        "date" if platform.system() != "Windows" else "time /t",
        "dir" if platform.system() == "Windows" else "ls -la"
    ]
    
    for cmd in test_commands:
        print(f"\n执行: {cmd}")
        result = run_command(cmd)
        print(f"成功: {result['success']}")
        print(f"输出: {result['stdout'][:200]}")
        if result['stderr']:
            print(f"错误: {result['stderr']}")
