#!/usr/bin/env python3
"""
对称约束检测演示脚本
"""

import sys
import os

# 添加路径以便导入模块
sys.path.append("/install/MAGICAL/qht_chuli_jianlishili")

# 直接导入需要的模块
from buju.constraint.symmetry import SymmetryDetector, SymmetryType, SymmetryPair
from buju.constraint.parser import SymmetryParser
from buju.constraint.axis_detector import SymmetryAxisDetector


def create_differential_pair_circuit():
    """创建差分对测试电路"""
    devices = {
        "M1": {
            "type": "nmos",
            "w": 10.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "VIN"},
                {"name": "D", "net": "OUT1"},
                {"name": "S", "net": "VSS"},
                {"name": "B", "net": "VSS"}
            ]
        },
        "M2": {
            "type": "nmos", 
            "w": 10.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "VIN"},
                {"name": "D", "net": "OUT2"},
                {"name": "S", "net": "VSS"},
                {"name": "B", "net": "VSS"}
            ]
        },
        "M3": {
            "type": "pmos",
            "w": 20.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "BIAS"},
                {"name": "D", "net": "OUT1"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        },
        "M4": {
            "type": "pmos",
            "w": 20.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "BIAS"},
                {"name": "D", "net": "OUT2"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        }
    }
    
    nets = {
        "VIN": {
            "pins": [
                {"device": "M1", "pin": "G"},
                {"device": "M2", "pin": "G"}
            ]
        },
        "OUT1": {
            "pins": [
                {"device": "M1", "pin": "D"},
                {"device": "M3", "pin": "D"}
            ]
        },
        "OUT2": {
            "pins": [
                {"device": "M2", "pin": "D"},
                {"device": "M4", "pin": "D"}
            ]
        },
        "BIAS": {
            "pins": [
                {"device": "M3", "pin": "G"},
                {"device": "M4", "pin": "G"}
            ]
        },
        "VDD": {
            "pins": [
                {"device": "M3", "pin": "S"},
                {"device": "M4", "pin": "S"},
                {"device": "M3", "pin": "B"},
                {"device": "M4", "pin": "B"}
            ]
        },
        "VSS": {
            "pins": [
                {"device": "M1", "pin": "S"},
                {"device": "M2", "pin": "S"},
                {"device": "M1", "pin": "B"},
                {"device": "M2", "pin": "B"}
            ]
        }
    }
    
    return devices, nets


def main():
    """主函数"""
    print("=== 对称约束检测演示 ===")
    
    # 创建测试电路
    devices, nets = create_differential_pair_circuit()
    
    print(f"测试电路包含 {len(devices)} 个器件，{len(nets)} 个网络")
    
    # 1. 自动检测对称约束
    print("\\n1. 自动检测对称约束:")
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    print(f"  检测到 {len(constraint.symmetry_pairs)} 个对称器件对")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"    {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type})")
    
    print(f"  检测到 {len(constraint.self_symmetric_devices)} 个自对称器件")
    for device in constraint.self_symmetric_devices:
        print(f"    - {device}")
    
    # 2. 检测对称轴
    print("\\n2. 检测对称轴:")
    axis_detector = SymmetryAxisDetector()
    axis = axis_detector.detect_symmetry_axis(devices, nets, constraint)
    print(f"  自动检测的对称轴位置: {axis}")
    
    # 3. 手动添加对称约束
    print("\\n3. 手动添加对称约束:")
    detector.add_symmetry_pair("M1", "M2", SymmetryType.VERTICAL)
    detector.add_symmetry_pair("M3", "M4", SymmetryType.VERTICAL)
    
    print(f"  添加后共有 {len(constraint.symmetry_pairs)} 个对称器件对")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"    {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type})")
    
    # 4. 创建示例约束文件
    print("\\n4. 创建示例约束文件:")
    parser = SymmetryParser()
    
    # 设置对称轴
    constraint.symmetry_axis = 50.0
    
    # 生成约束文件
    output_file = "/tmp/demo_symmetry.sym"
    parser.generate_symmetry_file(constraint, output_file)
    print(f"  约束文件已生成: {output_file}")
    
    # 5. 解析约束文件
    print("\\n5. 解析约束文件:")
    parsed_constraint = parser.parse_symmetry_file(output_file)
    print(f"  对称轴位置: {parsed_constraint.symmetry_axis}")
    print(f"  对称器件对数量: {len(parsed_constraint.symmetry_pairs)}")
    
    # 6. 显示生成的约束文件内容
    print("\\n6. 生成的约束文件内容:")
    with open(output_file, "r") as f:
        content = f.read()
        print(content)
    
    print("\\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
