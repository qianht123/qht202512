"""
GDSII format reader and writer
"""

import struct
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import IntEnum

from ..core.circuit import Circuit, Device, Pin
from ..core.geometry import Point, Rectangle, Shape
from ..core.technology import TechnologyDB


class GdsDataType(IntEnum):
    """GDSII data type enumeration"""
    HEADER = 0x0000
    BGNLIB = 0x0102
    LIBNAME = 0x0206
    UNITS = 0x0305
    ENDLIB = 0x0400
    BGNSTR = 0x0502
    STRNAME = 0x0606
    ENDEL = 0x0700
    BOUNDARY = 0x0800
    PATH = 0x0900
    SREF = 0x0A00
    AREF = 0x0B00
    TEXT = 0x0C00
    LAYER = 0x0D02
    DATATYPE = 0x0E02
    WIDTH = 0x0F03
    XY = 0x1003
    ENDEL = 0x1100
    SNAME = 0x1206
    COLROW = 0x1302
    TEXTNODE = 0x1400
    NODE = 0x1500
    BOX = 0x1600
    BOXTYPE = 0x1702
    PLEX = 0x1800
    BGNEXTN = 0x1A00
    ENDEXTN = 0x1B00
    TAPENUM = 0x1C01
    TAPECODE = 0x1D02
    STRCLASS = 0x1E02
    RESERVED = 0x1F00
    FORMAT = 0x2000
    MASK = 0x2102
    ENDMASKS = 0x2200
    LIBDIRSIZE = 0x2302
    SRFNAME = 0x2406
    LIBSECUR = 0x2502


@dataclass
class GdsRecord:
    """GDSII record structure"""
    record_type: int
    data_type: int
    data: bytes


class GdsReader:
    """GDSII file reader"""
    
    def __init__(self):
        self.records = []
        self.current_structure = None
        self.circuit = None
        
    def read(self, filename: str) -> Circuit:
        """Read GDSII file and return Circuit object"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"GDS file not found: {filename}")
        
        self.circuit = Circuit(name=os.path.splitext(os.path.basename(filename))[0])
        
        with open(filename, 'rb') as f:
            while True:
                record = self._read_record(f)
                if record is None:
                    break
                self.records.append(record)
                self._process_record(record)
        
        return self.circuit
    
    def _read_record(self, file) -> Optional[GdsRecord]:
        """Read a single GDSII record"""
        # Read record header
        header_data = file.read(2)
        if len(header_data) < 2:
            return None
        
        record_header = struct.unpack('>H', header_data)[0]
        record_type = (record_header >> 8) & 0xFF
        data_type = record_header & 0xFF
        
        # Read record length
        length_data = file.read(2)
        if len(length_data) < 2:
            return None
        
        length = struct.unpack('>H', length_data)[0]
        
        # Read record data
        data = b''
        if length > 0:
            data = file.read(length)
            if len(data) < length:
                return None
        
        return GdsRecord(record_type, data_type, data)
    
    def _process_record(self, record: GdsRecord):
        """Process a GDSII record"""
        if record.record_type == GdsDataType.BGNLIB:
            # Beginning of library
            pass
        elif record.record_type == GdsDataType.LIBNAME:
            # Library name
            lib_name = record.data.decode('ascii').rstrip('\x00')
            self.circuit.name = lib_name
        elif record.record_type == GdsDataType.UNITS:
            # Units information
            if len(record.data) == 16:
                units = struct.unpack('>dd', record.data)
                # units[0] = user units per database unit
                # units[1] = meters per database unit
                pass
        elif record.record_type == GdsDataType.BGNSTR:
            # Beginning of structure
            pass
        elif record.record_type == GdsDataType.STRNAME:
            # Structure name
            struct_name = record.data.decode('ascii').rstrip('\x00')
            self.current_structure = struct_name
        elif record.record_type == GdsDataType.BOUNDARY:
            # Boundary (polygon)
            self._process_boundary()
        elif record.record_type == GdsDataType.PATH:
            # Path
            self._process_path()
        elif record.record_type == GdsDataType.SREF:
            # Structure reference
            self._process_sref()
        elif record.record_type == GdsDataType.TEXT:
            # Text
            self._process_text()
        elif record.record_type == GdsDataType.LAYER:
            # Layer number
            pass
        elif record.record_type == GdsDataType.DATATYPE:
            # Data type
            pass
        elif record.record_type == GdsDataType.XY:
            # Coordinates
            self._process_xy(record)
        elif record.record_type == GdsDataType.WIDTH:
            # Width
            pass
        elif record.record_type == GdsDataType.ENDSTR:
            # End of structure
            self.current_structure = None
        elif record.record_type == GdsDataType.ENDLIB:
            # End of library
            pass
    
    def _process_boundary(self):
        """Process boundary record"""
        # This would create a polygon shape
        pass
    
    def _process_path(self):
        """Process path record"""
        # This would create a path/wire shape
        pass
    
    def _process_sref(self):
        """Process structure reference"""
        # This would create a device instance
        pass
    
    def _process_text(self):
        """Process text record"""
        # This would create text annotation
        pass
    
    def _process_xy(self, record: GdsRecord):
        """Process XY coordinates"""
        # XY coordinates are stored as 4-byte integers
        num_points = len(record.data) // 8
        if num_points > 0:
            points = struct.unpack('>' + 'ii' * num_points, record.data)
            # Process points...
            pass


class GdsWriter:
    """GDSII file writer"""
    
    def __init__(self):
        self.records = []
        
    def write(self, circuit: Circuit, filename: str, tech_db: Optional[TechnologyDB] = None):
        """Write Circuit to GDSII file"""
        self.circuit = circuit
        self.tech_db = tech_db
        
        # Initialize records
        self.records = []
        
        # Write header
        self._write_header()
        
        # Write structures (devices)
        for device in circuit.devices.values():
            if device.position:
                self._write_device(device)
        
        # Write top level structure
        self._write_top_structure()
        
        # Write footer
        self._write_footer()
        
        # Write to file
        with open(filename, 'wb') as f:
            for record in self.records:
                self._write_record(f, record)
    
    def _write_header(self):
        """Write GDSII header"""
        # Library begin
        self._add_record(GdsDataType.BGNLIB, b'\x00\x01\x03\x07\x02')  # Modified time
        self._add_record(GdsDataType.LIBNAME, self.circuit.name.encode('ascii'))
        
        # Units (user units per database unit, meters per database unit)
        units_data = struct.pack('>dd', 0.001, 1e-9)  # 1nm database units
        self._add_record(GdsDataType.UNITS, units_data)
    
    def _write_footer(self):
        """Write GDSII footer"""
        # Library end
        self._add_record(GdsDataType.ENDLIB, b'')
    
    def _write_device(self, device: Device):
        """Write a device as a structure"""
        # Structure begin
        self._add_record(GdsDataType.BGNSTR, b'\x00\x01\x03\x07\x02')
        
        # Structure name
        self._add_record(GdsDataType.STRNAME, device.name.encode('ascii'))
        
        # Write device geometry
        bbox = device.get_bounding_box()
        if bbox:
            self._write_rectangle(bbox, layer=1)  # Default layer
        
        # Structure end
        self._add_record(GdsDataType.ENDSTR, b'')
    
    def _write_top_structure(self):
        """Write top level structure with all devices"""
        # Structure begin
        self._add_record(GdsDataType.BGNSTR, b'\x00\x01\x03\x07\x02')
        
        # Structure name
        self._add_record(GdsDataType.STRNAME, b'TOP')
        
        # Write all devices as structure references
        for device in self.circuit.devices.values():
            if device.position:
                self._write_sref(device)
        
        # Structure end
        self._add_record(GdsDataType.ENDSTR, b'')
    
    def _write_rectangle(self, rect: Rectangle, layer: int, datatype: int = 0):
        """Write a rectangle"""
        # Boundary
        self._add_record(GdsDataType.BOUNDARY, b'')
        
        # Layer
        layer_data = struct.pack('>H', layer)
        self._add_record(GdsDataType.LAYER, layer_data)
        
        # Data type
        datatype_data = struct.pack('>H', datatype)
        self._add_record(GdsDataType.DATATYPE, datatype_data)
        
        # XY coordinates (5 points for rectangle)
        points = [
            (rect.lower_left.x, rect.lower_left.y),
            (rect.upper_right.x, rect.lower_left.y),
            (rect.upper_right.x, rect.upper_right.y),
            (rect.lower_left.x, rect.upper_right.y),
            (rect.lower_left.x, rect.lower_left.y)
        ]
        
        xy_data = b''
        for x, y in points:
            xy_data += struct.pack('>ii', int(x), int(y))
        
        self._add_record(GdsDataType.XY, xy_data)
        
        # ENDEL
        self._add_record(GdsDataType.ENDEL, b'')
    
    def _write_sref(self, device: Device):
        """Write structure reference"""
        # SREF
        self._add_record(GdsDataType.SREF, b'')
        
        # SNAME (structure name)
        self._add_record(GdsDataType.SNAME, device.name.encode('ascii'))
        
        # XY (position)
        if device.position:
            xy_data = struct.pack('>ii', int(device.position.x), int(device.position.y))
            self._add_record(GdsDataType.XY, xy_data)
        
        # ENDEL
        self._add_record(GdsDataType.ENDEL, b'')
    
    def _add_record(self, record_type: int, data: bytes):
        """Add a record to the list"""
        data_type = 0
        
        # Determine data type based on record type and data
        if record_type == GdsDataType.BGNLIB:
            data_type = 0x02
        elif record_type in [GdsDataType.LIBNAME, GdsDataType.STRNAME, GdsDataType.SNAME]:
            data_type = 0x06
        elif record_type == GdsDataType.UNITS:
            data_type = 0x05
        elif record_type in [GdsDataType.LAYER, GdsDataType.DATATYPE]:
            data_type = 0x02
        elif record_type == GdsDataType.XY:
            data_type = 0x03
        elif record_type in [GdsDataType.BOUNDARY, GdsDataType.SREF, GdsDataType.ENDEL]:
            data_type = 0x00
        
        self.records.append(GdsRecord(record_type, data_type, data))
    
    def _write_record(self, file, record: GdsRecord):
        """Write a record to file"""
        # Record header
        header = (record.record_type << 8) | record.data_type
        file.write(struct.pack('>H', header))
        
        # Record length
        file.write(struct.pack('>H', len(record.data)))
        
        # Record data
        file.write(record.data)


# Test function
if __name__ == "__main__":
    # Create a simple test circuit
    from ..core.circuit import Circuit, Device, DeviceType, Net, NetType, Pin
    from ..core.geometry import Point, Rectangle
    
    circuit = Circuit(name="test_circuit")
    
    # Add some nets
    vdd_net = Net(name="VDD", net_type=NetType.POWER)
    gnd_net = Net(name="GND", net_type=NetType.GROUND)
    circuit.add_net(vdd_net)
    circuit.add_net(gnd_net)
    
    # Add a device
    device = Device(
        name="TEST_MOS",
        device_type=DeviceType.NMOS,
        parameters={"W": "1u", "L": "40n"},
        position=Point(100, 100),
        width=10,
        height=5
    )
    circuit.add_device(device)
    
    # Write GDS
    writer = GdsWriter()
    writer.write(circuit, "test.gds")
    
    print("GDS file written to test.gds")
    
    # Read it back
    reader = GdsReader()
    read_circuit = reader.read("test.gds")
    
    print(f"Read circuit: {read_circuit.name}")
    print(f"Devices: {list(read_circuit.devices.keys())}")
    
    # Clean up
    os.remove("test.gds")