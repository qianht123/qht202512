"""
Geometry primitives for layout representation
"""

from typing import Tuple, List, Union
from dataclasses import dataclass
from enum import Enum


class ShapeType(Enum):
    """Shape type enumeration"""
    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    CIRCLE = "circle"


@dataclass
class Point:
    """2D Point representation"""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
    def manhattan_distance(self, other: 'Point') -> float:
        """Calculate Manhattan distance to another point"""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple representation"""
        return (self.x, self.y)


@dataclass
class Rectangle:
    """Rectangle representation"""
    lower_left: Point
    upper_right: Point
    
    @property
    def width(self) -> float:
        """Get rectangle width"""
        return self.upper_right.x - self.lower_left.x
    
    @property
    def height(self) -> float:
        """Get rectangle height"""
        return self.upper_right.y - self.lower_left.y
    
    @property
    def center(self) -> Point:
        """Get rectangle center point"""
        return Point(
            (self.lower_left.x + self.upper_right.x) / 2,
            (self.lower_left.y + self.upper_right.y) / 2
        )
    
    @property
    def area(self) -> float:
        """Get rectangle area"""
        return self.width * self.height
    
    def contains_point(self, point: Point) -> bool:
        """Check if point is inside rectangle (including boundary)"""
        return (self.lower_left.x <= point.x <= self.upper_right.x and
                self.lower_left.y <= point.y <= self.upper_right.y)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """Check if this rectangle intersects with another"""
        return not (self.upper_right.x < other.lower_left.x or
                   other.upper_right.x < self.lower_left.x or
                   self.upper_right.y < other.lower_left.y or
                   other.upper_right.y < self.lower_left.y)
    
    def union(self, other: 'Rectangle') -> 'Rectangle':
        """Get union rectangle containing both rectangles"""
        return Rectangle(
            Point(min(self.lower_left.x, other.lower_left.x),
                  min(self.lower_left.y, other.lower_left.y)),
            Point(max(self.upper_right.x, other.upper_right.x),
                  max(self.upper_right.y, other.upper_right.y))
        )
    
    def to_tuple(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Convert to tuple representation"""
        return (self.lower_left.to_tuple(), self.upper_right.to_tuple())


class Shape:
    """Generic shape base class"""
    
    def __init__(self, shape_type: ShapeType):
        self.shape_type = shape_type
    
    def get_bbox(self) -> Rectangle:
        """Get bounding box of the shape"""
        raise NotImplementedError("Subclasses must implement get_bbox")
    
    def contains_point(self, point: Point) -> bool:
        """Check if point is inside the shape"""
        raise NotImplementedError("Subclasses must implement contains_point")


class RectShape(Shape):
    """Rectangle shape implementation"""
    
    def __init__(self, rectangle: Rectangle):
        super().__init__(ShapeType.RECTANGLE)
        self.rectangle = rectangle
    
    def get_bbox(self) -> Rectangle:
        return self.rectangle
    
    def contains_point(self, point: Point) -> bool:
        return self.rectangle.contains_point(point)


class Polygon(Shape):
    """Polygon shape implementation"""
    
    def __init__(self, points: List[Point]):
        super().__init__(ShapeType.POLYGON)
        self.points = points
        self._bbox = None
    
    def get_bbox(self) -> Rectangle:
        """Calculate and cache bounding box"""
        if self._bbox is None:
            min_x = min(p.x for p in self.points)
            max_x = max(p.x for p in self.points)
            min_y = min(p.y for p in self.points)
            max_y = max(p.y for p in self.points)
            self._bbox = Rectangle(Point(min_x, min_y), Point(max_x, max_y))
        return self._bbox
    
    def contains_point(self, point: Point) -> bool:
        """Point-in-polygon test using ray casting algorithm"""
        if not self.get_bbox().contains_point(point):
            return False
        
        n = len(self.points)
        inside = False
        
        p1x, p1y = self.points[0].x, self.points[0].y
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n].x, self.points[i % n].y
            if point.y > min(p1y, p2y):
                if point.y <= max(p1y, p2y):
                    if point.x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (point.y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or point.x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside