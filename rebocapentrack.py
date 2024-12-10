import json
import math
import socket
import time
import struct

from libs.rebocap_python_sdk_v2.rebocap_ws_sdk import rebocap_ws_sdk

CONFIG = json.load(open("config.json"))
VERSION = CONFIG["version"]
REBOCAP_PORT = CONFIG["rebocap_port"]
OPENTRACK_PORT = CONFIG["opentrack_port"]
HEIGHT = CONFIG["height"]
TRACKING_MODE = CONFIG["tracking_mode"]

opentrack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sdk = None
pelvis_to_head_length = HEIGHT / 7 * 3


# 四元数转欧拉角
def quaternion_to_euler(list):
    x = list[0]
    y = list[1]
    z = list[2]
    w = list[3]
    # Yaw (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    yaw = math.asin(sinp) if abs(sinp) <= 1.0 else math.copysign(math.pi / 2, sinp)

    # Pitch (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    pitch = math.atan2(sinr_cosp, cosr_cosp)

    # Roll (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    roll = math.atan2(siny_cosp, cosy_cosp)

    return [math.degrees(yaw), -math.degrees(pitch), math.degrees(roll)]


# 四元数转旋转矩阵
def quaternion_to_rotation_matrix(q):
    w, x, y, z = q

    # Unity 左手坐标系中的旋转矩阵公式
    rotation_matrix = [
        [1 - 2 * (y**2 + z**2), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x**2 + z**2), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x**2 + y**2)],
    ]
    return rotation_matrix


def apply_rotation_matrix(point, matrix):
    x, y, z = point
    rotated_point = [
        matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z,
        -(matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z),
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z,
    ]
    return rotated_point


# 异常断开，这里处理重连或报错
def exception_close_callback(self: rebocap_ws_sdk.RebocapWsSdk):
    print("Rebocap 断开连接，正在尝试重新连接...")
    time.sleep(1)
    connect_rebocap()


# 连接rebocap
def connect_rebocap():
    global sdk

    # 初始化sdk  这里可以选择控件坐标系， 控件坐标系目前已经测试过的有： 1. UE  2. Unity  3. Blender
    # 选择输出角度是否是 global 角度，默认是 local 角度【简单解释，global 角度不受父节点影响 local角度受父节点影响， local角度逐级相乘就是 global 角度
    sdk = rebocap_ws_sdk.RebocapWsSdk(
        coordinate_type=rebocap_ws_sdk.CoordinateType.UnityCoordinate,
        use_global_rotation=True,
    )
    # 设置异常断开回调
    sdk.set_exception_close_callback(exception_close_callback)

    # 开始连接
    open_ret = sdk.open(REBOCAP_PORT)
    # 检查连接状态
    if open_ret == 0:
        print("Rebocap 连接成功")
    else:
        print("Rebocap 连接失败", open_ret)
        if open_ret == 1:
            print("Rebocap 连接状态错误")
        elif open_ret == 2:
            print("Rebocap 连接失败")
        elif open_ret == 3:
            print("Rebocap 认证失败")
        else:
            print("Rebocap 未知错误", open_ret)
        exit(1)


connect_rebocap()

print()
print("当前追踪方式：", end="")
if TRACKING_MODE == 1:
    print("计算头腰距离 + 头角度")
    print(f"身高为：{HEIGHT}，计算头腰距离为：{pelvis_to_head_length}")
else:
    print("仅头部角度")
print()
print(
    f"3 秒后接收 rebocap(端口：{REBOCAP_PORT}) 数据并转发到 opentrack(端口：{OPENTRACK_PORT})"
)
time.sleep(3)
print()
print("开始转发数据")

try:
    while True:
        msg = sdk.get_last_msg()
        head_euler = quaternion_to_euler(msg[1][15])
        data = [0.0, 0.0, 0.0]
        if TRACKING_MODE == 1:
            pelvis_matrix = quaternion_to_rotation_matrix(msg[1][0])
            data = apply_rotation_matrix([0, pelvis_to_head_length, 0], pelvis_matrix)
            data[1] -= pelvis_to_head_length
        data.extend(head_euler)
        data_bytes = struct.pack("6d", *data)
        opentrack_socket.sendto(data_bytes, ("127.0.0.1", OPENTRACK_PORT))
        time.sleep(1.0 / 60)
except KeyboardInterrupt:
    sdk.close()
