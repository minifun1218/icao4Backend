from mutagen import File
import os

file_path = r'C:\Users\Administrator\Desktop\icao4Backend\upload\audio\6-8_DzqBjGV.mp3'

audio = File(file_path)

if audio is None:
    print("错误：Mutagen 无法识别此文件类型。")
elif audio.info is None:
    print("错误：Mutagen 无法解析音频流信息，文件可能已损坏或格式特殊。")
else:
    print(f"标签数据（可能为空）：{audio}")
    print("--- 音频流信息 ---")
    print(f"时长: {audio.info.length:.2f} 秒")
    print(f"比特率: {audio.info.bitrate / 1000} kbps")
    print(f"采样率: {audio.info.sample_rate} Hz")