"""
Media handling commands - save view-once, download, convert media.
"""
import base64
import hashlib
import io
import re
import urllib.parse
from typing import Optional

import httpx

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier
from utils.redis_client import redis_client


@command("save", description="Save view-once media or download from URL", min_args=1, category="media")
class SaveMediaCommand(Command):
    """Save view-once photos/videos or download media from URLs."""
    usage_examples = [
        "!save <reply to view-once> - Save view-once media",
        "!save https://example.com/image.jpg - Download image",
        "!save video https://youtube.com/watch?v=... - Download video",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        url = ctx.args_str
        
        # Check if it's a view-once save request
        if url.lower() in ["viewonce", "view-once", "vo", "once"]:
            return CommandResult(
                success=True,
                message="""
📸 *View-Once Saver*

To save a view-once photo/video:
1. Long press the view-once message
2. Select "Reply"
3. Type: !save

The bot will capture and save the media for you!

⚠️ Note: This works by capturing the media when it's first viewed. The sender will see "opened" status.
                """.strip()
            )
        
        # Check if it's a URL
        if url.startswith(("http://", "https://")):
            return await self._download_from_url(url, ctx)
        
        # Check for video download request
        if ctx.args[0].lower() in ["video", "yt", "youtube", "tiktok", "ig", "instagram"]:
            platform = ctx.args[0].lower()
            video_url = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else None
            
            if not video_url:
                return CommandResult(
                    success=False,
                    message="❌ Please provide a video URL\nExample: !save video https://youtube.com/watch?v=..."
                )
            
            return await self._download_video(video_url, platform)
        
        return CommandResult(
            success=False,
            message="❌ Usage:\n• !save viewonce (reply to view-once)\n• !save <image URL>\n• !save video <video URL>"
        )
    
    async def _download_from_url(self, url: str, ctx: CommandContext) -> CommandResult:
        """Download media from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0, follow_redirects=True)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "")
                size = len(response.content)
                
                # Check file size (max 20MB for WhatsApp)
                if size > 20 * 1024 * 1024:
                    return CommandResult(
                        success=False,
                        message="❌ File too large (max 20MB)"
                    )
                
                # Determine media type
                if "image" in content_type:
                    media_type = "image"
                    emoji = "🖼️"
                elif "video" in content_type:
                    media_type = "video"
                    emoji = "🎥"
                elif "audio" in content_type:
                    media_type = "audio"
                    emoji = "🎵"
                else:
                    media_type = "file"
                    emoji = "📄"
                
                # Store in Redis temporarily (base64 encoded)
                media_id = hashlib.md5(url.encode()).hexdigest()[:12]
                await redis_client.set(
                    f"media:{ctx.user.id}:{media_id}",
                    base64.b64encode(response.content).decode(),
                    expire=3600  # 1 hour
                )
                
                size_mb = size / (1024 * 1024)
                
                return CommandResult(
                    success=True,
                    message=f"""
{emoji} *Media Downloaded*

Type: {media_type.title()}
Size: {size_mb:.2f} MB
ID: `{media_id}`

Use !get {media_id} to retrieve (valid for 1 hour)
                    """.strip()
                )
                
        except httpx.HTTPError as e:
            return CommandResult(
                success=False,
                message=f"❌ Failed to download: {str(e)}"
            )
    
    async def _download_video(self, url: str, platform: str) -> CommandResult:
        """Download video from various platforms."""
        # This would integrate with yt-dlp or similar
        # For now, return instructions
        
        downloaders = {
            "youtube": "https://y2mate.is",
            "yt": "https://y2mate.is",
            "tiktok": "https://ssstik.io",
            "instagram": "https://snapinsta.app",
            "ig": "https://snapinsta.app",
            "twitter": "https://ssstwitter.com",
            "x": "https://ssstwitter.com",
            "facebook": "https://fdown.net",
            "fb": "https://fdown.net",
        }
        
        downloader = downloaders.get(platform, "https://y2mate.is")
        encoded_url = urllib.parse.quote(url)
        
        return CommandResult(
            success=True,
            message=f"""
🎥 *Video Download*

Platform: {platform.title()}
URL: {url}

Download here: {downloader}

Or use these direct services:
• YouTube: https://y2mate.is/?video={encoded_url}
• TikTok: https://ssstik.io
• Instagram: https://snapinsta.app

⚠️ Respect copyright and terms of service!
            """.strip()
        )


@command("get", description="Retrieve saved media by ID", min_args=1, category="media")
class GetMediaCommand(Command):
    """Retrieve previously saved media."""
    usage_examples = [
        "!get abc123 - Retrieve media with ID abc123",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        media_id = ctx.args[0]
        
        # Try to get from Redis
        media_data = await redis_client.get(f"media:{ctx.user.id}:{media_id}")
        
        if not media_data:
            return CommandResult(
                success=False,
                message="❌ Media not found or expired (valid for 1 hour)"
            )
        
        return CommandResult(
            success=True,
            message=f"📎 *Media Retrieved*\n\nID: `{media_id}`\n\nNote: In a full implementation, this would send the actual file."
        )


@command("screenshot", description="Take screenshot of website", min_args=1, category="media")
class ScreenshotCommand(Command):
    """Generate screenshot of a website."""
    usage_examples = [
        "!screenshot https://google.com",
        "!screenshot example.com",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 15
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        url = ctx.args_str
        
        # Ensure URL has protocol
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Use screenshot API services
        screenshot_apis = [
            f"https://shot.screenshotapi.net/screenshot?token=&url={urllib.parse.quote(url)}&output=image&file_type=png&wait_for_event=load",
            f"https://api.apiflash.com/v1/urltoimage?access_key=&url={urllib.parse.quote(url)}&format=png",
        ]
        
        return CommandResult(
            success=True,
            message=f"""
📸 *Website Screenshot*

URL: {url}

Screenshot services:
• https://screenshotapi.net
• https://apiflash.com
• https://screenshotlayer.com

Try: https://mini.s-shot.ru/1024x768/JPEG/1024/Z100/?{urllib.parse.quote(url)}
            """.strip()
        )


@command("sticker", description="Create sticker from image/text", min_args=1, category="media")
class StickerCommand(Command):
    """Create WhatsApp stickers."""
    usage_examples = [
        "!sticker hello - Text to sticker",
        "!sticker <reply to image> - Image to sticker",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str
        
        # Sticker creation APIs
        return CommandResult(
            success=True,
            message=f"""
🎨 *Sticker Creator*

Text: "{text}"

Create stickers at:
• https://stickers.gg/create
• https://wa-sticker.vercel.app

Or use these sticker packs:
• !stickers - List popular sticker packs
            """.strip()
        )


@command("stickers", description="Get popular sticker packs", category="media")
class StickersListCommand(Command):
    """List popular sticker packs."""
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        packs = [
            ("Pepe the Frog", "https://t.me/addstickers/PepeTheFrogAnimated"),
            ("Doge", "https://t.me/addstickers/DogeStickers"),
            ("Cat Memes", "https://t.me/addstickers/CatMemesPack"),
            ("Programming", "https://t.me/addstickers/DevStickers"),
            ("Crypto", "https://t.me/addstickers/CryptoStickersPack"),
        ]
        
        lines = ["🎨 *Popular Sticker Packs*\n"]
        for name, url in packs:
            lines.append(f"• *{name}*\n  {url}\n")
        
        return CommandResult(success=True, message="\n".join(lines))


@command("compress", description="Compress image/video", min_args=1, category="media")
class CompressCommand(Command):
    """Compress media files."""
    usage_examples = [
        "!compress image <reply to image> - Compress image",
        "!compress video <reply to video> - Compress video",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        media_type = ctx.args[0].lower() if ctx.args else "image"
        
        compressors = {
            "image": [
                "https://tinypng.com",
                "https://compressjpeg.com",
                "https://squoosh.app",
            ],
            "video": [
                "https://www.freeconvert.com/compress-video",
                "https://cloudconvert.com/compress-video",
            ],
            "pdf": [
                "https://smallpdf.com/compress-pdf",
                "https://ilovepdf.com/compress_pdf",
            ],
        }
        
        services = compressors.get(media_type, compressors["image"])
        
        return CommandResult(
            success=True,
            message=f"""
🗜️ *{media_type.title()} Compression*

Online tools:
{chr(10).join(f"• {url}" for url in services)}

For WhatsApp, images are auto-compressed when sent!
            """.strip()
        )


@command("metadata", description="Extract metadata from media", min_args=1, category="media")
class MetadataCommand(Command):
    """Extract EXIF/metadata from images."""
    usage_examples = [
        "!metadata <reply to image> - Get image metadata",
        "!metadata https://example.com/photo.jpg - Get online image metadata",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="""
📋 *Metadata Extractor*

Upload your image to:
• https://exifdata.com
• https://pic2map.com
• https://www.exifviewer.org

This will show:
📍 GPS location (if available)
📷 Camera info
📅 Date taken
🔧 Settings used

⚠️ Be careful sharing photos with location data!
            """.strip()
        )


@command("removebg", description="Remove background from image", min_args=1, category="media")
class RemoveBGCommand(Command):
    """Remove background from images."""
    usage_examples = [
        "!removebg <reply to image>",
        "!removebg https://example.com/photo.jpg",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="""
✂️ *Background Remover*

Free tools:
• https://www.remove.bg (free tier)
• https://www.photoroom.com/tools/background-remover
• https://www.adobe.com/express/feature/image/remove-background

Upload your image and get a transparent PNG!
            """.strip()
        )


@command("ocr", description="Extract text from image (OCR)", min_args=1, category="media")
class OCRCommand(Command):
    """Optical Character Recognition."""
    usage_examples = [
        "!ocr <reply to image with text>",
        "!ocr https://example.com/image-with-text.jpg",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="""
📝 *OCR (Text from Image)*

Free OCR tools:
• https://www.onlineocr.net
• https://ocr.space
• https://www.newocr.com

Or use Google Lens on your phone!

Supports: English, Spanish, French, German, Chinese, Japanese, Arabic, and more!
            """.strip()
        )


@command("gif", description="Search or create GIFs", min_args=1, category="media")
class GIFCommand(Command):
    """Search for GIFs."""
    usage_examples = [
        "!gif happy dance - Search for happy dance GIF",
        "!gif trending - Get trending GIFs",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        query = ctx.args_str
        
        # Giphy search URL
        encoded_query = urllib.parse.quote(query)
        
        return CommandResult(
            success=True,
            message=f"""
🎬 *GIF Search: "{query}"*

Search results:
• https://giphy.com/search/{encoded_query}
• https://tenor.com/search/{encoded_query}-gifs

Trending:
• https://giphy.com/trending-gifs

Tap and hold a GIF to save it!
            """.strip()
        )


@command("tts", description="Text to Speech", min_args=1, category="media")
class TTSCommand(Command):
    """Convert text to speech."""
    usage_examples = [
        "!tts Hello World - Convert to speech",
        "!tts es Hola mundo - Spanish speech",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        # Check if first arg is language code
        lang = "en"
        text = ctx.args_str
        
        if ctx.args[0].lower() in ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]:
            lang = ctx.args[0].lower()
            text = " ".join(ctx.args[1:])
        
        # Google TTS URL (for demonstration)
        encoded_text = urllib.parse.quote(text)
        
        return CommandResult(
            success=True,
            message=f"""
🔊 *Text to Speech*

Text: "{text}"
Language: {lang.upper()}

Online TTS:
• https://ttsmp3.com
• https://naturalreaders.com/online/
• https://voicegenerator.io

Or use: https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob
            """.strip()
        )


@command("voice", description="Voice changer effects", min_args=1, category="media")
class VoiceCommand(Command):
    """Voice changer effects."""
    usage_examples = [
        "!voice robot - Robot voice effect",
        "!voice deep - Deep voice effect",
        "!voice chipmunk - Chipmunk voice effect",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        effect = ctx.args[0].lower()
        
        effects = {
            "robot": "🤖 Robot",
            "deep": "🔊 Deep Voice",
            "chipmunk": "🐿️ Chipmunk",
            "echo": "📢 Echo",
            "reverse": "⏪ Reverse",
            "slow": "🐌 Slow Motion",
            "fast": "⚡ Fast",
        }
        
        effect_name = effects.get(effect, "🎙️ Custom")
        
        return CommandResult(
            success=True,
            message=f"""
{effect_name} *Voice Effect*

Online voice changers:
• https://voicechanger.io
• https://www.voicechanger.io
• https://www.myinstants.com/en/instant/voice-changer/

Available effects:
{chr(10).join(f"• {k} - {v}" for k, v in effects.items())}

Upload your audio and apply effects!
            """.strip()
        )
