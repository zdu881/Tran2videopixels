import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import time
from tqdm import tqdm
import subprocess
import tempfile

def get_args():
    parser = argparse.ArgumentParser(description='将视频转换为字符画')
    parser.add_argument('--input', type=str, required=True, help='输入视频文件路径')
    parser.add_argument('--output', type=str, default='./output_ascii.mp4', help='输出视频文件路径')
    parser.add_argument('--width', type=int, default=120, help='字符画宽度（字符数）')
    parser.add_argument('--fps', type=int, default=0, help='输出视频帧率，0表示与原视频相同')
    parser.add_argument('--font-size', type=int, default=12, help='字体大小')
    parser.add_argument('--brightness', type=float, default=1.0, help='亮度调整倍数')
    parser.add_argument('--contrast', type=float, default=1.5, help='对比度调整倍数')
    parser.add_argument('--color', action='store_true', help='使用彩色模式')
    parser.add_argument('--font', type=str, default='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 
                       help='字体路径，Ubuntu默认提供DejaVu等等字体')
    parser.add_argument('--keep-audio', action='store_true', help='保留原视频音频')
    return parser.parse_args()

# 密度字符集 - 按亮度从高到低排序
DENSITY_CHARS = ["@", "#", "8", "&", "o", ":", "*", ".", " "]
def check_ffmpeg():
    """检查ffmpeg是否可用"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            print("警告：ffmpeg命令返回非零状态码，可能无法正常工作")
            print(f"错误信息: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        return True
    except FileNotFoundError:
        print("错误：找不到ffmpeg。请确保已安装ffmpeg并添加到系统路径中。")
        return False
    except Exception as e:
        print(f"检查ffmpeg时出错: {str(e)}")
        return False
        
def brightness_to_char(brightness):
    """将亮度值映射到字符"""
    index = int(brightness / 256 * len(DENSITY_CHARS))
    index = max(0, min(index, len(DENSITY_CHARS) - 1))
    return DENSITY_CHARS[index]

def create_ascii_frame(frame, width, brightness_factor, contrast_factor, font_size, use_color, font_path):
    """将单个视频帧转换为字符画"""
    # 获取原始图像尺寸
    height, orig_width = frame.shape[:2]
    
    # 按指定宽度调整大小，保持宽高比
    char_ratio = 0.5  # 字符的高宽比
    height_in_chars = int(width * height / orig_width * char_ratio)
    
    # 重调尺寸
    small = cv2.resize(frame, (width, height_in_chars))
    
    # 调整亮度和对比度
    adjusted = cv2.convertScaleAbs(small, alpha=contrast_factor, beta=(brightness_factor-1.0)*128)
    
    # 创建ASCII图像
    try:
        # 尝试加载指定字体
        font = ImageFont.truetype(font_path, font_size)
    except (OSError, IOError):
        # 如果失败，尝试加载Ubuntu上常见的等宽字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
        except (OSError, IOError):
            # 如果都失败了，使用默认字体
            print("警告：无法加载指定字体，使用默认字体")
            font = ImageFont.load_default()
    
    char_width = font_size * 0.6
    char_height = font_size
    
    img_width = int(width * char_width)
    img_height = int(height_in_chars * char_height)
    
    # 创建空白图像
    ascii_img = Image.new('RGB', (img_width, img_height), color=(0, 0, 0))
    draw = ImageDraw.Draw(ascii_img)
    
    # 为每个像素生成字符
    for y in range(height_in_chars):
        for x in range(width):
            if use_color:
                # 彩色模式
                b, g, r = adjusted[y, x] if len(adjusted.shape) == 3 else [adjusted[y, x]]*3
                # 计算亮度
                brightness = (r + g + b) / 3
                char = brightness_to_char(brightness)
                # 使用像素颜色
                color = (r, g, b)
            else:
                # 黑白模式
                brightness = adjusted[y, x, 0] if len(adjusted.shape) == 3 else adjusted[y, x]
                char = brightness_to_char(brightness)
                color = (255, 255, 255)  # 白色
            
            # 在图像上绘制字符
            draw.text((x * char_width, y * char_height), char, font=font, fill=color)
    
    # 将PIL图像转换回OpenCV格式
    ascii_frame = np.array(ascii_img)
    ascii_frame = cv2.cvtColor(ascii_frame, cv2.COLOR_RGB2BGR)
    
    return ascii_frame

def add_vignette(frame):
    """添加边缘暗角效果"""
    height, width = frame.shape[:2]
    
    # 创建径向渐变掩码
    mask = np.zeros((height, width), dtype=np.float32)
    center = (width // 2, height // 2)
    max_radius = min(width, height) * 0.6
    
    y, x = np.ogrid[:height, :width]
    distances = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    
    # 创建从内到外逐渐变暗的掩码
    mask = np.clip(1.0 - (distances - max_radius) / (max_radius * 0.5), 0.0, 1.0)
    mask = mask[:, :, np.newaxis] if len(frame.shape) > 2 else mask
    
    # 应用掩码
    vignette_frame = (frame * mask).astype(np.uint8)
    
    return vignette_frame

def process_video(args):
    """处理整个视频并输出新视频"""
    # 打开输入视频
    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"无法打开视频: {args.input}")
        return
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 如果指定了fps，使用指定的fps
    if args.fps > 0:
        fps = args.fps
    
    print(f"视频信息: {width}x{height}, {fps}fps, 总帧数: {frame_count}")
    
    # 创建临时输出文件
    temp_dir = tempfile.gettempdir()
    temp_output = os.path.join(temp_dir, f"temp_ascii_{int(time.time())}.mp4")
    
    # 尝试加载指定字体
    font_path = args.font if args.font != 'monospace' else None
    if font_path and not os.path.exists(font_path):
        print(f"警告：找不到指定字体 {font_path}，尝试使用系统默认字体")
        # Ubuntu常见等宽字体
        for system_font in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf"
        ]:
            if os.path.exists(system_font):
                font_path = system_font
                print(f"使用系统字体: {font_path}")
                break
    
    # 计算输出视频的尺寸（基于第一帧）
    _, first_frame = cap.read()
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到第一帧
    
    sample_ascii = create_ascii_frame(
        first_frame, args.width, args.brightness, args.contrast, 
        args.font_size, args.color, font_path
    )
    out_height, out_width = sample_ascii.shape[:2]
    
    # 设置视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用mp4v编码器
    out = cv2.VideoWriter(temp_output, fourcc, fps, (out_width, out_height))
    
    # 处理每一帧
    print("开始处理视频帧...")
    pbar = tqdm(total=frame_count)
    frame_number = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 创建ASCII字符画
        ascii_frame = create_ascii_frame(
            frame, args.width, args.brightness, args.contrast, 
            args.font_size, args.color, font_path
        )
        
        # 添加暗角效果（可选）
        # ascii_frame = add_vignette(ascii_frame)
        
        # 写入输出视频
        out.write(ascii_frame)
        
        # 更新进度条
        frame_number += 1
        pbar.update(1)
    
    # 关闭资源
    cap.release()
    out.release()
    pbar.close()
    
    # 使用FFmpeg重新编码以提高兼容性
    print("正在进行最终编码...")
    try:
        temp_audio = None
        
        # 如果需要保留音频
        if args.keep_audio:
            # 提取原视频音频到临时文件
            temp_audio = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.aac")
            extract_cmd = [
                'ffmpeg', '-i', args.input, 
                '-vn', '-acodec', 'copy',
                '-y', temp_audio
            ]
            print("提取原始视频音频...")
            subprocess.run(extract_cmd, check=True, stderr=subprocess.PIPE)
            
            # 将字符画视频与原音频合并
            cmd = [
                'ffmpeg', '-i', temp_output, 
                '-i', temp_audio,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0',
                '-y', args.output
            ]
        else:
            # 不保留音频，只处理视频
            cmd = [
                'ffmpeg', '-i', temp_output, 
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-y', args.output
            ]
            
        print("合成最终视频...")
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        print(f"视频已保存为: {args.output}")
        
        # 清理临时文件
        os.remove(temp_output)
        if temp_audio and os.path.exists(temp_audio):
            os.remove(temp_audio)
            
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg处理失败: {e}")
        print(f"FFmpeg错误输出: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else '无详细错误'}")
        print(f"临时文件已保存为: {temp_output}")
    except Exception as e:
        print(f"处理失败: {str(e)}")
        print(f"临时文件已保存为: {temp_output}")
        
if __name__ == "__main__":
    args = get_args()
    process_video(args)