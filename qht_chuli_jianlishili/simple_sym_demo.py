#!/usr/bin/env python3
"""
简化的sym文件自动生成演示
"""

import sys
sys.path.append("/install/MAGICAL/qht_chuli_jianlishili")

# 直接使用你的AdvancedSymmetryDetector
from buju.constraint.symmetry import AdvancedSymmetryDetector, SymmetryType
from buju.constraint.parser import SymmetryParser

def create_simple_circuit():
    """创建简单电路数据"""
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
        }
    }
    
    nets = {
        "VINP": {"pins": [{"device": "M1", "pin": "G"}]},
        "VINM": {"pins": [{"device": "M2", "pin": "G"}]},
        "OUTP": {"pins": [{"device": "M1", "pin": "D"}, {"device": "M3", "pin": "D"}]},
        "OUTM": {"pins": [{"device": "M2", "pin": "D"}, {"device": "M4", "pin": "D"}]},
        "BIAS": {"pins": [{"device": "M3", "pin": "G"}, {"device": "M4", "pin": "G"}]},
        "VDD": {"pins": [
            {"device": "M3", "pin": "S"}, {"device": "M4", "pin": "S"},
            {"device": "M3", "pin": "B"}, {"device": "M4", "pin": "B"}
        ]},
        "VSS": {"pins": [
            {"device": "M1", "pin": "S"}, {"device": "M2", "pin": "S"},
            {"device": "M1", "pin": "B"}, {"device": "M2", "pin": "B"}
        ]}
    }
    
    return devices, nets

def main():
    print("=== AdvancedSymmetryDetector 自动生成sym文件演示 ===")
    
    # 1. 创建电路数据
    devices, nets = create_simple_circuit()
    print(f"电路包含 {len(devices)} 个器件: {list(devices.keys())}")
    
    # 2. 手动创建对称约束（模拟你的算法检测结果）
    print("\\n1. 模拟AdvancedSymmetryDetector检测结果...")
    
    # 创建SymmetryConstraint对象
    from buju.constraint.symmetry import SymmetryConstraint, SymmetryPair
    constraint = SymmetryConstraint()
    
    # 添加检测到的对称对（你的算法会自动生成这些）
    constraint.symmetry_pairs.append(
        SymmetryPair("M1", "M2", SymmetryType.DIFFERENTIAL, score=0.95)
    )
    constraint.symmetry_pairs.append(
        SymmetryPair("M3", "M4", SymmetryType.VERTICAL, score=0.90)
    )
    
    print(f"检测到 {len(constraint.symmetry_pairs)} 个对称器件对:")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"  {i+1}. {pair.device1} <-> {pair.device2} ({pair.symmetry_type.value}, 置信度: {pair.score})")
    
    # 3. 自动生成sym文件
    print("\\n2. 自动生成sym文件...")
    parser = SymmetryParser()
    output_file = "/tmp/auto_generated.sym"
    
    # 设置对称轴
    constraint.symmetry_axis = 50.0
    
    # 生成文件
    parser.generate_symmetry_file(constraint, output_file)
    print(f"✅ sym文件已自动生成: {output_file}")
    
    # 4. 显示生成的文件内容
    print("\\n3. 生成的sym文件内容:")
    print("=" * 40)
    with open(output_file, "r") as f:
        content = f.read()
        print(content)
    print("=" * 40)
    
    # 5. 验证生成的文件
    print("\\n4. 验证生成的sym文件...")
    parsed_constraint = parser.parse_symmetry_file(output_file)
    print(f"✅ 解析成功: {len(parsed_constraint.symmetry_pairs)} 个对称对")
    
    # 6. 说明工作流程
    print("\\n5. 完整工作流程说明:")
    print("   📊 输入: 电路网表 (器件连接关系)")
    print("   🔍 检测: AdvancedSymmetryDetector 分析电路拓扑")
    print("   📝 输出: 自动生成 .sym 约束文件")
    print("   🎯 用途: 布局引擎读取约束文件进行对称布局")
    
    print("\\n=== 演示完成 ===")

if __name__ == "__main__":
    main()
