import mmap
import struct
from typing import Any, Dict, List, Optional, TextIO

from .constants import VAR_TYPE_MAP
from .structs import DiskSubHeader, Header, VarHeader


class IBT:
    def __init__(self) -> None:
        self._ibt_file: Optional[TextIO] = None
        self._shared_mem: Optional[mmap.mmap] = None
        self._header: Optional[Header] = None
        self._disk_header: Optional[DiskSubHeader] = None

        self.__var_headers: Optional[List[VarHeader]] = None
        self.__var_headers_dict: Optional[Dict[str, VarHeader]] = None
        self.__var_headers_names: Optional[List[str]] = None
        self.__session_info_dict: Optional[dict] = None

    def __getitem__(self, key: str) -> Any:
        return self.get(self._disk_header.session_record_count - 1, key)

    @property
    def file_name(self) -> Optional[str]:
        return self._ibt_file and self._ibt_file.name

    @property
    def var_header_buffer_tick(self) -> Optional[int]:
        return self._header and self._header.var_buf[0].tick_count

    @property
    def var_headers_names(self) -> Optional[List[str]]:
        if not self._header:
            return None
        if self.__var_headers_names is None:
            self.__var_headers_names = [var_header.name for var_header in self._var_headers]
        return self.__var_headers_names

    def open(self, ibt_file: str) -> None:
        self._ibt_file = open(ibt_file, 'rb')
        self._shared_mem = mmap.mmap(self._ibt_file.fileno(), 0, access=mmap.ACCESS_READ)
        self._header = Header(self._shared_mem)
        self._disk_header = DiskSubHeader(self._shared_mem, 112)

    def close(self) -> None:
        if self._shared_mem:
            self._shared_mem.close()

        if self._ibt_file:
            self._ibt_file.close()

        self._ibt_file = None
        self._shared_mem = None
        self._header = None
        self._disk_header = None

        self.__var_headers = None
        self.__var_headers_dict = None
        self.__var_headers_names = None
        self.__session_info_dict = None

    def get(self, index: int, key: str) -> Any:
        if not self._header:
            return None
        if not (0 <= index < self._disk_header.session_record_count):
            return None
        if key in self._var_headers_dict:
            var_header = self._var_headers_dict[key]
            fmt = VAR_TYPE_MAP[var_header.type] * var_header.count
            var_offset = var_header.offset + self._header.var_buf[0].buf_offset + index * self._header.buf_len
            res = struct.unpack_from(fmt, self._shared_mem, var_offset)
            return list(res) if var_header.count > 1 else res[0]
        return None

    def get_all(self, key: str) -> Optional[List[Any]]:
        if not self._header:
            return None
        if key in self._var_headers_dict:
            var_header = self._var_headers_dict[key]
            fmt = VAR_TYPE_MAP[var_header.type] * var_header.count
            var_offset = var_header.offset + self._header.var_buf[0].buf_offset
            buf_len = self._header.buf_len
            is_array = var_header.count > 1
            results = []
            for i in range(self._disk_header.session_record_count):
                res = struct.unpack_from(fmt, self._shared_mem, var_offset + i * buf_len)
                results.append(list(res) if is_array else res[0])
            return results
        return None

    @property
    def _var_headers(self) -> Optional[List[VarHeader]]:
        if not self._header:
            return None
        if self.__var_headers is None:
            self.__var_headers = []
            for i in range(self._header.num_vars):
                var_header = VarHeader(self._shared_mem, self._header.var_header_offset + i * 144)
                self._var_headers.append(var_header)
        return self.__var_headers

    @property
    def _var_headers_dict(self) -> Optional[Dict[str, VarHeader]]:
        if not self._header:
            return None
        if self.__var_headers_dict is None:
            self.__var_headers_dict = {}
            for var_header in self._var_headers:
                self.__var_headers_dict[var_header.name] = var_header
        return self.__var_headers_dict