#!/usr/bin/env python3
"""
测试AdvancedSymmetryDetector自动生成sym文件
"""

import sys
sys.path.append("/install/MAGICAL/qht_chuli_jianlishili")

from buju.constraint.symmetry import AdvancedSymmetryDetector
from buju.constraint.parser import SymmetryParser

def create_test_circuit():
    """创建测试电路数据"""
    devices = {
        "M1": {
            "type": "nmos",
            "parameters": {"w": 10.0, "l": 0.18, "nf": 2, "m": 1},
            "pins": [
                {"name": "G", "net": "VINP"},
                {"name": "D", "net": "OUTP"},
                {"name": "S", "net": "VSS"},
                {"name": "B", "net": "VSS"}
            ]
        },
        "M2": {
            "type": "nmos",
            "parameters": {"w": 10.0, "l": 0.18, "nf": 2, "m": 1},
            "pins": [
                {"name": "G", "net": "VINM"},
                {"name": "D", "net": "OUTM"},
                {"name": "S", "net": "VSS"},
                {"name": "B", "net": "VSS"}
            ]
        },
        "M3": {
            "type": "pmos",
            "parameters": {"w": 20.0, "l": 0.18, "nf": 1, "m": 1},
            "pins": [
                {"name": "G", "net": "BIAS"},
                {"name": "D", "net": "OUTP"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        },
        "M4": {
            "type": "pmos",
            "parameters": {"w": 20.0, "l": 0.18, "nf": 1, "m": 1},
            "pins": [
                {"name": "G", "net": "BIAS"},
                {"name": "D", "net": "OUTM"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        },
        "M5": {
            "type": "pmos",
            "parameters": {"w": 5.0, "l": 0.18, "nf": 1, "m": 1},
            "pins": [
                {"name": "G", "net": "BIAS2"},
                {"name": "D", "net": "BIAS2"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        },
        "M6": {
            "type": "pmos",
            "parameters": {"w": 10.0, "l": 0.18, "nf": 1, "m": 1},
            "pins": [
                {"name": "G", "net": "BIAS2"},
                {"name": "D", "net": "IBIAS"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        }
    }
    
    nets = {
        "VINP": {"pins": [{"device": "M1", "pin": "G"}]},
        "VINM": {"pins": [{"device": "M2", "pin": "G"}]},
        "OUTP": {"pins": [{"device": "M1", "pin": "D"}, {"device": "M3", "pin": "D"}]},
        "OUTM": {"pins": [{"device": "M2", "pin": "D"}, {"device": "M4", "pin": "D"}]},
        "BIAS": {"pins": [{"device": "M3", "pin": "G"}, {"device": "M4", "pin": "G"}]},
        "BIAS2": {"pins": [{"device": "M5", "pin": "G"}, {"device": "M5", "pin": "D"}, {"device": "M6", "pin": "G"}]},
        "IBIAS": {"pins": [{"device": "M6", "pin": "D"}]},
        "VDD": {"pins": [
            {"device": "M3", "pin": "S"}, {"device": "M4", "pin": "S"},
            {"device": "M5", "pin": "S"}, {"device": "M6", "pin": "S"},
            {"device": "M3", "pin": "B"}, {"device": "M4", "pin": "B"},
            {"device": "M5", "pin": "B"}, {"device": "M6", "pin": "B"}
        ]},
        "VSS": {"pins": [
            {"device": "M1", "pin": "S"}, {"device": "M2", "pin": "S"},
            {"device": "M1", "pin": "B"}, {"device": "M2", "pin": "B"}
        ]}
    }
    
    return devices, nets

def main():
    print("=== AdvancedSymmetryDetector 自动生成sym文件演示 ===")
    
    # 1. 创建测试电路
    devices, nets = create_test_circuit()
    print(f"测试电路: {len(devices)} 个器件, {len(nets)} 个网络")
    
    # 2. 运行你的高级检测算法
    print("\\n1. 运行AdvancedSymmetryDetector...")
    detector = AdvancedSymmetryDetector()
    constraint = detector.detect(devices, nets)
    
    print(f"检测到 {len(constraint.symmetry_pairs)} 个对称器件对:")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"  {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type.value}, 置信度: {pair.score})")
    
    # 3. 自动生成sym文件
    print("\\n2. 自动生成sym文件...")
    parser = SymmetryParser()
    output_file = "/tmp/advanced_detected.sym"
    
    # 设置对称轴（可选）
    constraint.symmetry_axis = 50.0
    
    # 生成文件
    parser.generate_symmetry_file(constraint, output_file)
    print(f"sym文件已生成: {output_file}")
    
    # 4. 显示生成的文件内容
    print("\\n3. 生成的sym文件内容:")
    with open(output_file, "r") as f:
        content = f.read()
        print(content)
    
    # 5. 验证生成的文件
    print("\\n4. 验证生成的sym文件...")
    parsed_constraint = parser.parse_symmetry_file(output_file)
    print(f"解析成功: {len(parsed_constraint.symmetry_pairs)} 个对称对")
    
    print("\\n=== 演示完成 ===")

if __name__ == "__main__":
    main()
