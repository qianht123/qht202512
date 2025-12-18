from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# --- 数据结构保持不变，但增加一些辅助 ---
class SymmetryType(Enum):
    VERTICAL = "vertical"
    CROSS_COUPLED = "cross_coupled"  # 新增：交叉耦合
    DIFFERENTIAL = "differential"
    PASSIVE = "passive"             # 新增：无源器件对称

@dataclass
class SymmetryPair:
    device1: str
    device2: str
    symmetry_type: SymmetryType
    score: float = 1.0  # 新增：置信度评分

@dataclass
class SymmetryConstraint:
    symmetry_pairs: List[SymmetryPair] = field(default_factory=list)
    # 使用集合防止重复添加
    processed_devices: Set[str] = field(default_factory=set)

class AdvancedSymmetryDetector:
    def __init__(self):
        self.constraint = SymmetryConstraint()

    def detect(self, devices: Dict[str, Dict], nets: Dict[str, Dict]) -> SymmetryConstraint:
        """
        增强的检测流程
        Args:
            devices: {name: {type, pins:[], parameters:{w, l, nf, m...}}} 
            nets: {net_name: [connected_pins...]}
        """
        # 1. 预处理：按类型对器件分组 (MOS, CAP, RES)
        grouped_devices = self._group_devices_by_type_and_param(devices)
        
        # 2. 检测核心模拟结构 (优先级最高)
        # 差分对 (Differential Pair)
        self._detect_differential_pairs(grouped_devices, nets, devices)
        
        # 交叉耦合对 (Cross-Coupled Pair) - RF VCO/Mixer常见
        self._detect_cross_coupled_pairs(grouped_devices, nets, devices)
        
        # 3. 检测无源器件对称 (电阻/电容负载)
        self._detect_passive_symmetry(grouped_devices, nets, devices)

        # 4. (进阶) 连通性传播
        # 如果 M1/M2 是差分对，那么连接在它们漏极的负载管 M3/M4 通常也是对称的
        self._propagate_symmetry(devices, nets)
        
        return self.constraint

    def _group_devices_by_type_and_param(self, devices: Dict) -> Dict[str, List[str]]:
        """
        关键改进：只有类型相同、且W/L/NF参数一致的器件才可能是对称对。
        """
        groups = {}
        for name, data in devices.items():
            # 生成指纹：例如 "nmos_w10u_l0.18u_nf4"
            params = data.get("parameters", {})
            w = params.get("w", 0)
            l = params.get("l", 0)
            nf = params.get("nf", 1)
            model = data.get("type", "unknown")
            
            fingerprint = f"{model}_{w}_{l}_{nf}"
            
            if fingerprint not in groups:
                groups[fingerprint] = []
            groups[fingerprint].append(name)
        return groups

    def _get_pin_net(self, device_data: Dict, pin_type: str) -> str:
        """辅助函数：获取特定引脚连接的网络名"""
        # 这里需要处理引脚映射，例如 Gate 可能是 'G', 'g', 'gate' 等
        pin_map = {'G': ['g', 'gate', 'b'], 'D': ['d', 'drain'], 'S': ['s', 'source']}
        target_names = pin_map.get(pin_type, [])
        
        for pin in device_data.get("pins", []):
            if pin.get("name", "").lower() in target_names:
                return pin.get("net")
        return None

    def _detect_differential_pairs(self, grouped_devices, nets, all_devices):
        """
        改进的差分对检测：
        1. 必须参数匹配
        2. 源极(Source)必须连接在一起 (Common Source)
        3. 栅极(Gate)连接不同网络 (差分输入)
        4. 漏极(Drain)连接不同网络 (差分输出)
        """
        for signature, dev_list in grouped_devices.items():
            if "mos" not in signature and "ch" not in signature: continue # 只看MOS管
            
            # 两两比较
            processed = set()
            for i in range(len(dev_list)):
                for j in range(i + 1, len(dev_list)):
                    d1_name, d2_name = dev_list[i], dev_list[j]
                    if d1_name in self.constraint.processed_devices or d2_name in self.constraint.processed_devices:
                        continue

                    d1 = all_devices[d1_name]
                    d2 = all_devices[d2_name]
                    
                    # 获取连接
                    g1, s1, d1_net = self._get_pin_net(d1, 'G'), self._get_pin_net(d1, 'S'), self._get_pin_net(d1, 'D')
                    g2, s2, d2_net = self._get_pin_net(d2, 'G'), self._get_pin_net(d2, 'S'), self._get_pin_net(d2, 'D')
                    
                    # 核心逻辑：源极共连，栅漏分离
                    is_diff = (s1 == s2) and (g1 != g2) and (d1_net != d2_net) and (s1 is not None)
                    
                    if is_diff:
                        self.constraint.symmetry_pairs.append(SymmetryPair(d1_name, d2_name, SymmetryType.DIFFERENTIAL))
                        self.constraint.processed_devices.add(d1_name)
                        self.constraint.processed_devices.add(d2_name)

    def _detect_cross_coupled_pairs(self, grouped_devices, nets, all_devices):
        """
        检测交叉耦合对 (Cross-Coupled Pair) - 在VCO和存储器中极其重要
        特征：M1的栅极接M2的漏极，M2的栅极接M1的漏极
        """
        for signature, dev_list in grouped_devices.items():
            if "mos" not in signature: continue
            
            for i in range(len(dev_list)):
                for j in range(i + 1, len(dev_list)):
                    d1_name, d2_name = dev_list[i], dev_list[j]
                    if d1_name in self.constraint.processed_devices: continue

                    d1, d2 = all_devices[d1_name], all_devices[d2_name]
                    
                    g1, s1, d1_net = self._get_pin_net(d1, 'G'), self._get_pin_net(d1, 'S'), self._get_pin_net(d1, 'D')
                    g2, s2, d2_net = self._get_pin_net(d2, 'G'), self._get_pin_net(d2, 'S'), self._get_pin_net(d2, 'D')
                    
                    # 交叉耦合逻辑
                    is_cross = (g1 == d2_net) and (g2 == d1_net) and (s1 == s2)
                    
                    if is_cross:
                        self.constraint.symmetry_pairs.append(SymmetryPair(d1_name, d2_name, SymmetryType.CROSS_COUPLED))
                        self.constraint.processed_devices.update([d1_name, d2_name])

    def _detect_passive_symmetry(self, grouped_devices, nets, all_devices):
        """检测电阻/电容的对称性"""
        # 逻辑：寻找两个参数相同的R/C，它们的一端连接在一起（或接到地/电源），另一端分别接到一个已知的对称对上
        pass # 实现逻辑类似上述，重点在于利用已知的MOS对称对作为锚点

        def _propagate_symmetry(self, devices: Dict[str, Dict], nets: Dict[str, Dict]):
            """
            对称传播算法：基于已知的对称对，沿着网络连接发现新的对称对。
            例如：从差分对 -> 共源共栅管 (Cascode) -> 有源负载 (Active Load)。
            """
        # 1. 构建反向查找表：Net Name -> List[(Device Name, Pin Name)]
        # 这样我们可以快速知道谁连在这个网上，而不用遍历所有器件
        net_to_devices_map = self._build_net_to_device_map(all_devices)

        # 使用队列进行广度优先搜索 (BFS) 风格的传播
        # 初始队列包含当前所有已知的对称对
        processing_queue = list(self.constraint.symmetry_pairs)
        
        # 防止重复处理同一个对称对
        processed_pairs_ids = set() 
        
        while processing_queue:
            current_pair = processing_queue.pop(0)
            
            # 生成唯一ID防止重复处理
            pair_id = frozenset([current_pair.device1, current_pair.device2])
            if pair_id in processed_pairs_ids:
                continue
            processed_pairs_ids.add(pair_id)

            dev1_info = devices.get(current_pair.device1)
            dev2_info = devices.get(current_pair.device2)
            
            if not dev1_info or not dev2_info:
                continue

            # 遍历该对器件的所有主要引脚 (D, S, G)
            # 我们检查对应的引脚是否连接到不同的网络
            # 如果连接到同一个网络（如共源节点），通常不需要传播（那是自对称点）
            for pin_type in ['D', 'S', 'G']:
                net1 = self._get_pin_net(dev1_info, pin_type)
                net2 = self._get_pin_net(dev2_info, pin_type)

                # 只有当两个网络不同，且都有连接时，才具备传播差分对称的条件
                if net1 and net2 and net1 != net2:
                    # 查找连接到 net1 的所有邻居
                    neighbors1 = net_to_devices_map.get(net1, [])
                    # 查找连接到 net2 的所有邻居
                    neighbors2 = net_to_devices_map.get(net2, [])

                    # 在邻居中寻找匹配的对
                    self._find_and_add_matching_neighbors(
                        neighbors1, neighbors2, 
                        devices, processing_queue,
                        current_pair.device1, current_pair.device2
                    )

    def _build_net_to_device_map(self, devices: Dict) -> Dict[str, List[Tuple[str, str]]]:
        """
        辅助函数：构建网络拓扑映射
        Returns: { 'net_name': [('M1', 'D'), ('M2', 'S'), ...], ... }
        """
        net_map = {}
        for dev_name, dev_data in devices.items():
            for pin in dev_data.get("pins", []):
                net_name = pin.get("net")
                pin_name = pin.get("name")
                if net_name:
                    if net_name not in net_map:
                        net_map[net_name] = []
                    net_map[net_name].append((dev_name, pin_name))
        return net_map

    def _find_and_add_matching_neighbors(
        self, 
        candidates1: List[Tuple[str, str]], 
        candidates2: List[Tuple[str, str]], 
        devices: Dict,
        queue: List[SymmetryPair],
        parent_dev1: str,
        parent_dev2: str
    ):
        """
        在两个网络的候选器件中寻找匹配对
        """
        # 遍历 net1 上的所有器件
        for (cand1_name, cand1_pin) in candidates1:
            # 排除掉自己（来源器件）
            if cand1_name == parent_dev1:
                continue
            
            # 如果这个器件已经被归类为对称对，跳过
            if cand1_name in self.constraint.processed_devices:
                continue

            cand1_data = devices[cand1_name]

            # 遍历 net2 上的所有器件，寻找 cand1 的“双胞胎”
            for (cand2_name, cand2_pin) in candidates2:
                if cand2_name == parent_dev2:
                    continue
                
                if cand2_name in self.constraint.processed_devices:
                    continue
                
                cand2_data = devices[cand2_name]

                # === 严格的匹配逻辑 ===
                
                # 1. 必须是同一类型的器件 (e.g. 都是 nmos)
                if cand1_data.get("type") != cand2_data.get("type"):
                    continue

                # 2. 必须是相同的引脚连接方式
                # 例如：如果 cand1 是用 Source 连在这个网上，cand2 也必须是用 Source 连在那个网上
                if not self._is_same_pin_role(cand1_pin, cand2_pin):
                    continue

                # 3. 必须具有相同的参数 (W, L, NF, M)
                if not self._are_params_identical(cand1_data, cand2_data):
                    continue

                # 4. 防止自引用 (cand1 和 cand2 是同一个器件)
                if cand1_name == cand2_name:
                    continue

                # === 发现新对称对 ===
                new_pair = SymmetryPair(
                    device1=cand1_name,
                    device2=cand2_name,
                    symmetry_type=SymmetryType.VERTICAL, # 传播得到的通常维持原有对称性
                    score=0.9 # 传播得到的置信度略低，但依然很高
                )
                
                # 记录并加入队列，以便继续向下传播
                self.constraint.symmetry_pairs.append(new_pair)
                self.constraint.processed_devices.add(cand1_name)
                self.constraint.processed_devices.add(cand2_name)
                queue.append(new_pair)
                
                # 找到匹配后，对于当前的 cand1 就不再找其他 cand2 了 (假设一对一匹配)
                break

    def _is_same_pin_role(self, pin1: str, pin2: str) -> bool:
        """检查两个引脚名是否代表相同的功能"""
        # 归一化处理：'D', 'd', 'Drain' -> 'd'
        p1 = pin1.lower()[0] # 取首字母
        p2 = pin2.lower()[0]
        return p1 == p2

    def _are_params_identical(self, d1: Dict, d2: Dict) -> bool:
        """比较两个器件的物理参数是否一致"""
        p1 = d1.get("parameters", {})
        p2 = d2.get("parameters", {})
        
        # 比较关键参数，允许极小的浮点误差
        keys_to_check = ['w', 'l', 'nf', 'm']
        for k in keys_to_check:
            val1 = float(p1.get(k, 0))
            val2 = float(p2.get(k, 0))
            if abs(val1 - val2) > 1e-9:
                return False
        return True

