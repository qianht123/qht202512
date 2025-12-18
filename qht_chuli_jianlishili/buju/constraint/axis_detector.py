"""
对称驱动布局生成器 (Symmetry-Driven Placer)
输入：
1. 逻辑约束 (Symmetry Constraints)
2. 器件物理尺寸 (Device Dimensions: Width, Height)
3. 拓扑层级 (Signal Levels)

输出：
生成的布局坐标 (X, Y) 和 旋转方向 (Orientation)
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from .symmetry import SymmetryConstraint, SymmetryType

@dataclass
class DeviceDimension:
    width: float
    height: float
    label: str

@dataclass
class PlacedInstance:
    name: str
    x: float        # 中心点 X
    y: float        # 中心点 Y
    width: float
    height: float
    orientation: str # R0 (默认), MX (镜像)

class SymmetryDrivenPlacer:
    
    def __init__(self, min_spacing: float = 1.0, row_spacing: float = 2.0):
        self.spacing = min_spacing    # 器件间水平间距
        self.row_spacing = row_spacing # 行间垂直间距
        self.placements: Dict[str, PlacedInstance] = {}

    def place(self, 
              dimensions: Dict[str, DeviceDimension], 
              constraint: SymmetryConstraint, 
              levels: Dict[str, int]) -> Dict[str, PlacedInstance]:
        """
        执行布局计算
        """
        self.placements = {}
        
        # 1. 将器件按 Row (Level) 分组
        rows = {}
        for name, level in levels.items():
            if level not in rows: rows[level] = []
            rows[level].append(name)
        
        # 按层级从下往上排 (Level 0 -> Y=0)
        sorted_levels = sorted(rows.keys())
        current_y_bottom = 0.0
        
        for level in sorted_levels:
            device_names = rows[level]
            
            # 2. 计算当前行的高度 (取该行最高器件)
            row_height = max([dimensions[d].height for d in device_names if d in dimensions], default=10.0)
            center_y = current_y_bottom + row_height / 2.0
            
            # 3. 行内布局 (核心算法)
            self._place_row(device_names, dimensions, constraint, center_y)
            
            # 更新下一行的起始Y
            current_y_bottom += row_height + self.row_spacing
            
        return self.placements

    def _place_row(self, 
                   row_devices: List[str], 
                   dimensions: Dict[str, DeviceDimension], 
                   constraint: SymmetryConstraint, 
                   center_y: float):
        """
        在单行内，基于 X=0 对称轴摆放器件
        策略：优先摆放对称对，由内向外 (Center-Out)
        """
        # 标记哪些器件已经处理过
        processed = set()
        
        # 1. 寻找该行内的对称对
        row_pairs = []
        for pair in constraint.symmetry_pairs:
            if pair.device1 in row_devices and pair.device2 in row_devices:
                row_pairs.append(pair)
                processed.add(pair.device1)
                processed.add(pair.device2)
        
        # 2. 寻找该行内的自对称器件 (假设在 constraint 中有记录，或者基于名字推断)
        # 这里简化：如果不在对称对里，且是单数，暂时视为普通器件，或者放在中心
        # 实际代码应从 constraint.self_symmetric_devices 获取
        
        # === 开始摆放 ===
        
        # current_x_cursor: 记录当前已经用到哪里了 (从中心向右的距离)
        # 初始时，如果有自对称器件，cursor 会被推开；如果没有，从 0 开始推
        cursor_x = 0.0 
        
        # A. 摆放对称对 (Symmetry Pairs)
        # 排序策略：通常共质心(Common Centroid)放最中间，普通镜像放两边
        # 这里简单按列表顺序
        for pair in row_pairs:
            d1_name, d2_name = pair.device1, pair.device2
            dim1, dim2 = dimensions[d1_name], dimensions[d2_name]
            
            # 计算这对器件占用的物理宽度
            # 如果是 Common Centroid (ABBA)，我们视为它们交织在一起，占据的总宽是 W1+W2
            # 如果是 Simple Mirror (A | B)，M1在左，M2在右
            
            # 这一对器件的各自半宽
            w1_half = dim1.width / 2.0
            w2_half = dim2.width / 2.0
            
            # 计算中心位置
            # M2 (右侧): 中心 = 当前游标 + 间距 + M2半宽
            pos_x_right = cursor_x + self.spacing + w2_half
            
            # M1 (左侧): 对称位置
            pos_x_left = -pos_x_right
            
            # 保存布局结果
            self.placements[d2_name] = PlacedInstance(
                name=d2_name, x=pos_x_right, y=center_y, 
                width=dim1.width, height=dim1.height, orientation="MX" # 右侧通常镜像
            )
            self.placements[d1_name] = PlacedInstance(
                name=d1_name, x=pos_x_left, y=center_y, 
                width=dim2.width, height=dim2.height, orientation="R0"
            )
            
            # 更新游标 (推到 M2 的右边缘)
            cursor_x = pos_x_right + w2_half

        # B. 摆放剩余非对称器件 (Remaining)
        # 简单策略：依次摆在最右边 (或者左边，看具体需求)
        for name in row_devices:
            if name not in processed:
                dim = dimensions[name]
                w_half = dim.width / 2.0
                pos_x = cursor_x + self.spacing + w_half
                
                self.placements[name] = PlacedInstance(
                    name=name, x=pos_x, y=center_y, 
                    width=dim.width, height=dim.height, orientation="R0"
                )
                
                cursor_x = pos_x + w_half

    def visualize(self):
        """使用 Matplotlib 绘制生成的 Floorplan"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 绘制中心轴
        ax.axvline(x=0, color='red', linestyle='--', label='Symmetry Axis')
        
        for name, p in self.placements.items():
            # 计算左下角坐标 (Matplotlib使用左下角+宽高)
            corner_x = p.x - p.width / 2.0
            corner_y = p.y - p.height / 2.0
            
            # 颜色区分
            color = 'skyblue'
            if p.orientation == 'MX': color = 'lightgreen'
            
            rect = patches.Rectangle((corner_x, corner_y), p.width, p.height, 
                                     linewidth=1, edgecolor='black', facecolor=color, alpha=0.8)
            ax.add_patch(rect)
            
            # 标签
            ax.text(p.x, p.y, f"{name}/{p.orientation}", 
                    ha='center', va='center', fontsize=9, color='black', weight='bold')

        ax.set_xlim(-50, 50) # 根据实际范围自动调整
        ax.set_ylim(-10, 50)
        ax.set_aspect('equal')
        ax.set_title("Auto-Generated Symmetry Placement")
        ax.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.show()


