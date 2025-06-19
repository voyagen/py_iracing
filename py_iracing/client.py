import ctypes
import asyncio
import mmap
import re
import struct
from typing import Any, Dict, List, Optional, TextIO, Union
import aiohttp
import yaml
from yaml.reader import Reader as YamlReader

from .constants import (
    BROADCAST_MSG_NAME, DATA_VALID_EVENT_NAME, MEM_MAP_FILE, MEM_MAP_FILE_SIZE,
    SIM_STATUS_URL, VAR_TYPE_MAP, YAML_CODE_PAGE, YAML_TRANSLATER
)
from .enums import (
    BroadcastMsg, CameraState, ChatCommandMode, FFBCommandMode,
    PitCommandMode, ReloadTexturesMode, ReplayPositionMode, ReplaySearchMode,
    ReplayStateMode, StatusField, TelemCommandMode, VideoCaptureMode
)
from .structs import Header, VarBuffer, VarHeader
from .yaml_parser import CustomYamlSafeLoader


class iRacingClient:
    """
    The main class for interacting with the iRacing SDK.

    This class provides methods for getting session data, live telemetry data, and broadcasting messages to the iRacing simulator.
    It uses asyncio for non-blocking I/O, making it suitable for real-time applications.
    """

    def __init__(self) -> None:
        """
        Initializes the iRacingClient.
        """
        self.is_initialized = False
        self.last_session_info_update = 0

        self._shared_mem: Optional[mmap.mmap] = None
        self._header: Optional[Header] = None
        self._data_valid_event: Optional[int] = None

        self.__var_headers: Optional[List[VarHeader]] = None
        self.__var_headers_dict: Optional[Dict[str, VarHeader]] = None
        self.__var_headers_names: Optional[List[str]] = None
        self.__var_buffer_latest: Optional[VarBuffer] = None
        self.__session_info_dict: Dict[str, dict] = {}
        self.__broadcast_msg_id: Optional[int] = None
        self.__test_file: Optional[TextIO] = None
        self.__workaround_connected_state = 0

    def __getitem__(self, key: str) -> Union[int, float, bool, str, List[Any], None]:
        raise NotImplementedError("Use get() for asynchronous access.")

    async def get(self, key: str) -> Union[int, float, bool, str, List[Any], None]:
        if self._var_headers_dict and key in self._var_headers_dict:
            var_header = self._var_headers_dict[key]
            var_buf_latest = self._var_buffer_latest
            res = struct.unpack_from(
                VAR_TYPE_MAP[var_header.type] * var_header.count,
                var_buf_latest.get_memory(),
                var_buf_latest.buf_offset + var_header.offset)
            return res[0] if var_header.count == 1 else list(res)

        return await self._get_session_info(key)

    async def is_connected(self) -> bool:
        if self._header:
            if self._header.status == StatusField.status_connected:
                self.__workaround_connected_state = 0
            if self.__workaround_connected_state == 0 and self._header.status != StatusField.status_connected:
                self.__workaround_connected_state = 1
            if self.__workaround_connected_state == 1 and (await self.get('SessionNum') is None or self.__test_file):
                self.__workaround_connected_state = 2
            if self.__workaround_connected_state == 2 and await self.get('SessionNum') is not None:
                self.__workaround_connected_state = 3
        return self._header is not None and \
            (self.__test_file or self._data_valid_event) and \
            (self._header.status == StatusField.status_connected or self.__workaround_connected_state == 3)

    @property
    def session_info_update(self) -> int:
        """
        The last time the session info was updated.
        """
        return self._header.session_info_update

    @property
    def var_headers_names(self) -> Optional[List[str]]:
        """
        A list of all the telemetry variable names.
        """
        if self.__var_headers_names is None:
            self.__var_headers_names = [var_header.name for var_header in self._var_headers]
        return self.__var_headers_names

    async def startup(self, test_file: Optional[str] = None, dump_to: Optional[str] = None) -> bool:
        """
        Connects to the iRacing simulator and initializes the client.

        Args:
            test_file: Path to a test file to use instead of live data.
            dump_to: Path to dump the shared memory to a file.

        Returns:
            True if the client was successfully initialized, False otherwise.
        """
        if test_file is None:
            # Check if the simulator is running
            if not await self._check_sim_status():
                return False
            self._data_valid_event = ctypes.windll.kernel32.OpenEventW(0x00100000, False, DATA_VALID_EVENT_NAME)
        if not await self._wait_valid_data_event():
            self._data_valid_event = None
            return False

        if self._shared_mem is None:
            if test_file:
                self.__test_file = open(test_file, 'rb')
                self._shared_mem = mmap.mmap(self.__test_file.fileno(), 0, access=mmap.ACCESS_READ)
            else:
                self._shared_mem = mmap.mmap(0, MEM_MAP_FILE_SIZE, MEM_MAP_FILE, access=mmap.ACCESS_READ)

        if self._shared_mem:
            if dump_to:
                with open(dump_to, 'wb') as f:
                    f.write(self._shared_mem)
            self._header = Header(_shared_mem=self._shared_mem)
            self.is_initialized = self._header.version >= 1 and len(self._header.var_buf) > 0

        return self.is_initialized

    def shutdown(self) -> None:
        """
        Shuts down the iRacingClient and releases all resources.
        """
        self.is_initialized = False
        self.last_session_info_update = 0
        if self._shared_mem:
            self._shared_mem.close()
            self._shared_mem = None
        self._header = None
        self._data_valid_event = None
        self.__var_headers = None
        self.__var_headers_dict = None
        self.__var_headers_names = None
        self.__var_buffer_latest = None
        self.__session_info_dict = {}
        self.__broadcast_msg_id = None
        if self.__test_file:
            self.__test_file.close()
            self.__test_file = None

    def parse_to(self, to_file: str) -> None:
        """
        Parses the session info YAML and telemetry data to a file.

        Args:
            to_file: The path to the file to write the data to.
        """
        if not self.is_initialized:
            return
        with open(to_file, 'w', encoding='utf-8') as f:
            f.write(self._shared_mem[self._header.session_info_offset:self._header.session_info_len].rstrip(b'\x00').decode(YAML_CODE_PAGE))
            f.write('\n'.join([
                '{:32}{}'.format(i, self[i])
                for i in sorted(self._var_headers_dict.keys(), key=str.lower)
            ]))

    def cam_switch_pos(self, position: int = 0, group: int = 1, camera: int = 0) -> int:
        """
        Switches the camera to a specific position.

        Args:
            position: The position to switch to.
            group: The camera group to use.
            camera: The camera to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.cam_switch_pos, position, group, camera)

    def cam_switch_num(self, car_number: str = '1', group: int = 1, camera: int = 0) -> int:
        """
        Switches the camera to a specific car number.

        Args:
            car_number: The car number to switch to.
            group: The camera group to use.
            camera: The camera to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.cam_switch_num, self._pad_car_num(car_number), group, camera)

    def cam_set_state(self, camera_state: CameraState = CameraState.cam_tool_active) -> int:
        """
        Sets the state of the camera.

        Args:
            camera_state: The camera state to set.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.cam_set_state, camera_state)

    def replay_set_play_speed(self, speed: int = 0, slow_motion: bool = False) -> int:
        """
        Sets the replay play speed.

        Args:
            speed: The speed to set.
            slow_motion: Whether to use slow motion.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.replay_set_play_speed, speed, 1 if slow_motion else 0)

    def replay_set_play_position(self, pos_mode: ReplayPositionMode = ReplayPositionMode.begin, frame_num: int = 0) -> int:
        """
        Sets the replay play position.

        Args:
            pos_mode: The position mode to use.
            frame_num: The frame number to seek to.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.replay_set_play_position, pos_mode, frame_num)

    def replay_search(self, search_mode: ReplaySearchMode = ReplaySearchMode.to_start) -> int:
        """
        Searches the replay.

        Args:
            search_mode: The search mode to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.replay_search, search_mode)

    def replay_set_state(self, state_mode: ReplayStateMode = ReplayStateMode.erase_tape) -> int:
        """
        Sets the replay state.

        Args:
            state_mode: The state mode to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.replay_set_state, state_mode)

    def reload_all_textures(self) -> int:
        """
        Reloads all car textures.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.reload_textures, ReloadTexturesMode.all)

    def reload_texture(self, car_idx: int = 0) -> int:
        """
        Reloads the texture for a specific car.

        Args:
            car_idx: The car index to reload the texture for.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.reload_textures, ReloadTexturesMode.car_idx, car_idx)

    def chat_command(self, chat_command_mode: ChatCommandMode = ChatCommandMode.begin_chat) -> int:
        """
        Sends a chat command.

        Args:
            chat_command_mode: The chat command mode to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.chat_command, chat_command_mode)

    def chat_command_macro(self, macro_num: int = 0) -> int:
        """
        Sends a chat command macro.

        Args:
            macro_num: The macro number to send.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.chat_command, ChatCommandMode.macro, macro_num)

    def pit_command(self, pit_command_mode: PitCommandMode = PitCommandMode.clear, var: int = 0) -> int:
        """
        Sends a pit command.

        Args:
            pit_command_mode: The pit command mode to use.
            var: An optional variable for the pit command.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.pit_command, pit_command_mode, var)

    def telem_command(self, telem_command_mode: TelemCommandMode = TelemCommandMode.stop) -> int:
        """
        Sends a telemetry command.

        Args:
            telem_command_mode: The telemetry command mode to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.telem_command, telem_command_mode)

    def ffb_command(self, ffb_command_mode: FFBCommandMode = FFBCommandMode.ffb_command_max_force, value: float = 0) -> int:
        """
        Sends a force feedback command.

        Args:
            ffb_command_mode: The force feedback command mode to use.
            value: The value for the command.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.ffb_command, ffb_command_mode, int(value * 65536))

    def replay_search_session_time(self, session_num: int = 0, session_time_ms: int = 0) -> int:
        """
        Searches the replay to a specific session time.

        Args:
            session_num: The session number to search in.
            session_time_ms: The session time in milliseconds to search for.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.replay_search_session_time, session_num, session_time_ms)

    def video_capture(self, video_capture_mode: VideoCaptureMode = VideoCaptureMode.trigger_screen_shot) -> int:
        """
        Sends a video capture command.

        Args:
            video_capture_mode: The video capture mode to use.

        Returns:
            The result of the broadcast message.
        """
        return self._broadcast_msg(BroadcastMsg.video_capture, video_capture_mode)

    async def _check_sim_status(self) -> bool:
        """
        Checks if the iRacing simulator is running.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SIM_STATUS_URL) as response:
                    text = await response.text()
                    return 'running:1' in text
        except aiohttp.ClientError as e:
            print(f"Failed to connect to sim: {e}")
            return False

    @property
    def _var_buffer_latest(self) -> Optional[VarBuffer]:
        """
        The latest telemetry variable buffer.
        """
        if self._header:
            return sorted(self._header.var_buf, key=lambda v: v.tick_count, reverse=True)[1]
        return None

    @property
    def _var_headers(self) -> Optional[List[VarHeader]]:
        """
        A list of all the telemetry variable headers.
        """
        if self.__var_headers is None and self._header:
            self.__var_headers = []
            for i in range(self._header.num_vars):
                var_header = VarHeader(_shared_mem=self._shared_mem, offset=self._header.var_header_offset + i * 144)
                self._var_headers.append(var_header)
        return self.__var_headers

    @property
    def _var_headers_dict(self) -> Optional[Dict[str, VarHeader]]:
        """
        A dictionary of all the telemetry variable headers, keyed by name.
        """
        if self.__var_headers_dict is None and self._var_headers:
            self.__var_headers_dict = {}
            for var_header in self._var_headers:
                self.__var_headers_dict[var_header.name] = var_header
        return self.__var_headers_dict

    def freeze_var_buffer_latest(self) -> None:
        self.unfreeze_var_buffer_latest()
        self._wait_valid_data_event()
        if self._header:
            self.__var_buffer_latest = sorted(self._header.var_buf, key=lambda v: v.tick_count, reverse=True)[0]
            self.__var_buffer_latest.freeze()

    def unfreeze_var_buffer_latest(self) -> None:
        if self.__var_buffer_latest:
            self.__var_buffer_latest.unfreeze()
            self.__var_buffer_latest = None

    def get_session_info_update_by_key(self, key: str) -> Optional[int]:
        if key in self.__session_info_dict:
            return self.__session_info_dict[key].get('update')
        return None

    async def _wait_valid_data_event(self) -> bool:
        """
        Waits for the data valid event to be set by the iRacing simulator.
        """
        if self._data_valid_event is not None:
            return await asyncio.to_thread(ctypes.windll.kernel32.WaitForSingleObject, self._data_valid_event, 32) == 0
        return True

    async def _get_session_info(self, key: str) -> Union[Dict[str, Any], None]:
        """
        Gets a value from the session info YAML.
        """
        if self._header and self.last_session_info_update < self._header.session_info_update:
            self.last_session_info_update = self._header.session_info_update
            for session_data in self.__session_info_dict.values():
                if 'data' in session_data and session_data['data']:
                    session_data['data_last'] = session_data['data']
                session_data['data'] = None

        if key not in self.__session_info_dict:
            self.__session_info_dict[key] = {'data': None}

        session_data = self.__session_info_dict[key]

        if session_data.get('data'):
            return session_data['data']

        await self._parse_yaml(key, session_data)
        return session_data.get('data')

    def _get_session_info_binary(self, key: str) -> Optional[bytes]:
        """
        Gets a value from the session info YAML as a binary string.
        """
        if not self._header:
            return None
        start = self._header.session_info_offset
        end = start + self._header.session_info_len
        match_start = re.compile(('\n%s:\n' % key).encode(YAML_CODE_PAGE)).search(self._shared_mem, start, end)
        if not match_start:
            return None
        match_end = re.compile(b'\n\n').search(self._shared_mem, match_start.start() + 1, end)
        if not match_end:
            return None
        return self._shared_mem[match_start.start() + 1: match_end.start()]

    async def _parse_yaml(self, key: str, session_data: dict) -> None:
        """
        Parses the session info YAML.
        """
        session_info_update = self.last_session_info_update
        data_binary = self._get_session_info_binary(key)

        if not data_binary:
            if 'data_last' in session_data:
                session_data['data'] = session_data['data_last']
            return

        if 'data_binary' in session_data and data_binary == session_data['data_binary'] and 'data_last' in session_data:
            session_data['data'] = session_data['data_last']
            return
        session_data['data_binary'] = data_binary

        yaml_src = await asyncio.to_thread(self._prepare_yaml, data_binary, key)
        result = await asyncio.to_thread(yaml.load, yaml_src, Loader=CustomYamlSafeLoader)
        if result and self.last_session_info_update == session_info_update:
            session_data['data'] = result.get(key)
            if session_data['data']:
                session_data['update'] = session_info_update
            elif 'data_last' in session_data:
                session_data['data'] = session_data['data_last']

    def _prepare_yaml(self, data_binary: bytes, key: str) -> str:
        """
        Prepares the session info YAML for parsing.
        """
        yaml_src = re.sub(YamlReader.NON_PRINTABLE, '', data_binary.translate(YAML_TRANSLATER).rstrip(b'\x00').decode(YAML_CODE_PAGE))
        if key == 'DriverInfo':
            def name_replace(m: re.Match) -> str:
                return m.group(1) + '"%s"' % re.sub(r'(["\\])', r'\\\1', m.group(2))
            yaml_src = re.sub(r'((?:DriverSetupName|UserName|TeamName|AbbrevName|Initials): )(.*)', name_replace, yaml_src)
        yaml_src = re.sub(r'(\w+: )(,.*)', r'\1"\2"', yaml_src)
        return yaml_src

    @property
    def _broadcast_msg_id(self) -> int:
        """
        The ID of the broadcast message for sending commands to iRacing.
        """
        if self.__broadcast_msg_id is None:
            self.__broadcast_msg_id = ctypes.windll.user32.RegisterWindowMessageW(BROADCAST_MSG_NAME)
        return self.__broadcast_msg_id

    def _broadcast_msg(self, broadcast_type: int = 0, var1: int = 0, var2: int = 0, var3: int = 0) -> int:
        """
        Broadcasts a message to the iRacing simulator.
        """
        return ctypes.windll.user32.SendNotifyMessageW(0xFFFF, self._broadcast_msg_id,
                                                     broadcast_type | var1 << 16, var2 | var3 << 16)

    def _pad_car_num(self, num: str) -> int:
        """
        Pads a car number to be used in a broadcast message.
        """
        num_len = len(num)
        zero = num_len - len(num.lstrip("0"))
        if zero > 0 and num_len == zero:
            zero -= 1
        num_int = int(num)
        if zero:
            num_place = 3 if num_int > 99 else 2 if num_int > 9 else 1
            return num_int + 1000 * (num_place + zero)
        return num_int