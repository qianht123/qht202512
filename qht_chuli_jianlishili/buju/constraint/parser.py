"""
模拟/射频IC 对称约束检测与管理系统 (Advanced Version)
包含：设计意图捕获、自动检测、对称传播、ERC检查、JSON文件I/O
"""

import json
import os
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any, Tuple

# =============================================================================
# 1. 核心数据结构与定义 (捕获设计意图)
# =============================================================================

class LayoutPattern(Enum):
    """布局模式枚举：捕获设计意图"""
    NONE = "none"                       # 不强制特定模式
    SIMPLE_MIRROR = "simple_mirror"     # 简单镜像 (A | B)
    COMMON_CENTROID = "common_centroid" # 共质心 (ABBA / 2D Matrix) - 高精度差分对
    INTERDIGITATED = "interdigitated"   # 叉指 (A B A B) - 电流镜/电阻匹配

class SymmetryType(Enum):
    """对称电气拓扑类型"""
    VERTICAL = "vertical"           # 通用垂直对称
    DIFFERENTIAL = "differential"   # 差分对
    CROSS_COUPLED = "cross_coupled" # 交叉耦合 (VCO/Latch)
    PASSIVE = "passive"             # 无源器件对称

@dataclass
class SymmetryOptions:
    """高级对称物理选项"""
    add_dummy: bool = False             # 是否添加Dummy管
    guard_ring: str = "none"            # 保护环类型: none, pwell, nwell, deep_nwell
    match_orientation: bool = True      # 是否强制方向一致
    tolerance: float = 1e-9             # 允许的参数误差绝对值

@dataclass
class SymmetryPair:
    """对称器件对"""
    device1: str
    device2: str
    symmetry_type: SymmetryType = SymmetryType.VERTICAL
    # --- 新增设计意图字段 ---
    pattern: LayoutPattern = LayoutPattern.SIMPLE_MIRROR
    options: SymmetryOptions = field(default_factory=SymmetryOptions)
    score: float = 1.0  # 置信度评分 (0.0 - 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SymmetryConstraint:
    """对称约束容器"""
    symmetry_pairs: List[SymmetryPair] = field(default_factory=list)
    symmetry_axis: float = 0.0
    processed_devices: Set[str] = field(default_factory=set)

# =============================================================================
# 2. 电气规则检查器 (ERC)
# =============================================================================

class SymmetryERC:
    """
    Symmetry Electrical Rule Checker
    负责验证对称约束在电气层面是否合法 (W/L/NF/M 必须匹配)
    """
    
    def __init__(self, devices: Dict[str, Dict]):
        self.devices = devices
        self.errors = []
        self.warnings = []

    def run_check(self, constraint: SymmetryConstraint) -> bool:
        """执行检查"""
        self.errors = []
        self.warnings = []
        
        for pair in constraint.symmetry_pairs:
            self._check_pair_integrity(pair)
            
        return len(self.errors) == 0

    def print_report(self):
        print("=== Symmetry ERC Report ===")
        if not self.errors and not self.warnings:
            print("Status: PASSED (Clean)")
        else:
            if self.errors:
                print(f"Errors ({len(self.errors)}):")
                for e in self.errors: print(f"  [Error] {e}")
            if self.warnings:
                print(f"Warnings ({len(self.warnings)}):")
                for w in self.warnings: print(f"  [Warn]  {w}")
        print("===========================")

    def _check_pair_integrity(self, pair: SymmetryPair):
        d1 = self.devices.get(pair.device1)
        d2 = self.devices.get(pair.device2)
        
        # 1. 存在性检查
        if not d1 or not d2:
            self.errors.append(f"Device missing: {pair.device1} or {pair.device2}")
            return

        # 2. 类型检查
        if d1.get("type") != d2.get("type"):
            self.errors.append(f"Type mismatch: {pair.device1}({d1.get('type')}) vs {pair.device2}({d2.get('type')})")
            return

        # 3. 参数严格匹配
        params_to_check = ["w", "l", "nf", "m"]
        p1 = d1.get("parameters", {})
        p2 = d2.get("parameters", {})
        
        for param in params_to_check:
            val1 = float(p1.get(param, 0))
            val2 = float(p2.get(param, 0))
            if abs(val1 - val2) > pair.options.tolerance:
                self.errors.append(f"Param mismatch {pair.device1}/{pair.device2}: {param} ({val1} != {val2})")

        # 4. 意图合理性检查
        if pair.pattern == LayoutPattern.COMMON_CENTROID:
            nf = float(p1.get("nf", 1))
            m = float(p1.get("m", 1))
            if nf < 2 and m < 2:
                self.warnings.append(f"Intent warning: {pair.device1}/{pair.device2} requested Common Centroid but has no multi-fingers.")

# =============================================================================
# 3. 高级对称检测器 (Detector)
# =============================================================================

class SymmetryDetector:
    """包含指纹识别、拓扑匹配和传播算法的检测器"""
    
    def __init__(self):
        self.constraint = SymmetryConstraint()
    
    def detect(self, devices: Dict[str, Dict], nets: Dict[str, Dict]) -> SymmetryConstraint:
        self.constraint = SymmetryConstraint() # Reset
        
        # 1. 指纹分组 (基于类型和W/L/NF)
        grouped_devices = self._group_devices_by_type_and_param(devices)
        
        # 2. 核心拓扑检测
        self._detect_differential_pairs(grouped_devices, devices)
        self._detect_cross_coupled_pairs(grouped_devices, devices)
        
        # 3. 对称传播 (Propagation) - 关键步骤
        self._propagate_symmetry(devices)
        
        return self.constraint

    def _group_devices_by_type_and_param(self, devices: Dict) -> Dict[str, List[str]]:
        groups = {}
        for name, data in devices.items():
            params = data.get("parameters", {})
            # 创建唯一指纹: "nmos_10u_0.18u_nf4"
            fingerprint = f"{data.get('type')}_{params.get('w')}_{params.get('l')}_{params.get('nf', 1)}"
            if fingerprint not in groups: groups[fingerprint] = []
            groups[fingerprint].append(name)
        return groups

    def _get_pin_net(self, device_data: Dict, pin_type: str) -> Optional[str]:
        """归一化获取引脚连接的网络"""
        pin_map = {'G': ['g', 'gate', 'b'], 'D': ['d', 'drain'], 'S': ['s', 'source']}
        target_names = pin_map.get(pin_type, [])
        for pin in device_data.get("pins", []):
            if any(t in pin.get("name", "").lower() for t in target_names):
                return pin.get("net")
        return None

    def _detect_differential_pairs(self, groups, all_devices):
        """检测差分对：源极共连，栅漏分离"""
        for _, dev_list in groups.items():
            if len(dev_list) < 2: continue
            for i in range(len(dev_list)):
                for j in range(i + 1, len(dev_list)):
                    d1, d2 = dev_list[i], dev_list[j]
                    if d1 in self.constraint.processed_devices: continue
                    
                    info1, info2 = all_devices[d1], all_devices[d2]
                    g1, s1, d1_net = self._get_pin_net(info1, 'G'), self._get_pin_net(info1, 'S'), self._get_pin_net(info1, 'D')
                    g2, s2, d2_net = self._get_pin_net(info2, 'G'), self._get_pin_net(info2, 'S'), self._get_pin_net(info2, 'D')
                    
                    # 差分逻辑
                    if s1 and (s1 == s2) and (g1 != g2) and (d1_net != d2_net):
                        self._add_pair(d1, d2, SymmetryType.DIFFERENTIAL, LayoutPattern.COMMON_CENTROID)

    def _detect_cross_coupled_pairs(self, groups, all_devices):
        """检测交叉耦合：G1-D2, G2-D1"""
        for _, dev_list in groups.items():
            for i in range(len(dev_list)):
                for j in range(i + 1, len(dev_list)):
                    d1, d2 = dev_list[i], dev_list[j]
                    if d1 in self.constraint.processed_devices: continue
                    
                    info1, info2 = all_devices[d1], all_devices[d2]
                    g1, s1, d1_net = self._get_pin_net(info1, 'G'), self._get_pin_net(info1, 'S'), self._get_pin_net(info1, 'D')
                    g2, s2, d2_net = self._get_pin_net(info2, 'G'), self._get_pin_net(info2, 'S'), self._get_pin_net(info2, 'D')
                    
                    if s1 and (s1 == s2) and (g1 == d2_net) and (g2 == d1_net):
                        self._add_pair(d1, d2, SymmetryType.CROSS_COUPLED, LayoutPattern.COMMON_CENTROID)

    def _propagate_symmetry(self, devices):
        """沿着信号链传播对称性"""
        net_map = self._build_net_map(devices)
        queue = list(self.constraint.symmetry_pairs)
        visited_pairs = set()

        while queue:
            pair = queue.pop(0)
            pair_id = frozenset([pair.device1, pair.device2])
            if pair_id in visited_pairs: continue
            visited_pairs.add(pair_id)

            d1_info, d2_info = devices.get(pair.device1), devices.get(pair.device2)
            if not d1_info or not d2_info: continue

            # 检查漏极连接的器件
            n1 = self._get_pin_net(d1_info, 'D')
            n2 = self._get_pin_net(d2_info, 'D')

            if n1 and n2 and n1 != n2:
                neighbors1 = net_map.get(n1, [])
                neighbors2 = net_map.get(n2, [])
                self._find_neighbors_match(neighbors1, neighbors2, devices, queue)

    def _find_neighbors_match(self, cands1, cands2, devices, queue):
        """在两个网络集合中寻找参数匹配的器件"""
        for (name1, pin1) in cands1:
            if name1 in self.constraint.processed_devices: continue
            for (name2, pin2) in cands2:
                if name2 in self.constraint.processed_devices: continue
                if name1 == name2: continue
                
                # 简单参数校验 (详细校验由ERC完成)
                dev1, dev2 = devices[name1], devices[name2]
                if dev1['type'] == dev2['type'] and \
                   dev1.get('parameters') == dev2.get('parameters') and \
                   pin1[0].lower() == pin2[0].lower(): # Pin role match (D vs D)
                    
                    new_pair = self._add_pair(name1, name2, SymmetryType.VERTICAL, LayoutPattern.SIMPLE_MIRROR)
                    if new_pair: queue.append(new_pair)
                    break # 假设一对一

    def _build_net_map(self, devices):
        """建立 Net -> [(Device, Pin)] 映射"""
        mapping = {}
        for dname, ddata in devices.items():
            for pin in ddata.get("pins", []):
                net = pin.get("net")
                if net:
                    if net not in mapping: mapping[net] = []
                    mapping[net].append((dname, pin.get("name")))
        return mapping

    def _add_pair(self, d1, d2, stype, pattern):
        if d1 not in self.constraint.processed_devices and d2 not in self.constraint.processed_devices:
            pair = SymmetryPair(device1=d1, device2=d2, symmetry_type=stype, pattern=pattern)
            self.constraint.symmetry_pairs.append(pair)
            self.constraint.processed_devices.add(d1)
            self.constraint.processed_devices.add(d2)
            return pair
        return None

# =============================================================================
# 4. JSON 文件解析与管理 (File I/O)
# =============================================================================

class SymmetryManager:
    """管理 Symmetry 的 I/O 和流程"""
    
    @staticmethod
    def load_from_json(file_path: str) -> SymmetryConstraint:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return SymmetryConstraint()

        with open(file_path, 'r') as f:
            data = json.load(f)

        constraint = SymmetryConstraint()
        constraint.symmetry_axis = data.get("global", {}).get("axis_x", 0.0)

        for pdata in data.get("pairs", []):
            # 解析枚举
            try:
                stype = SymmetryType(pdata.get("type", "vertical"))
            except: stype = SymmetryType.VERTICAL
            
            try:
                pattern = LayoutPattern(pdata.get("pattern", "simple_mirror"))
            except: pattern = LayoutPattern.SIMPLE_MIRROR

            # 解析选项
            opt_dict = pdata.get("options", {})
            options = SymmetryOptions(
                add_dummy=opt_dict.get("add_dummy", False),
                guard_ring=opt_dict.get("guard_ring", "none"),
                match_orientation=opt_dict.get("match_orientation", True),
                tolerance=opt_dict.get("tolerance", 1e-9)
            )

            pair = SymmetryPair(
                device1=pdata["d1"],
                device2=pdata["d2"],
                symmetry_type=stype,
                pattern=pattern,
                options=options,
                metadata=pdata.get("metadata", {})
            )
            constraint.symmetry_pairs.append(pair)
            constraint.processed_devices.update([pdata["d1"], pdata["d2"]])
            
        return constraint

    @staticmethod
    def save_to_json(constraint: SymmetryConstraint, file_path: str):
        output = {
            "global": {"axis_x": constraint.symmetry_axis},
            "pairs": []
        }
        for pair in constraint.symmetry_pairs:
            output["pairs"].append({
                "d1": pair.device1,
                "d2": pair.device2,
                "type": pair.symmetry_type.value,
                "pattern": pair.pattern.value,
                "options": {
                    "add_dummy": pair.options.add_dummy,
                    "guard_ring": pair.options.guard_ring,
                    "match_orientation": pair.options.match_orientation
                },
                "metadata": pair.metadata
            })
        
        with open(file_path, 'w', indent=4) as f:
            json.dump(output, f, indent=4)
        print(f"Constraints saved to {file_path}")