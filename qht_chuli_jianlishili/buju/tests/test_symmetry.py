"""
对称约束检测测试
"""

import sys
import os

# 添加路径以便导入模块
sys.path.append("/install/MAGICAL/qht_chuli_jianlishili")

from buju.constraint.symmetry import SymmetryDetector, SymmetryType
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


def create_current_mirror_circuit():
    """创建电流镜测试电路"""
    devices = {
        "M5": {
            "type": "pmos",
            "w": 10.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "BIAS2"},
                {"name": "D", "net": "BIAS2"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        },
        "M6": {
            "type": "pmos",
            "w": 20.0,
            "l": 0.5,
            "nf": 1,
            "pins": [
                {"name": "G", "net": "BIAS2"},
                {"name": "D", "net": "IOUT"},
                {"name": "S", "net": "VDD"},
                {"name": "B", "net": "VDD"}
            ]
        }
    }
    
    nets = {
        "BIAS2": {
            "pins": [
                {"device": "M5", "pin": "G"},
                {"device": "M5", "pin": "D"},
                {"device": "M6", "pin": "G"}
            ]
        },
        "IOUT": {
            "pins": [
                {"device": "M6", "pin": "D"}
            ]
        },
        "VDD": {
            "pins": [
                {"device": "M5", "pin": "S"},
                {"device": "M6", "pin": "S"},
                {"device": "M5", "pin": "B"},
                {"device": "M6", "pin": "B"}
            ]
        }
    }
    
    return devices, nets


def test_symmetry_detection():
    """测试对称约束检测"""
    print("=== 测试对称约束检测 ===")
    
    # 测试差分对电路
    print("\\n1. 测试差分对电路:")
    devices, nets = create_differential_pair_circuit()
    
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    print(f"检测到的对称器件对数量: {len(constraint.symmetry_pairs)}")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"  对 {i+1}: {pair.device1} <-> {pair.device2}")
    
    # 测试电流镜电路
    print("\\n2. 测试电流镜电路:")
    devices, nets = create_current_mirror_circuit()
    
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    print(f"检测到的对称器件对数量: {len(constraint.symmetry_pairs)}")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"  对 {i+1}: {pair.device1} <-> {pair.device2}")


def test_symmetry_parser():
    """测试对称约束解析器"""
    print("\\n=== 测试对称约束解析器 ===")
    
    # 创建测试sym文件
    test_sym_file = "/tmp/test_circuit.sym"
    
    with open(test_sym_file, "w") as f:
        f.write("""# 测试对称约束文件
SYMMETRY_AXIS 100.0

# 差分对
SYMMETRY_PAIR M1 M2
SYMMETRY_PAIR M3 M4

# 电流镜
SYMMETRY_PAIR M5 M6

# 自对称器件
SELF_SYMMETRY M7
""")
    
    # 解析文件
    parser = SymmetryParser()
    constraint = parser.parse_symmetry_file(test_sym_file)
    
    print(f"对称轴位置: {constraint.symmetry_axis}")
    print(f"对称器件对数量: {len(constraint.symmetry_pairs)}")
    print(f"自对称器件数量: {len(constraint.self_symmetric_devices)}")
    
    # 验证约束
    available_devices = ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]
    errors = parser.validate_constraints(constraint, available_devices)
    
    if errors:
        print("验证错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("约束验证通过")
    
    # 生成对称约束文件
    output_file = "/tmp/test_output.sym"
    parser.generate_symmetry_file(constraint, output_file)
    print(f"\\n生成的约束文件: {output_file}")


def test_axis_detection():
    """测试对称轴检测"""
    print("\\n=== 测试对称轴检测 ===")
    
    # 测试差分对电路的对称轴检测
    devices, nets = create_differential_pair_circuit()
    
    # 首先检测对称约束
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    # 然后检测对称轴
    axis_detector = SymmetryAxisDetector()
    axis = axis_detector.detect_symmetry_axis(devices, nets, constraint)
    
    print(f"差分对电路检测到的对称轴位置: {axis}")
    
    # 测试电流镜电路的对称轴检测
    devices, nets = create_current_mirror_circuit()
    
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    axis_detector = SymmetryAxisDetector()
    axis = axis_detector.detect_symmetry_axis(devices, nets, constraint)
    
    print(f"电流镜电路检测到的对称轴位置: {axis}")


def test_complete_workflow():
    """测试完整工作流程"""
    print("\\n=== 测试完整工作流程 ===")
    
    # 创建复杂测试电路
    devices = {
        "M1": {"type": "nmos", "w": 10.0, "l": 0.5, "nf": 2, "pins": [
            {"name": "G", "net": "VIN"}, {"name": "D", "net": "OUT1"}, 
            {"name": "S", "net": "VSS"}, {"name": "B", "net": "VSS"}
        ]},
        "M2": {"type": "nmos", "w": 10.0, "l": 0.5, "nf": 2, "pins": [
            {"name": "G", "net": "VIN"}, {"name": "D", "net": "OUT2"}, 
            {"name": "S", "net": "VSS"}, {"name": "B", "net": "VSS"}
        ]},
        "M3": {"type": "pmos", "w": 20.0, "l": 0.5, "nf": 1, "pins": [
            {"name": "G", "net": "BIAS"}, {"name": "D", "net": "OUT1"}, 
            {"name": "S", "net": "VDD"}, {"name": "B", "net": "VDD"}
        ]},
        "M4": {"type": "pmos", "w": 20.0, "l": 0.5, "nf": 1, "pins": [
            {"name": "G", "net": "BIAS"}, {"name": "D", "net": "OUT2"}, 
            {"name": "S", "net": "VDD"}, {"name": "B", "net": "VDD"}
        ]},
        "M5": {"type": "pmos", "w": 5.0, "l": 0.5, "nf": 1, "pins": [
            {"name": "G", "net": "BIAS2"}, {"name": "D", "net": "BIAS2"}, 
            {"name": "S", "net": "VDD"}, {"name": "B", "net": "VDD"}
        ]},
        "M6": {"type": "pmos", "w": 10.0, "l": 0.5, "nf": 1, "pins": [
            {"name": "G", "net": "BIAS2"}, {"name": "D", "net": "IOUT"}, 
            {"name": "S", "net": "VDD"}, {"name": "B", "net": "VDD"}
        ]}
    }
    
    nets = {
        "VIN": {"pins": [{"device": "M1", "pin": "G"}, {"device": "M2", "pin": "G"}]},
        "OUT1": {"pins": [{"device": "M1", "pin": "D"}, {"device": "M3", "pin": "D"}]},
        "OUT2": {"pins": [{"device": "M2", "pin": "D"}, {"device": "M4", "pin": "D"}]},
        "BIAS": {"pins": [{"device": "M3", "pin": "G"}, {"device": "M4", "pin": "G"}]},
        "BIAS2": {"pins": [{"device": "M5", "pin": "G"}, {"device": "M5", "pin": "D"}, {"device": "M6", "pin": "G"}]},
        "IOUT": {"pins": [{"device": "M6", "pin": "D"}]},
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
    
    # 1. 自动检测对称约束
    print("1. 自动检测对称约束:")
    detector = SymmetryDetector()
    constraint = detector.detect_symmetry_from_nets(devices, nets)
    
    print(f"  检测到 {len(constraint.symmetry_pairs)} 个对称器件对")
    for i, pair in enumerate(constraint.symmetry_pairs):
        print(f"    {i+1}. {pair.device1} <-> {pair.device2}")
    
    print(f"  检测到 {len(constraint.self_symmetric_devices)} 个自对称器件")
    for device in constraint.self_symmetric_devices:
        print(f"    - {device}")
    
    # 2. 检测对称轴
    print("\\n2. 检测对称轴:")
    axis_detector = SymmetryAxisDetector()
    axis = axis_detector.detect_symmetry_axis(devices, nets, constraint)
    print(f"  自动检测的对称轴位置: {axis}")
    
    # 3. 优化对称轴
    refined_axis = axis_detector.refine_symmetry_axis(axis, devices, constraint)
    print(f"  优化后的对称轴位置: {refined_axis}")
    
    # 4. 生成约束文件
    print("\\n3. 生成约束文件:")
    parser = SymmetryParser()
    output_file = "/tmp/complete_workflow.sym"
    parser.generate_symmetry_file(constraint, output_file)
    print(f"  约束文件已生成: {output_file}")
    
    print("\\n=== 完整工作流程测试完成 ===")


if __name__ == "__main__":
    print("开始对称约束检测测试...")
    
    test_symmetry_detection()
    test_symmetry_parser()
    test_axis_detection()
    test_complete_workflow()
    
    print("\\n所有测试完成！")
