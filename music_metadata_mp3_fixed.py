#!/usr/bin/env python3
"""
音乐文件元数据解析工具 - MP3歌词强化版
专门针对MP3文件的USLT/SYLT歌词帧进行解析
"""

import os
import sys
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3, USLT, SYLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

class MusicMetadataExtractor:
    """音乐元数据提取器 - 强化MP3歌词解析"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.extension = self.file_path.suffix.lower()
        self.metadata = {
            'title': None, 'artist': None, 'album': None,
            'track': None, 'disc': None, 'lyrics': None,
            'cover': None, 'duration': None, 'format': None,
            'file_name': self.file_path.name
        }
    
    def extract(self):
        """主提取方法"""
        if not self.file_path.exists():
            print(f"❌ 文件不存在: {self.file_path}")
            return None
        
        print(f"\n🔍 解析文件: {self.file_path.name}")
        print(f"📁 格式: {self.extension[1:].upper()}")
        
        try:
            # 根据格式调用相应的解析器
            if self.extension == '.mp3':
                return self._parse_mp3()
            elif self.extension in ['.flac']:
                return self._parse_flac()
            elif self.extension in ['.m4a', '.mp4']:
                return self._parse_m4a()
            elif self.extension in ['.ogg']:
                return self._parse_ogg()
            elif self.extension in ['.opus']:
                return self._parse_opus()
            else:
                # 通用解析器（用于其他格式）
                return self._parse_generic()
                
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return None
    
    def _parse_mp3(self):
        """专用MP3解析器 - 重点强化歌词提取"""
        try:
            # 方法1：使用ID3专门加载MP3标签
            try:
                id3 = ID3(self.file_path)
            except ID3NoHeaderError:
                print("⚠️  MP3文件没有ID3标签头，尝试通用解析")
                return self._parse_generic()
            
            # 提取基本元数据
            self.metadata.update({
                'title': self._get_id3_text(id3, 'TIT2'),
                'artist': self._get_id3_text(id3, 'TPE1'),
                'album': self._get_id3_text(id3, 'TALB'),
                'track': self._get_id3_track(id3, 'TRCK'),
                'disc': self._get_id3_text(id3, 'TPOS'),
                'format': 'MP3'
            })
            
            # 提取封面
            self._extract_mp3_cover(id3)
            
            # ★ 核心改进：使用专用函数提取MP3歌词
            self.metadata['lyrics'] = self._extract_mp3_lyrics_dedicated(id3)
            
            # 获取时长
            try:
                audio = File(self.file_path)
                if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                    self.metadata['duration'] = audio.info.length
            except:
                pass
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ MP3解析失败: {e}")
            return None
    
    def _extract_mp3_lyrics_dedicated(self, id3_tags):
        """
        专用的MP3歌词提取函数
        重点处理USLT和SYLT帧
        """
        if not id3_tags:
            return None
        
        lyrics = None
        
        print("🎵 正在搜索MP3歌词帧...")
        
        # 方法1：优先查找USLT（无时间戳歌词）
        try:
            # getall('USLT') 返回所有USLT帧的列表
            uslt_frames = id3_tags.getall('USLT')
            if uslt_frames:
                # 通常取第一个USLT帧
                uslt = uslt_frames[0]
                lyrics = uslt.text
                
                # 尝试不同编码解码
                if isinstance(lyrics, bytes):
                    lyrics = self._decode_lyrics_bytes(lyrics)
                
                print(f"   ✅ 从 [USLT] 帧找到歌词 ({len(lyrics)} 字符)")
                return lyrics
        except Exception as e:
            print(f"   ⚠️  解析USLT帧失败: {e}")
        
        # 方法2：查找SYLT（同步歌词）
        try:
            sylt_frames = id3_tags.getall('SYLT')
            if sylt_frames:
                sylt = sylt_frames[0]
                lyric_lines = []
                
                # SYLT歌词带时间戳，格式化为LRC格式
                if hasattr(sylt, 'lyrics') and sylt.lyrics:
                    for time_ms, text in sylt.lyrics:
                        # 毫秒转换为 [mm:ss.xx] 格式
                        minutes = time_ms // 60000
                        seconds = (time_ms % 60000) // 1000
                        hundredths = (time_ms % 1000) // 10
                        time_tag = f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]"
                        lyric_lines.append(f"{time_tag}{text}")
                    
                    lyrics = '\n'.join(lyric_lines)
                    print(f"   ✅ 从 [SYLT] 帧找到同步歌词 ({len(sylt.lyrics)} 行)")
                    return lyrics
        except Exception as e:
            print(f"   ⚠️  解析SYLT帧失败: {e}")
        
        # 方法3：遍历所有标签查找歌词相关帧
        try:
            for frame_id, frame in id3_tags.items():
                # 检查是否为歌词帧
                if isinstance(frame, USLT):
                    lyrics = frame.text
                    if isinstance(lyrics, bytes):
                        lyrics = self._decode_lyrics_bytes(lyrics)
                    print(f"   ✅ 通过遍历找到 [USLT: {frame_id}] 歌词")
                    return lyrics
                elif isinstance(frame, SYLT):
                    if hasattr(frame, 'lyrics') and frame.lyrics:
                        lyric_lines = []
                        for time_ms, text in frame.lyrics:
                            minutes = time_ms // 60000
                            seconds = (time_ms % 60000) // 1000
                            hundredths = (time_ms % 1000) // 10
                            time_tag = f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]"
                            lyric_lines.append(f"{time_tag}{text}")
                        lyrics = '\n'.join(lyric_lines)
                        print(f"   ✅ 通过遍历找到 [SYLT: {frame_id}] 同步歌词")
                        return lyrics
        except Exception as e:
            print(f"   ⚠️  遍历标签失败: {e}")
        
        # 方法4：查找包含"LYRICS"的自定义文本帧（TXXX）
        try:
            for frame_id, frame in id3_tags.items():
                if 'TXXX:' in frame_id and 'LYRICS' in frame_id.upper():
                    if hasattr(frame, 'text'):
                        lyrics = frame.text[0] if isinstance(frame.text, list) else frame.text
                    else:
                        lyrics = str(frame)
                    
                    if isinstance(lyrics, bytes):
                        lyrics = self._decode_lyrics_bytes(lyrics)
                    
                    print(f"   ✅ 找到自定义歌词帧 [{frame_id}]")
                    return lyrics
        except Exception as e:
            print(f"   ⚠️  查找自定义歌词帧失败: {e}")
        
        print("   ❌ 未找到MP3内嵌歌词")
        return None
    
    def _decode_lyrics_bytes(self, lyric_bytes):
        """尝试多种编码解码歌词字节"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1', 'utf-16', 'utf-16le']
        
        for encoding in encodings:
            try:
                return lyric_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 所有编码都失败，使用忽略错误的方式解码
        try:
            return lyric_bytes.decode('utf-8', errors='ignore')
        except:
            return str(lyric_bytes)
    
    def _extract_mp3_cover(self, id3_tags):
        """提取MP3封面"""
        if not id3_tags:
            return
        
        # 查找APIC帧（专辑图片）
        for frame_id, frame in id3_tags.items():
            if frame_id.startswith('APIC:'):
                if hasattr(frame, 'data'):
                    self.metadata['cover'] = frame.data
                    print("   🖼️  找到封面图片")
                    break
    
    def _parse_flac(self):
        """FLAC解析器"""
        try:
            audio = FLAC(self.file_path)
            
            self.metadata.update({
                'title': self._get_vorbis_value(audio, 'title'),
                'artist': self._get_vorbis_value(audio, 'artist'),
                'album': self._get_vorbis_value(audio, 'album'),
                'track': self._get_vorbis_value(audio, 'tracknumber'),
                'disc': self._get_vorbis_value(audio, 'discnumber'),
                'format': 'FLAC'
            })
            
            # 提取FLAC封面
            if audio.pictures:
                self.metadata['cover'] = audio.pictures[0].data
                print("   🖼️  找到封面图片")
            
            # 提取歌词
            self.metadata['lyrics'] = self._extract_generic_lyrics(audio)
            
            # 获取时长
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.metadata['duration'] = audio.info.length
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ FLAC解析失败: {e}")
            return None
    
    def _parse_m4a(self):
        """M4A/MP4解析器"""
        try:
            audio = MP4(self.file_path)
            
            self.metadata.update({
                'title': audio.get('©nam', [None])[0],
                'artist': audio.get('©ART', [None])[0],
                'album': audio.get('©alb', [None])[0],
                'format': 'M4A/MP4'
            })
            
            # 音轨号
            track_data = audio.get('trkn', [(None, None)])[0]
            if track_data and track_data[0]:
                self.metadata['track'] = str(track_data[0])
            
            # 碟号
            disc_data = audio.get('disk', [(None, None)])[0]
            if disc_data and disc_data[0]:
                self.metadata['disc'] = str(disc_data[0])
            
            # 封面
            if 'covr' in audio:
                self.metadata['cover'] = audio['covr'][0]
                print("   🖼️  找到封面图片")
            
            # 歌词
            self.metadata['lyrics'] = self._extract_generic_lyrics(audio)
            
            # 时长
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.metadata['duration'] = audio.info.length
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ M4A/MP4解析失败: {e}")
            return None
    
    def _parse_ogg(self):
        """OGG解析器"""
        try:
            audio = OggVorbis(self.file_path)
            
            self.metadata.update({
                'title': self._get_vorbis_value(audio, 'title'),
                'artist': self._get_vorbis_value(audio, 'artist'),
                'album': self._get_vorbis_value(audio, 'album'),
                'track': self._get_vorbis_value(audio, 'tracknumber'),
                'disc': self._get_vorbis_value(audio, 'discnumber'),
                'format': 'OGG'
            })
            
            self.metadata['lyrics'] = self._extract_generic_lyrics(audio)
            
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.metadata['duration'] = audio.info.length
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ OGG解析失败: {e}")
            return None
    
    def _parse_opus(self):
        """Opus解析器"""
        try:
            audio = OggOpus(self.file_path)
            
            self.metadata.update({
                'title': self._get_vorbis_value(audio, 'title'),
                'artist': self._get_vorbis_value(audio, 'artist'),
                'album': self._get_vorbis_value(audio, 'album'),
                'track': self._get_vorbis_value(audio, 'tracknumber'),
                'disc': self._get_vorbis_value(audio, 'discnumber'),
                'format': 'OPUS'
            })
            
            self.metadata['lyrics'] = self._extract_generic_lyrics(audio)
            
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.metadata['duration'] = audio.info.length
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ OPUS解析失败: {e}")
            return None
    
    def _parse_generic(self):
        """通用解析器（用于其他格式）"""
        try:
            audio = File(self.file_path, easy=False)
            if audio is None:
                print("❌ 无法识别的音频格式")
                return None
            
            self.metadata['format'] = self.extension[1:].upper()
            
            # 尝试获取常见字段
            common_fields = {
                'title': ['title', 'TIT2', '©nam'],
                'artist': ['artist', 'TPE1', '©ART'],
                'album': ['album', 'TALB', '©alb'],
                'track': ['tracknumber', 'TRCK', 'trkn'],
                'disc': ['discnumber', 'TPOS', 'disk']
            }
            
            for meta_key, field_list in common_fields.items():
                for field in field_list:
                    try:
                        if hasattr(audio, 'tags') and field in audio.tags:
                            value = audio.tags[field]
                            if hasattr(value, 'text'):
                                self.metadata[meta_key] = value.text[0]
                                break
                            elif isinstance(value, list) and value:
                                self.metadata[meta_key] = value[0]
                                break
                        elif field in audio:
                            value = audio[field]
                            if isinstance(value, list) and value:
                                self.metadata[meta_key] = value[0]
                                break
                    except:
                        continue
            
            # 通用歌词提取
            self.metadata['lyrics'] = self._extract_generic_lyrics(audio)
            
            # 通用封面提取
            self.metadata['cover'] = self._extract_generic_cover(audio)
            
            # 时长
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.metadata['duration'] = audio.info.length
            
            return self.metadata
            
        except Exception as e:
            print(f"❌ 通用解析失败: {e}")
            return None
    
    def _extract_generic_lyrics(self, audio):
        """通用歌词提取（用于非MP3格式）"""
        if audio is None:
            return None
        
        lyrics_fields = [
            'lyrics', 'LYRICS', 'Lyrics', '©lyr',
            '----:com.apple.iTunes:LYRICS'
        ]
        
        for field in lyrics_fields:
            try:
                if hasattr(audio, 'tags') and field in audio.tags:
                    value = audio.tags[field]
                    if isinstance(value, list) and value:
                        lyrics = value[0]
                        if isinstance(lyrics, bytes):
                            lyrics = self._decode_lyrics_bytes(lyrics)
                        print(f"   ✅ 找到歌词 [{field}]")
                        return lyrics
                elif field in audio:
                    value = audio[field]
                    if isinstance(value, list) and value:
                        lyrics = value[0]
                        if isinstance(lyrics, bytes):
                            lyrics = self._decode_lyrics_bytes(lyrics)
                        print(f"   ✅ 找到歌词 [{field}]")
                        return lyrics
            except:
                continue
        
        return None
    
    def _extract_generic_cover(self, audio):
        """通用封面提取"""
        if audio is None:
            return None
        
        # MP4/M4A
        if 'covr' in audio:
            return audio['covr'][0]
        
        # FLAC
        if hasattr(audio, 'pictures') and audio.pictures:
            return audio.pictures[0].data
        
        return None
    
    def _get_id3_text(self, tags, tag_name):
        """安全获取ID3文本标签"""
        if tag_name in tags:
            tag = tags[tag_name]
            if hasattr(tag, 'text') and tag.text:
                return tag.text[0]
        return None
    
    def _get_id3_track(self, tags, tag_name):
        """安全获取ID3音轨号（处理x/y格式）"""
        if tag_name in tags:
            tag = tags[tag_name]
            if hasattr(tag, 'text') and tag.text:
                track = tag.text[0]
                if '/' in track:
                    return track.split('/')[0]
                return track
        return None
    
    def _get_vorbis_value(self, audio, key):
        """安全获取Vorbis注释值"""
        if hasattr(audio, 'tags') and key in audio.tags:
            value = audio.tags[key]
            if isinstance(value, list) and value:
                return value[0]
        return None

class MetadataSaver:
    """元数据保存器"""
    
    @staticmethod
    def save_all(metadata, base_dir="."):
        """保存所有元数据"""
        if not metadata:
            print("❌ 没有可保存的元数据")
            return False
        
        base_name = Path(metadata['file_name']).stem
        base_name = base_name.replace(' ', '_').replace('/', '_')
        save_path = Path(base_dir)
        save_path.mkdir(exist_ok=True)
        
        results = []
        
        # 1. 保存文本元数据
        txt_file = save_path / f"{base_name}_metadata.txt"
        MetadataSaver._save_text_metadata(metadata, txt_file)
        results.append(f"📄 文本: {txt_file.name}")
        
        # 2. 保存歌词
        if metadata['lyrics']:
            lrc_file = save_path / f"{base_name}_lyrics.lrc"
            if MetadataSaver._save_lyrics(metadata['lyrics'], lrc_file):
                results.append(f"🎵 歌词: {lrc_file.name}")
        
        # 3. 保存封面
        if metadata['cover']:
            png_file = save_path / f"{base_name}_cover.png"
            if MetadataSaver._save_cover(metadata['cover'], png_file):
                results.append(f"🖼️  封面: {png_file.name}")
        
        # 显示结果
        print("\n" + "="*50)
        print("✅ 保存完成!")
        for result in results:
            print(f"  {result}")
        print("="*50)
        return True
    
    @staticmethod
    def _save_text_metadata(metadata, filepath):
        """保存文本元数据"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*40 + "\n")
                f.write("音乐文件元数据报告\n")
                f.write("="*40 + "\n\n")
                
                f.write(f"📁 文件: {metadata['file_name']}\n")
                f.write(f"🎵 格式: {metadata['format'] or '未知'}\n")
                if metadata['duration']:
                    mins = int(metadata['duration'] // 60)
                    secs = int(metadata['duration'] % 60)
                    f.write(f"⏱️  时长: {mins}:{secs:02d}\n")
                f.write("-"*30 + "\n\n")
                
                fields = [
                    ("🎵 标题", metadata['title']),
                    ("👤 作者", metadata['artist']),
                    ("💿 专辑", metadata['album']),
                    ("#️⃣ 音轨号", metadata['track']),
                    ("💿 碟号", metadata['disc']),
                ]
                
                for label, value in fields:
                    f.write(f"{label}: {value or '未找到'}\n")
                
                f.write("\n" + "-"*30 + "\n")
                f.write(f"📝 歌词: {'✅ 已提取' if metadata['lyrics'] else '❌ 未找到'}\n")
                f.write(f"🖼️  封面: {'✅ 已提取' if metadata['cover'] else '❌ 未找到'}\n")
            
            return True
        except Exception as e:
            print(f"⚠️  保存文本元数据失败: {e}")
            return False
    
    @staticmethod
    def _save_lyrics(lyrics_data, filepath):
        """保存歌词为LRC文件"""
        try:
            # 确保是字符串
            if isinstance(lyrics_data, bytes):
                lyrics_text = lyrics_data.decode('utf-8', errors='ignore')
            else:
                lyrics_text = str(lyrics_data)
            
            # 如果是纯文本，添加基本的LRC标签
            if not lyrics_text.strip().startswith('['):
                lyrics_text = f"[ar:Unknown]\n[ti:Unknown]\n\n{lyrics_text}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(lyrics_text)
            return True
        except Exception as e:
            print(f"⚠️  歌词保存失败: {e}")
            return False
    
    @staticmethod
    def _save_cover(cover_data, filepath):
        """保存封面为PNG文件"""
        try:
            if isinstance(cover_data, bytes):
                with open(filepath, 'wb') as f:
                    f.write(cover_data)
                return True
            elif hasattr(cover_data, 'data'):
                with open(filepath, 'wb') as f:
                    f.write(cover_data.data)
                return True
            else:
                print("⚠️  封面数据格式无法识别")
                return False
        except Exception as e:
            print(f"⚠️  封面保存失败: {e}")
            return False

def display_metadata(metadata):
    """美观地显示元数据"""
    if not metadata:
        return
    
    print("\n" + "✨" + "="*48 + "✨")
    print("                 元数据解析结果")
    print("✨" + "="*48 + "✨")
    
    # 基础信息
    print(f"📁 文件: {metadata['file_name']}")
    print(f"🎵 格式: {metadata['format'] or '未知'}")
    if metadata['duration']:
        mins = int(metadata['duration'] // 60)
        secs = int(metadata['duration'] % 60)
        print(f"⏱️  时长: {mins}分{secs}秒")
    
    print("-"*50)
    
    # 核心元数据
    meta_items = [
        ("🎵 标题", metadata['title']),
        ("👤 作者", metadata['artist']), 
        ("💿 专辑", metadata['album']),
        ("#️⃣ 音轨号", metadata['track']),
        ("💿 碟号", metadata['disc']),
    ]
    
    for icon, value in meta_items:
        if value:
            print(f"{icon}  {value}")
        else:
            print(f"{icon}  [未找到]")
    
    print("-"*50)
    
    # 状态信息
    status_items = [
        ("📝 歌词", metadata['lyrics']),
        ("🖼️  封面", metadata['cover']),
    ]
    
    for icon, data in status_items:
        status = "✅ 已提取" if data else "❌ 未找到"
        print(f"{icon}: {status}")

def debug_mp3_tags(file_path):
    """调试函数：显示MP3文件的所有ID3标签"""
    try:
        id3 = ID3(file_path)
        print(f"\n🔍 MP3标签调试信息: {Path(file_path).name}")
        print("="*60)
        
        print(f"找到 {len(id3.keys())} 个标签帧:")
        
        # 分类显示标签
        lyric_frames = []
        cover_frames = []
        text_frames = []
        other_frames = []
        
        for frame_id in id3.keys():
            if 'USLT' in frame_id or 'SYLT' in frame_id:
                lyric_frames.append(frame_id)
            elif 'APIC' in frame_id:
                cover_frames.append(frame_id)
            elif frame_id.startswith(('T', 'W', 'C')):  # 文本帧
                text_frames.append(frame_id)
            else:
                other_frames.append(frame_id)
        
        # 显示歌词帧
        if lyric_frames:
            print(f"\n🎵 歌词相关帧 ({len(lyric_frames)} 个):")
            for frame_id in lyric_frames:
                frame = id3[frame_id]
                frame_type = "USLT" if 'USLT' in frame_id else "SYLT"
                print(f"  • {frame_id} ({frame_type})")
                if isinstance(frame, USLT):
                    text_preview = frame.text[:100] + "..." if len(frame.text) > 100 else frame.text
                    print(f"    内容预览: {text_preview}")
                elif isinstance(frame, SYLT):
                    print(f"    同步歌词行数: {len(frame.lyrics) if hasattr(frame, 'lyrics') else '未知'}")
        
        # 显示封面帧
        if cover_frames:
            print(f"\n🖼️  封面帧 ({len(cover_frames)} 个):")
            for frame_id in cover_frames:
                frame = id3[frame_id]
                print(f"  • {frame_id}")
                if hasattr(frame, 'mime'):
                    print(f"    类型: {frame.mime}")
                if hasattr(frame, 'data'):
                    print(f"    大小: {len(frame.data)} 字节")
        
        # 显示重要文本帧
        important_text = ['TIT2', 'TPE1', 'TALB', 'TRCK', 'TPOS']
        if any(frame in text_frames for frame in important_text):
            print(f"\n📝 重要文本帧:")
            for frame_id in important_text:
                if frame_id in id3:
                    frame = id3[frame_id]
                    value = frame.text[0] if hasattr(frame, 'text') else str(frame)
                    print(f"  • {frame_id}: {value}")
        
        # 显示其他帧数量
        if other_frames:
            print(f"\n📋 其他帧 ({len(other_frames)} 个):")
            print(f"  {', '.join(other_frames[:10])}")
            if len(other_frames) > 10:
                print(f"  ... 还有 {len(other_frames)-10} 个")
        
        print("="*60)
        
    except ID3NoHeaderError:
        print("❌ 此MP3文件没有ID3标签")
    except Exception as e:
        print(f"❌ 调试失败: {e}")

def main():
    """主交互函数"""
    # 清除屏幕（跨平台）
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 伪3D ASCII艺术标题：SMPE
    print("\n" + "="*60)
    print("\n")
    print("      ███████╗███╗   ███╗██████╗ ███████╗")
    print("      ██╔════╝████╗ ████║██╔══██╗██╔════╝")
    print("      ███████╗██╔████╔██║██████╔╝█████╗  ")
    print("      ╚════██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ")
    print("      ███████║██║ ╚═╝ ██║██║     ███████╗")
    print("      ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝")
    print("\n")
    print("      ╔══════════════════════════════════════════╗")
    print("      ║     S O N G   M E T A D A T A           ║")
    print("      ║     P A R S I N G   E N G I N E         ║")
    print("      ╚══════════════════════════════════════════╝")
    print("\n" + "="*60)
    print("          专业音乐文件元数据解析工具 (MP3歌词强化版)")
    print("="*60)
    print("📢 支持格式: MP3, FLAC, M4A, MP4, OGG, OPUS")
    print("📢 命令: DL=保存全部 | L=仅歌词 | C=仅封面 | DEBUG=查看MP3标签")
    print("📢 输入 'exit' 或 'quit' 退出")
    print("-"*60)
    
    # 添加一点延迟让用户欣赏标题
    import time
    time.sleep(0.5)
    
    current_metadata = None
    
    while True:
        try:
            user_input = input("\n🎯 请输入文件路径或命令: ").strip()
            
            # 退出命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n" + "="*60)
                print("        感谢使用 SMPE - Song Metadata Parsing Engine")
                print("="*60)
                print("\n再见！👋")
                break
            # 保存命令
            if user_input.upper() == 'DL':
                if current_metadata:
                    MetadataSaver.save_all(current_metadata)
                else:
                    print("⚠️  请先解析一个文件")
                continue
            elif user_input.upper() == 'L':
                if current_metadata and current_metadata['lyrics']:
                    base_name = Path(current_metadata['file_name']).stem
                    lrc_file = f"{base_name}_lyrics.lrc"
                    if MetadataSaver._save_lyrics(current_metadata['lyrics'], lrc_file):
                        print(f"✅ 歌词已保存: {lrc_file}")
                else:
                    print("⚠️  无歌词可保存")
                continue
            elif user_input.upper() == 'C':
                if current_metadata and current_metadata['cover']:
                    base_name = Path(current_metadata['file_name']).stem
                    png_file = f"{base_name}_cover.png"
                    if MetadataSaver._save_cover(current_metadata['cover'], png_file):
                        print(f"✅ 封面已保存: {png_file}")
                else:
                    print("⚠️  无封面可保存")
                continue
            elif user_input.upper() == 'DEBUG':
                if current_metadata and current_metadata['format'] == 'MP3':
                    debug_mp3_tags(current_metadata['file_name'])
                elif current_metadata:
                    print("⚠️  DEBUG命令仅支持MP3文件")
                else:
                    print("⚠️  请先解析一个MP3文件")
                continue
            
            # 文件路径处理
            file_path = user_input
            for quote in ['"', "'"]:
                if file_path.startswith(quote) and file_path.endswith(quote):
                    file_path = file_path[1:-1]
            
            if not Path(file_path).exists():
                print(f"❌ 文件不存在: {file_path}")
                continue
            
            # 解析文件
            extractor = MusicMetadataExtractor(file_path)
            current_metadata = extractor.extract()
            
            if current_metadata:
                display_metadata(current_metadata)
            else:
                print("❌ 文件解析失败")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    # 检查依赖
    try:
        import mutagen
        from mutagen.id3 import ID3, USLT, SYLT
    except ImportError:
        print("❌ 未找到 mutagen 库")
        print("💡 请安装: pip install mutagen")
        sys.exit(1)
    
    # 运行主程序
    main()
    
    # 如果是双击运行，保持窗口
    if os.name == 'nt' and 'PROMPT' not in os.environ:
        input("\n按 Enter 键退出...")
