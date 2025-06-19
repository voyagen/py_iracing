from enum import IntEnum, IntFlag

class StatusField(IntEnum):
    status_connected = 1

class EngineWarnings(IntFlag):
    water_temp_warning    = 0x01
    fuel_pressure_warning = 0x02
    oil_pressure_warning  = 0x04
    engine_stalled        = 0x08
    pit_speed_limiter     = 0x10
    rev_limiter_active    = 0x20
    oil_temp_warning      = 0x40

class Flags(IntFlag):
    # global flags
    checkered        = 0x0001
    white            = 0x0002
    green            = 0x0004
    yellow           = 0x0008
    red              = 0x0010
    blue             = 0x0020
    debris           = 0x0040
    crossed          = 0x0080
    yellow_waving    = 0x0100
    one_lap_to_green = 0x0200
    green_held       = 0x0400
    ten_to_go        = 0x0800
    five_to_go       = 0x1000
    random_waving    = 0x2000
    caution          = 0x4000
    caution_waving   = 0x8000

    # drivers black flags
    black      = 0x010000
    disqualify = 0x020000
    servicible = 0x040000 # car is allowed service (not a flag)
    furled     = 0x080000
    repair     = 0x100000

    # start lights
    start_hidden = 0x10000000
    start_ready  = 0x20000000
    start_set    = 0x40000000
    start_go     = 0x80000000

class TrackLocation(IntEnum):
    not_in_world    = -1
    off_track       = 0
    in_pit_stall    = 1
    aproaching_pits = 2
    on_track        = 3

class TrackSurface(IntEnum):
    not_in_world  = -1
    undefined     =  0
    asphalt_1     =  1
    asphalt_2     =  2
    asphalt_3     =  3
    asphalt_4     =  4
    concrete_1    =  5
    concrete_2    =  6
    racing_dirt_1 =  7
    racing_dirt_2 =  8
    paint_1       =  9
    paint_2       = 10
    rumble_1      = 11
    rumble_2      = 12
    rumble_3      = 13
    rumble_4      = 14
    grass_1       = 15
    grass_2       = 16
    grass_3       = 17
    grass_4       = 18
    dirt_1        = 19
    dirt_2        = 20
    dirt_3        = 21
    dirt_4        = 22
    sand          = 23
    gravel_1      = 24
    gravel_2      = 25
    grasscrete    = 26
    astroturf     = 27

class SessionState(IntEnum):
    invalid     = 0
    get_in_car  = 1
    warmup      = 2
    parade_laps = 3
    racing      = 4
    checkered   = 5
    cool_down   = 6

class CameraState(IntFlag):
    is_session_screen       = 0x0001
    is_scenic_active        = 0x0002
    cam_tool_active         = 0x0004
    ui_hidden               = 0x0008
    use_auto_shot_selection = 0x0010
    use_temporary_edits     = 0x0020
    use_key_acceleration    = 0x0040
    use_key10x_acceleration = 0x0080
    use_mouse_aim_mode      = 0x0100

class BroadcastMsg(IntEnum):
    cam_switch_pos             =  0
    cam_switch_num             =  1
    cam_set_state              =  2
    replay_set_play_speed      =  3
    replay_set_play_position   =  4
    replay_search              =  5
    replay_set_state           =  6
    reload_textures            =  7
    chat_command               =  8
    pit_command                =  9
    telem_command              = 10
    ffb_command                = 11
    replay_search_session_time = 12
    video_capture              = 13

class ChatCommandMode(IntEnum):
    macro      = 0
    begin_chat = 1
    reply      = 2
    cancel     = 3

class PitCommandMode(IntEnum):
    clear       =  0
    ws          =  1
    fuel        =  2
    lf          =  3
    rf          =  4
    lr          =  5
    rr          =  6
    clear_tires =  7
    fr          =  8
    clear_ws    =  9
    clear_fr    = 10
    clear_fuel  = 11

class TelemCommandMode(IntEnum):
    stop    = 0
    start   = 1
    restart = 2

class ReplayStateMode(IntEnum):
    erase_tape = 0

class ReloadTexturesMode(IntEnum):
    all     = 0
    car_idx = 1

class ReplaySearchMode(IntEnum):
    to_start      = 0
    to_end        = 1
    prev_session  = 2
    next_session  = 3
    prev_lap      = 4
    next_lap      = 5
    prev_frame    = 6
    next_frame    = 7
    prev_incident = 8
    next_incident = 9

class ReplayPositionMode(IntEnum):
    begin   = 0
    current = 1
    end     = 2

class CameraSwitchMode(IntEnum):
    at_incident = -3
    at_leader   = -2
    at_exciting = -1

class PitSvFlags(IntFlag):
    lf_tire_change     = 0x01
    rf_tire_change     = 0x02
    lr_tire_change     = 0x04
    rr_tire_change     = 0x08
    fuel_fill          = 0x10
    windshield_tearoff = 0x20
    fast_repair        = 0x40

class PitSvStatus(IntEnum):
    none            = 0
    in_progress     = 1
    complete        = 2
    too_far_left    = 100
    too_far_right   = 101
    too_far_forward = 102
    too_far_back    = 103
    bad_angle       = 104
    cant_fix_that   = 105

class PaceMode(IntEnum):
    single_file_start   = 0
    double_file_start   = 1
    single_file_restart = 2
    double_file_restart = 3
    not_pacing          = 4

class PaceFlags(IntFlag):
    end_of_line  = 0x0001
    free_pass    = 0x0002
    waved_around = 0x0004

class CarLeftRight(IntEnum):
    off            = 0
    clear          = 1
    car_left       = 2
    car_right      = 3
    car_left_right = 4
    two_cars_left  = 5
    two_cars_right = 6

class FFBCommandMode(IntEnum):
    ffb_command_max_force = 0

class VideoCaptureMode(IntEnum):
    trigger_screen_shot   = 0
    start_video_capture   = 1
    end_video_capture     = 2
    toggle_video_capture  = 3
    show_video_timer      = 4
    hide_video_timer      = 5

class TrackWetness(IntEnum):
    unknown          = 0
    dry              = 1
    mostly_dry       = 2
    very_lightly_wet = 3
    lightly_wet      = 4
    moderately_wet   = 5
    very_wet         = 6
    extremely_wet    = 7