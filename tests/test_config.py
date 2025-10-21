#!/usr/bin/env python3
"""
测试配置功能验证脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_websocket_protocol import get_config

def test_config():
    """测试配置功能"""
    print("测试配置功能...")
    
    # 测试默认配置
    print("\n1. 测试默认配置:")
    config = get_config()
    print(f"   主机: {config['host']}")
    print(f"   端口: {config['port']}")
    print(f"   超时: {config['timeout']}")
    print(f"   路径: {config['path']}")
    print(f"   URL: {config['ws_url']}")
    
    # 测试环境变量
    print("\n2. 测试环境变量:")
    os.environ['TEST_HOST'] = '192.168.1.100'
    os.environ['TEST_PORT'] = '9000'
    os.environ['TEST_TIMEOUT'] = '60'
    
    config = get_config()
    print(f"   主机: {config['host']}")
    print(f"   端口: {config['port']}")
    print(f"   超时: {config['timeout']}")
    print(f"   URL: {config['ws_url']}")
    
    # 清理环境变量
    del os.environ['TEST_HOST']
    del os.environ['TEST_PORT']
    del os.environ['TEST_TIMEOUT']
    
    print("\n✅ 配置功能测试完成")

if __name__ == "__main__":
    test_config()
