# rebocapentrack
一个将rebocap用于opentrack的头部追踪方案。

## 实现方式

通过 rebocap 的 websocket 将追踪数据转换并通过 udp 转发到 opentrack。

## 配置文件说明

- `rebocap_port` Rebocap 配套软件中的 Websocket 端口。

- `opentrack_port` Opentrack 的 UDP 输入端口。

- `height` 身高，通过 `身高 / 7 * 3` 计算腰部到头顶的距离。

- `tracking_mode` 追踪模式，0 为仅头部角度，1 为除头部角度外，根据头和腰的距离和腰的角度计算位置。

> :warning: 注意
由于 rebocap 本身是[方向传感器](https://doc.rebocap.com/zh_cn/tutorial/instroction_for_straps.html#%E8%B7%9F%E8%B8%AA%E5%99%A8%E5%AE%9A%E4%BD%8D%E5%8E%9F%E7%90%86%E4%BB%8B%E7%BB%8D)，所以不能直接得到位置信息，用于 opentrack 的位置信息需要通过腰到头部的角度和距离进行推算。

## 使用说明

### 1. Rebocap 相关操作

- **确定 websocket 端口**

    启动 Rebocap 的配套软件，点击下方的 `配置`，在右侧的系统设置中找到 `websocket` 广播，确保其处于开启状态，并且端口与配置文件 `config.json` 中的 `rebocap_port` 一致。

- **穿戴追踪器并校准**

    由于 Rebocap 需要在已校准的情况下才对数据进行广播，我们需要先进行一次校准。
    而又由于 Rebocap 的校准要求[十分严格](https://doc.rebocap.com/zh_cn/tutorial/instroction_for_straps.html#pc-%E6%94%AF%E6%8C%81%E6%A8%A1%E5%BC%8F)，我们需要至少佩戴 4 枚 Rebocap 追踪器并进行校准：

    - 头部
    - 左上臂
    - 右上臂
    - 胸部
    - 腰部（如果不需要位置信息可以不穿戴）

    但是我们可以在校准完毕后关机，并重新开启需要的追踪器（头部和腰部），减少多余追踪器的使用。

### 2. Opentrack 相关操作

- **确定 UDP 端口**

    启动 Opentrack，在输入中选择 `UDP over network`，点击其右侧的:hammer:按钮，检查其中的 `Port` 是否与配置文件 `config.json` 中的 `opentrack_port` 一致。

- **开始追踪**

    点击 Opentrack 窗口右下角的 `开始` 按钮。

### 3. rebocapentrack 相关操作

- **检查配置文件**

    查看配置文件中各个选项是否正确。

- **启动软件**

    双击 `rebocapentrack.exe` 启动软件，如果显示 `开始转发数据` 则代表连接 rebocap 成功，并正在将 rebocap 的数据转换并转发至 opentrack 的 udp 端口。
