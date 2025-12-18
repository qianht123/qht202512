# 布局引擎 (buju) - 对称约束检测模块

## 概述

这个模块实现了模拟集成电路布局中的对称约束检测功能，能够自动从电路网表中识别对称结构并生成相应的约束。

## 功能特性

### 1. 对称约束自动检测
- **差分对检测**: 识别共享栅极和源极的MOSFET对
- **电流镜检测**: 识别栅极-漏极相连的MOSFET对
- **自对称器件检测**: 识别多指器件等自对称结构

### 2. 对称约束文件解析
- 支持`.sym`格式文件解析
- 支持对称器件对、对称组、自对称器件
- 约束验证和错误检查

### 3. 对称轴自动检测
- 基于对称器件对计算对称轴位置
- 基于电路拓扑结构检测对称性
- 对称轴位置优化

## 模块结构

```
buju/
├── __init__.py                 # 模块初始化
├── README.md                   # 说明文档
├── constraint/                 # 约束管理
│   ├── __init__.py
│   ├── symmetry.py            # 对称约束检测
│   ├── parser.py              # 约束文件解析
│   └── axis_detector.py       # 对称轴检测
├── database/                   # 数据结构 (待实现)
├── global/                     # 全局布局 (待实现)
├── legalization/              # 合法化 (待实现)
├── optimization/              # 优化算法 (待实现)
└── tests/                     # 测试用例
    ├── __init__.py
    └── test_symmetry.py
```

## 使用方法

### 1. 基本使用

```python
from buju.constraint.symmetry import SymmetryDetector
from buju.constraint.parser import SymmetryParser
from buju.constraint.axis_detector import SymmetryAxisDetector

# 创建电路数据
devices = {
    "M1": {
        "type": "nmos",
        "w": 10.0, "l": 0.5, "nf": 1,
        "pins": [
            {"name": "G", "net": "VIN"},
            {"name": "D", "net": "OUT1"},
            {"name": "S", "net": "VSS"}
        ]
    },
    # ... 更多器件
}

nets = {
    "VIN": {
        "pins": [
            {"device": "M1", "pin": "G"},
            {"device": "M2", "pin": "G"}
        ]
    },
    # ... 更多网络
}

# 1. 检测对称约束
detector = SymmetryDetector()
constraint = detector.detect_symmetry_from_nets(devices, nets)

# 2. 检测对称轴
axis_detector = SymmetryAxisDetector()
axis = axis_detector.detect_symmetry_axis(devices, nets, constraint)

# 3. 生成约束文件
parser = SymmetryParser()
parser.generate_symmetry_file(constraint, "output.sym")
```

### 2. 手动添加对称约束

```python
# 添加对称器件对
detector.add_symmetry_pair("M1", "M2", SymmetryType.VERTICAL)

# 添加对称组
detector.add_symmetry_group(["M3", "M4", "M5", "M6"], SymmetryType.VERTICAL)

# 添加自对称器件
detector.add_self_symmetric_device("M7")
```

### 3. 解析约束文件

```python
parser = SymmetryParser()
constraint = parser.parse_symmetry_file("input.sym")

# 验证约束
available_devices = ["M1", "M2", "M3", "M4"]
errors = parser.validate_constraints(constraint, available_devices)
```

## 约束文件格式

`.sym`文件支持以下格式：

```
# 对称轴位置
SYMMETRY_AXIS 100.0

# 对称器件对 (默认垂直对称)
SYMMETRY_PAIR M1 M2
SYMMETRY_PAIR M3 M4

# 对称器件对 (水平对称)
SYMMETRY_PAIR M5 M6 HORIZONTAL

# 对称组
SYMMETRY_GROUP M7 M8 M9 M10

# 自对称器件
SELF_SYMMETRY M11 M12
```

## 测试

运行测试用例：

```bash
cd /install/MAGICAL/qht_chuli_jianlishili
python3 test_symmetry_demo.py
```

## 下一步开发

1. **数据结构模块**: 实现器件、网络、布局数据库
2. **全局布局算法**: 实现力导向布局、模拟退火等算法
3. **合法化模块**: 实现器件放置合法化
4. **优化算法**: 实现线长优化、对称约束优化

## 注意事项

1. 当前版本主要针对MOSFET器件的对称检测
2. 对称轴检测基于器件重要性估算，实际布局时需要结合器件位置
3. 约束文件解析器支持基本的格式，可根据需要扩展
4. 测试用例包含简单的差分对和电流镜结构

## 作者信息

- 创建时间: 2025-12-18
- 模块版本: v0.1.0
- Python版本: 3.7+
