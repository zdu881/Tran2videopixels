# 视频字符画转换器

一个将普通视频转换成字符画风格的工具，支持彩色和黑白两种模式。

## 功能特点

- 将视频转换为 ASCII 字符画风格
- 支持彩色和黑白两种渲染模式
- 可调整输出分辨率、帧率、亮度和对比度
- 可选择自定义字体
- 支持保留原视频的音频轨道

## 安装

### 依赖项

- Python 3.6+
- OpenCV (cv2)
- NumPy
- Pillow (PIL)
- tqdm
- ffmpeg (系统级依赖)

### 安装步骤

1. 确保系统已安装 Python 3.6 或更高版本
2. 安装 ffmpeg：
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
3. 安装 Python 依赖：
   ```bash
   pip install opencv-python numpy pillow tqdm
   ```

## 使用方法

基本用法：

```bash
python ex.py --input 输入视频.mp4 --output 输出视频.mp4
```

### 参数说明

| 参数           | 描述                                                                  |
| -------------- | --------------------------------------------------------------------- |
| `--input`      | 输入视频文件路径（必需）                                              |
| `--output`     | 输出视频文件路径（默认：./output_ascii.mp4）                          |
| `--width`      | 字符画宽度，即每行字符数（默认：120）                                 |
| `--fps`        | 输出视频帧率，0 表示与原视频相同（默认：0）                           |
| `--font-size`  | 字体大小（默认：12）                                                  |
| `--brightness` | 亮度调整倍数（默认：1.0）                                             |
| `--contrast`   | 对比度调整倍数（默认：1.5）                                           |
| `--color`      | 使用彩色模式（默认为黑白模式）                                        |
| `--font`       | 字体路径（默认：/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf） |
| `--keep-audio` | 保留原视频音频                                                        |

## 使用示例

### 基本转换（黑白模式）

```bash
python ex.py --input input.mp4 --output output.mp4
```

### 彩色字符画

```bash
python ex.py --input input.mp4 --output color_ascii.mp4 --color
```

### 调整分辨率和对比度

```bash
python ex.py --input input.mp4 --width 160 --contrast 2.0 --output hd_ascii.mp4
```

### 保留原视频音频

```bash
python ex.py --input input.mp4 --output ascii_with_audio.mp4 --keep-audio
```

### 使用自定义字体

```bash
python ex.py --input input.mp4 --font /path/to/custom/font.ttf --output custom_font.mp4
```

## 常见问题

1. **找不到 ffmpeg**：确保已安装 ffmpeg 并添加到系统路径
2. **找不到指定字体**：程序会尝试使用系统默认字体，或者您可以指定一个存在的字体文件路径
3. **处理速度慢**：减小 `--width` 参数值可以加快处理速度
4. **内存不足**：处理高分辨率视频时可能需要较大内存，可以降低输出分辨率

## 许可证

MIT
