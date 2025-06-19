from typing import List

VERSION: str = '1.0.0'

SIM_STATUS_URL: str = 'http://127.0.0.1:32034/get_sim_status?object=simStatus'

DATA_VALID_EVENT_NAME: str = 'Local\\IRSDKDataValidEvent'
MEM_MAP_FILE: str = 'Local\\IRSDKMemMapFileName'
MEM_MAP_FILE_SIZE: int = 1164 * 1024
BROADCAST_MSG_NAME: str = 'IRSDK_BROADCASTMSG'

VAR_TYPE_MAP: List[str] = ['c', '?', 'i', 'I', 'f', 'd']

YAML_TRANSLATER: dict[int, int] = bytes.maketrans(b'\x81\x8D\x8F\x90\x9D', b'     ')
YAML_CODE_PAGE: str = 'cp122'