from dataclasses import dataclass
import mmap
import struct
from typing import Any, List, Union

def _get_value(mem: mmap.mmap, offset: int, type: str) -> Any:
    return struct.unpack_from(type, mem, offset)[0]

def _get_string(mem: mmap.mmap, offset: int, length: int) -> str:
    return struct.unpack_from(f'{length}s', mem, offset)[0].strip(b'\x00').decode('latin-1')

@dataclass
class VarBuffer:
    """
    Represents a buffer containing telemetry data for a single tick.
    """
    _shared_mem: mmap.mmap
    _offset: int
    _buf_len: int
    is_memory_frozen: bool = False
    _frozen_memory: Union[bytes, None] = None

    @property
    def tick_count(self) -> int:
        return _get_value(self.get_memory(), self.buf_offset, 'i')

    @property
    def _buf_offset_raw(self) -> int:
        return _get_value(self._shared_mem, self._offset + 4, 'i')

    def freeze(self) -> None:
        self._frozen_memory = self._shared_mem[self._buf_offset_raw : self._buf_offset_raw + self._buf_len]
        self.is_memory_frozen = True

    def unfreeze(self) -> None:
        self._frozen_memory = None
        self.is_memory_frozen = False

    def get_memory(self) -> Union[mmap.mmap, bytes]:
        return self._frozen_memory if self.is_memory_frozen else self._shared_mem

    @property
    def buf_offset(self) -> int:
        return 0 if self.is_memory_frozen else self._buf_offset_raw

@dataclass
class Header:
    """
    Represents the main header for the iRacing shared memory map.
    """
    _shared_mem: mmap.mmap
    _offset: int = 0

    @property
    def version(self) -> int:
        return _get_value(self._shared_mem, self._offset, 'i')

    @property
    def status(self) -> int:
        return _get_value(self._shared_mem, self._offset + 4, 'i')

    @property
    def tick_rate(self) -> int:
        return _get_value(self._shared_mem, self._offset + 8, 'i')

    @property
    def session_info_update(self) -> int:
        return _get_value(self._shared_mem, self._offset + 12, 'i')

    @property
    def session_info_len(self) -> int:
        return _get_value(self._shared_mem, self._offset + 16, 'i')

    @property
    def session_info_offset(self) -> int:
        return _get_value(self._shared_mem, self._offset + 20, 'i')

    @property
    def num_vars(self) -> int:
        return _get_value(self._shared_mem, self._offset + 24, 'i')

    @property
    def var_header_offset(self) -> int:
        return _get_value(self._shared_mem, self._offset + 28, 'i')

    @property
    def num_buf(self) -> int:
        return _get_value(self._shared_mem, self._offset + 32, 'i')

    @property
    def buf_len(self) -> int:
        return _get_value(self._shared_mem, self._offset + 36, 'i')

    @property
    def var_buf(self) -> List[VarBuffer]:
        return [
            VarBuffer(self._shared_mem, 48 + i * 16, buf_len=self.buf_len)
            for i in range(self.num_buf)
        ]

@dataclass
class VarHeader:
    """
    Represents the header for a single telemetry variable.
    """
    _shared_mem: mmap.mmap
    _offset: int

    @property
    def type(self) -> int:
        return _get_value(self._shared_mem, self._offset, 'i')

    @property
    def offset(self) -> int:
        return _get_value(self._shared_mem, self._offset + 4, 'i')

    @property
    def count(self) -> int:
        return _get_value(self._shared_mem, self._offset + 8, 'i')

    @property
    def count_as_time(self) -> bool:
        return _get_value(self._shared_mem, self._offset + 12, '?')

    @property
    def name(self) -> str:
        return _get_string(self._shared_mem, self._offset + 16, 32)

    @property
    def desc(self) -> str:
        return _get_string(self._shared_mem, self._offset + 48, 64)

    @property
    def unit(self) -> str:
        return _get_string(self._shared_mem, self._offset + 112, 32)

@dataclass
class DiskSubHeader:
    """
    Represents the sub-header for a disk-based telemetry file.
    """
    _shared_mem: mmap.mmap
    _offset: int

    @property
    def session_start_date(self) -> int:
        return _get_value(self._shared_mem, self._offset, 'Q')

    @property
    def session_start_time(self) -> float:
        return _get_value(self._shared_mem, self._offset + 8, 'd')

    @property
    def session_end_time(self) -> float:
        return _get_value(self._shared_mem, self._offset + 16, 'd')

    @property
    def session_lap_count(self) -> int:
        return _get_value(self._shared_mem, self._offset + 24, 'i')

    @property
    def session_record_count(self) -> int:
        return _get_value(self._shared_mem, self._offset + 28, 'i')