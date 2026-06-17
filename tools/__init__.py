# MagicOrigin Tools
"""
工具模块 - 跨平台兼容
"""

from .terminal import run_command
from .file_ops import read_file, write_file, list_files

__all__ = ['run_command', 'read_file', 'write_file', 'list_files']
