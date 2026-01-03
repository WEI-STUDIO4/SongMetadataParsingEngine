<div align="center">
<h1>🎵 SMPE - Song Metadata Parsing Engine</h1>
  
![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Mutagen](https://img.shields.io/badge/powered%20by-mutagen-orange.svg)

**专业的音乐文件元数据解析工具，特别强化MP3歌词提取能力**

</div>


## ✨ 功能特性

### 📁 多格式支持
- **MP3**: 完整的ID3v2标签解析，专业处理USLT/SYLT歌词帧
- **FLAC**: Vorbis注释解析，支持内嵌封面提取
- **M4A/MP4**: iTunes风格标签解析
- **OGG/Opus**: Vorbis注释支持
- **其他格式**: 通用解析器支持常见音频格式

### 🎵 元数据提取
- **基础信息**: 标题、作者、专辑、音轨号、碟号
- **高级数据**: 歌词（强化MP3解析）、专辑封面、时长
- **格式识别**: 智能文件扩展名识别，专用解析器处理

### 💾 导出功能
- **一键保存**: `DL`命令保存所有元数据
- **歌词导出**: 自动保存为LRC格式文件
- **封面提取**: 保存为PNG格式图片
- **文本报告**: 生成格式化的元数据报告

### 🖥️ 交互体验
- **伪3D标题**: 专业美观的ASCII艺术界面
- **智能交互**: 拖拽文件支持，路径自动处理
- **调试工具**: MP3标签详细分析功能
- **友好提示**: 清晰的状态反馈和错误处理

## 🚀 快速开始

### 安装依赖

```bash
# 只需一个依赖库
pip install mutagen
```

### 运行程序

```bash
# 克隆或下载项目后
python music_metadata_mp3_fixed.py
```

### 基本使用

```bash
# 1. 启动程序后，输入文件路径
🎯 请输入文件路径或命令: "C:\Music\song.mp3"

# 2. 查看解析结果
✨================================================✨
                 元数据解析结果
✨================================================✨
📁 文件: song.mp3
🎵 格式: MP3
⏱️  时长: 3分45秒
--------------------------------------------------
🎵  标题: 平凡之路
👤  作者: 朴树
💿  专辑: 猎户星座
#️⃣  音轨号: 1
💿  碟号: 1
--------------------------------------------------
📝 歌词: ✅ 已提取
🖼️  封面: ✅ 已提取

# 3. 保存元数据
🎯 请输入文件路径或命令: DL
✅ 保存完成!
  📄 文本: song_metadata.txt
  🎵 歌词: song_lyrics.lrc
  🖼️  封面: song_cover.png
```

## 📖 详细使用指南

### 交互命令说明

| 命令 | 功能描述 | 示例 |
|------|---------|------|
| **文件路径** | 直接输入路径解析文件 | `C:\Music\song.mp3` |
| **DL** | 保存所有元数据（歌词+LRC，封面+PNG，文本+TXT） | 解析后输入 `DL` |
| **L** | 仅保存歌词文件 | 解析后输入 `L` |
| **C** | 仅保存封面图片 | 解析后输入 `C` |
| **DEBUG** | 查看MP3文件的详细标签结构（仅MP3） | 解析MP3后输入 `DEBUG` |
| **exit/quit** | 退出程序 | `exit` 或 `quit` |

### 支持的文件格式

| 格式 | 扩展名 | 歌词支持 | 封面支持 |
|------|--------|---------|---------|
| MP3 | `.mp3` | ✅ USLT/SYLT帧 | ✅ APIC帧 |
| FLAC | `.flac` | ✅ lyrics字段 | ✅ 内嵌图片 |
| M4A/MP4 | `.m4a`, `.mp4` | ✅ ©lyr字段 | ✅ covr字段 |
| OGG Vorbis | `.ogg` | ✅ lyrics字段 | ⚠️ 有限支持 |
| Opus | `.opus` | ✅ lyrics字段 | ⚠️ 有限支持 |

### MP3歌词解析技术

本工具针对MP3文件实现了四级歌词查找策略：

```python
# 1. 直接获取所有USLT帧（无时间戳歌词）
uslt_frames = id3_tags.getall('USLT')

# 2. 获取所有SYLT帧（同步歌词，转换为LRC格式）
sylt_frames = id3_tags.getall('SYLT')

# 3. 遍历所有标签查找歌词帧
for frame_id, frame in id3_tags.items():
    if isinstance(frame, USLT) or isinstance(frame, SYLT):
        # 处理歌词...

# 4. 查找TXXX自定义歌词帧
if 'TXXX:LYRICS' in id3_tags:
    # 处理自定义歌词...
```

## 🛠️ 项目结构

```
SMPE/
├── music_metadata_mp3_fixed.py  # 主程序文件
├── README.md                    # 项目说明文档
└── requirements.txt             # 依赖说明

# 运行时生成的文件（示例）
├── song_metadata.txt           # 文本元数据报告
├── song_lyrics.lrc             # LRC格式歌词文件
└── song_cover.png              # 专辑封面图片
```

### 核心类说明

- **`MusicMetadataExtractor`**: 主解析器类，根据文件格式分发处理
- **`MetadataSaver`**: 元数据保存器，处理文件导出
- **专用解析器**: 每个音频格式都有对应的解析方法（`_parse_mp3`、`_parse_flac`等）

## 🔧 高级功能

### 调试MP3标签

```bash
# 解析MP3文件后，使用DEBUG命令
🎯 请输入文件路径或命令: DEBUG

🔍 MP3标签调试信息: song.mp3
============================================================
找到 15 个标签帧:

🎵 歌词相关帧 (1 个):
  • USLT::eng (USLT)
    内容预览: [00:00.00]作曲 : 朴树...

🖼️  封面帧 (1 个):
  • APIC: (封面)
    类型: image/jpeg
    大小: 153428 字节

📝 重要文本帧:
  • TIT2: 平凡之路
  • TPE1: 朴树
  • TALB: 猎户星座
  • TRCK: 1
  • TPOS: 1
```

### 编码问题处理

工具内置多编码支持，自动尝试以下编码解码歌词：
- UTF-8, GBK, GB2312, Big5
- Latin-1, UTF-16, UTF-16LE
- 自动回退到忽略错误模式

## ❓ 常见问题

### Q1: MP3文件解析不出歌词？
**A**: 可能是以下原因：
1. 文件确实没有内嵌歌词
2. 歌词存储在外部LRC文件
3. 使用了非标准歌词帧

**解决方案**：
1. 使用`DEBUG`命令查看标签结构
2. 检查是否有`USLT`或`SYLT`帧
3. 尝试其他来源的MP3文件

### Q2: 封面保存失败？
**A**: 确保：
1. 文件确实包含封面数据
2. 有写入当前目录的权限
3. 封面数据格式受支持（JPEG/PNG）

### Q3: 如何批量处理文件？
**A**: 目前为交互式单文件处理，但可以：
```python
# 简单批量处理示例
import os
from your_module import MusicMetadataExtractor

for file in os.listdir('music_folder'):
    if file.endswith('.mp3'):
        extractor = MusicMetadataExtractor(os.path.join('music_folder', file))
        metadata = extractor.extract()
        # 处理metadata...
```

## 📝 开发与贡献

### 扩展新格式支持

要添加新格式支持，请：

1. 在`MusicMetadataExtractor`类中添加新的解析方法
2. 更新`extract()`方法中的格式分发逻辑
3. 添加对应的文件扩展名识别

```python
def _parse_new_format(self):
    """新的音频格式解析器"""
    try:
        # 使用对应的mutagen解析器
        audio = NewFormatParser(self.file_path)
        # 提取元数据...
        return self.metadata
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None
```

### 代码规范

- 使用有意义的变量名和函数名
- 添加适当的错误处理
- 保持与现有代码风格一致
- 为新增功能添加文档说明

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢 [mutagen](https://github.com/quodlibet/mutagen) 项目提供的强大音频元数据解析库
- 感谢所有测试用户的问题反馈和改进建议

---

<div align="center">

**如果这个工具对你有帮助，请给个⭐星标支持！**

*让音乐数据触手可及* 🎶

</div>
