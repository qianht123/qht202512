"""
对称约束文件解析器 - 适配新版SymmetryConstraint
解析.sym文件格式的对称约束
"""

import re
import os
from typing import List, Dict, Optional
from .symmetry import SymmetryConstraint, AdvancedSymmetryDetector, SymmetryType


class SymmetryParser:
    """对称约束解析器"""
    
    def __init__(self):
        self.constraint = SymmetryConstraint()
    
    def parse_symmetry_file(self, file_path: str) -> SymmetryConstraint:
        """
        解析对称约束文件
        
        Args:
            file_path: .sym文件路径
            
        Returns:
            SymmetryConstraint: 解析得到的对称约束
        """
        if not os.path.exists(file_path):
            print(f"警告: 对称约束文件不存在: {file_path}")
            return self.constraint
        
        with open(file_path, "r") as f:
            content = f.read()
        
        # 解析各种对称约束
        self._parse_symmetry_pairs(content)
        self._parse_symmetry_axis(content)
        
        return self.constraint
    
    def _parse_symmetry_pairs(self, content: str):
        """解析对称器件对"""
        # 格式: SYMMETRY_PAIR M1 M2
        #       SYMMETRY_PAIR M1 M2 HORIZONTAL
        pattern = r"SYMMETRY_PAIR\\s+(\\w+)\\s+(\\w+)(?:\\s+(\\w+))?"
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for match in matches:
            device1, device2, sym_type = match
            symmetry_type = SymmetryType.VERTICAL
            
            if sym_type:
                sym_type = sym_type.upper()
                if sym_type == "HORIZONTAL":
                    symmetry_type = SymmetryType.HORIZONTAL
                elif sym_type == "DIFFERENTIAL":
                    symmetry_type = SymmetryType.DIFFERENTIAL
                elif sym_type == "CROSS_COUPLED":
                    symmetry_type = SymmetryType.CROSS_COUPLED
            
            # 手动添加到constraint（因为SymmetryConstraint没有add方法）
            from .symmetry import SymmetryPair
            pair = SymmetryPair(device1, device2, symmetry_type)
            self.constraint.symmetry_pairs.append(pair)
    
    def _parse_symmetry_axis(self, content: str):
        """解析对称轴位置"""
        # 格式: SYMMETRY_AXIS 100.0
        pattern = r"SYMMETRY_AXIS\\s+([\\d.]+)"
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        if matches:
            try:
                self.constraint.symmetry_axis = float(matches[0])
            except ValueError:
                print(f"警告: 无效的对称轴位置: {matches[0]}")
    
    def generate_symmetry_file(self, constraint: SymmetryConstraint, output_path: str):
        """
        生成对称约束文件
        
        Args:
            constraint: 对称约束对象
            output_path: 输出文件路径
        """
        content = []
        
        # 写入对称轴
        if hasattr(constraint, "symmetry_axis") and constraint.symmetry_axis is not None:
            content.append(f"SYMMETRY_AXIS {constraint.symmetry_axis}")
        
        # 写入对称器件对
        for pair in constraint.symmetry_pairs:
            line = f"SYMMETRY_PAIR {pair.device1} {pair.device2}"
            if hasattr(pair, "symmetry_type") and pair.symmetry_type != SymmetryType.VERTICAL:
                line += f" {pair.symmetry_type.value.upper()}"
            content.append(line)
        
        # 写入文件
        with open(output_path, "w") as f:
            f.write("\\n".join(content))
    
    def parse_from_netlist(self, netlist_devices: Dict, netlist_nets: Dict) -> SymmetryConstraint:
        """
        从网表自动检测对称约束
        
        Args:
            netlist_devices: 网表器件字典
            netlist_nets: 网表网络字典
            
        Returns:
            SymmetryConstraint: 检测到的对称约束
        """
        detector = AdvancedSymmetryDetector()
        return detector.detect(netlist_devices, netlist_nets)
    
    def validate_constraints(self, constraint: SymmetryConstraint, available_devices: List[str]) -> List[str]:
        """
        验证对称约束的有效性
        
        Args:
            constraint: 对称约束
            available_devices: 可用的器件列表
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        device_set = set(available_devices)
        
        # 检查对称器件对
        for pair in constraint.symmetry_pairs:
            if pair.device1 not in device_set:
                errors.append(f"对称器件对中的器件不存在: {pair.device1}")
            if pair.device2 not in device_set:
                errors.append(f"对称器件对中的器件不存在: {pair.device2}")
        
        return errors


if __name__ == "__main__":
    # 测试代码
    parser = SymmetryParser()
    
    # 创建示例约束
    from .symmetry import SymmetryConstraint, SymmetryPair, SymmetryType
    constraint = SymmetryConstraint()
    constraint.symmetry_pairs.append(SymmetryPair("M1", "M2", SymmetryType.DIFFERENTIAL))
    constraint.symmetry_pairs.append(SymmetryPair("M3", "M4", SymmetryType.VERTICAL))
    constraint.symmetry_axis = 50.0
    
    # 生成文件
    output_file = "/tmp/test_fixed.sym"
    parser.generate_symmetry_file(constraint, output_file)
    print(f"Generated: {output_file}")
    
    # 解析文件
    parsed = parser.parse_symmetry_file(output_file)
    print(f"Parsed {len(parsed.symmetry_pairs)} pairs")
