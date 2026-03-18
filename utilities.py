"""
Utility commands.
"""
import base64
import hashlib
import json
import re
import urllib.parse
from datetime import datetime, timedelta

import httpx

from commands.base import Command, CommandContext, CommandResult, command


@command("calculate", description="Calculate mathematical expressions", aliases=["calc", "math"], min_args=1, category="utilities")
class CalculateCommand(Command):
    usage_examples = [
        "!calc 2 + 2",
        "!calc 10 * 5 / 2",
        "!calc sqrt(16)",
        "!calc 2^10",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        expression = ctx.args_str
        
        # Sanitize input
        allowed_chars = set("0123456789+-*/().^ sqrtcobaistnlgr")
        if not all(c in allowed_chars for c in expression.lower()):
            return CommandResult(
                success=False,
                message="❌ Invalid characters in expression"
            )
        
        try:
            # Replace common symbols
            expr = expression.replace("^", "**")
            expr = expr.replace("sqrt", "__import__('math').sqrt")
            
            # Evaluate safely
            result = eval(expr, {"__builtins__": {}}, {"__import__": __import__})
            
            return CommandResult(
                success=True,
                message=f"🧮 {expression} = *{result}*"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"❌ Error: {str(e)}"
            )


@command("convert", description="Convert units", min_args=3, category="utilities")
class ConvertCommand(Command):
    usage_examples = [
        "!convert 10 km to miles",
        "!convert 100 USD to EUR",
        "!convert 1 hour to minutes",
    ]
    
    CONVERSIONS = {
        # Length
        ("km", "miles"): 0.621371,
        ("miles", "km"): 1.60934,
        ("m", "ft"): 3.28084,
        ("ft", "m"): 0.3048,
        ("cm", "in"): 0.393701,
        ("in", "cm"): 2.54,
        # Weight
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("g", "oz"): 0.035274,
        ("oz", "g"): 28.3495,
        # Volume
        ("l", "gal"): 0.264172,
        ("gal", "l"): 3.78541,
        # Time
        ("hour", "minutes"): 60,
        ("hours", "minutes"): 60,
        ("minutes", "seconds"): 60,
        ("day", "hours"): 24,
        ("days", "hours"): 24,
        ("week", "days"): 7,
        ("year", "days"): 365.25,
    }
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            value = float(ctx.args[0])
            from_unit = ctx.args[1].lower()
            to_unit = ctx.args[3].lower()
            
            # Check direct conversion
            key = (from_unit, to_unit)
            if key in self.CONVERSIONS:
                result = value * self.CONVERSIONS[key]
                return CommandResult(
                    success=True,
                    message=f"📐 {value} {from_unit} = *{result:.4f}* {to_unit}"
                )
            
            # Check reverse conversion
            reverse_key = (to_unit, from_unit)
            if reverse_key in self.CONVERSIONS:
                result = value / self.CONVERSIONS[reverse_key]
                return CommandResult(
                    success=True,
                    message=f"📐 {value} {from_unit} = *{result:.4f}* {to_unit}"
                )
            
            # Same unit
            if from_unit == to_unit:
                return CommandResult(
                    success=True,
                    message=f"📐 {value} {from_unit} = *{value}* {to_unit}"
                )
            
            return CommandResult(
                success=False,
                message=f"❌ Conversion not supported: {from_unit} to {to_unit}"
            )
            
        except (ValueError, IndexError):
            return CommandResult(
                success=False,
                message="❌ Usage: !convert <value> <from> to <to>\nExample: !convert 10 km to miles"
            )


@command("base64", description="Encode/decode Base64", min_args=2, category="utilities")
class Base64Command(Command):
    usage_examples = [
        "!base64 encode Hello World",
        "!base64 decode SGVsbG8gV29ybGQ=",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        action = ctx.args[0].lower()
        text = " ".join(ctx.args[1:])
        
        try:
            if action == "encode":
                encoded = base64.b64encode(text.encode()).decode()
                return CommandResult(success=True, message=f"🔐 Encoded:\n`{encoded}`")
            elif action == "decode":
                decoded = base64.b64decode(text.encode()).decode()
                return CommandResult(success=True, message=f"🔓 Decoded:\n{decoded}")
            else:
                return CommandResult(success=False, message="❌ Use 'encode' or 'decode'")
        except Exception as e:
            return CommandResult(success=False, message=f"❌ Error: {str(e)}")


@command("hash", description="Generate hash of text", min_args=2, category="utilities")
class HashCommand(Command):
    usage_examples = [
        "!hash md5 Hello World",
        "!hash sha256 password123",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        algo = ctx.args[0].lower()
        text = " ".join(ctx.args[1:])
        
        try:
            if algo == "md5":
                result = hashlib.md5(text.encode()).hexdigest()
            elif algo == "sha1":
                result = hashlib.sha1(text.encode()).hexdigest()
            elif algo == "sha256":
                result = hashlib.sha256(text.encode()).hexdigest()
            elif algo == "sha512":
                result = hashlib.sha512(text.encode()).hexdigest()
            else:
                return CommandResult(
                    success=False,
                    message="❌ Supported: md5, sha1, sha256, sha512"
                )
            
            return CommandResult(success=True, message=f"🔑 {algo.upper()}:\n`{result}`")
        except Exception as e:
            return CommandResult(success=False, message=f"❌ Error: {str(e)}")


@command("urlencode", description="URL encode/decode", min_args=2, category="utilities")
class URLEncodeCommand(Command):
    usage_examples = [
        "!urlencode encode hello world",
        "!urlencode decode hello%20world",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        action = ctx.args[0].lower()
        text = " ".join(ctx.args[1:])
        
        try:
            if action == "encode":
                result = urllib.parse.quote(text)
                return CommandResult(success=True, message=f"🔗 Encoded:\n`{result}`")
            elif action == "decode":
                result = urllib.parse.unquote(text)
                return CommandResult(success=True, message=f"🔗 Decoded:\n{result}")
            else:
                return CommandResult(success=False, message="❌ Use 'encode' or 'decode'")
        except Exception as e:
            return CommandResult(success=False, message=f"❌ Error: {str(e)}")


@command("json", description="Format JSON", min_args=1, category="utilities")
class JSONCommand(Command):
    usage_examples = [
        "!json {\"name\":\"John\",\"age\":30}",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            data = json.loads(ctx.args_str)
            formatted = json.dumps(data, indent=2)
            return CommandResult(success=True, message=f"📋 Formatted JSON:\n```json\n{formatted}\n```")
        except json.JSONDecodeError as e:
            return CommandResult(success=False, message=f"❌ Invalid JSON: {str(e)}")


@command("lorem", description="Generate Lorem Ipsum text", category="utilities")
class LoremCommand(Command):
    usage_examples = [
        "!lorem - Generate 1 paragraph",
        "!lorem 3 - Generate 3 paragraphs",
    ]
    
    LOREM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            paragraphs = int(ctx.args[0]) if ctx.args else 1
            paragraphs = min(max(paragraphs, 1), 10)
        except ValueError:
            paragraphs = 1
        
        text = "\n\n".join([self.LOREM] * paragraphs)
        return CommandResult(success=True, message=f"📝 *Lorem Ipsum* ({paragraphs} paragraph(s)):\n\n{text}")


@command("countdown", description="Countdown timer", min_args=1, category="utilities")
class CountdownCommand(Command):
    usage_examples = [
        "!countdown 2025-01-01",
        "!countdown 2024-12-25 00:00:00",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            date_str = ctx.args[0]
            if len(ctx.args) > 1:
                date_str += " " + ctx.args[1]
            else:
                date_str += " 00:00:00"
            
            target = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            if target < now:
                return CommandResult(success=False, message="❌ That date is in the past!")
            
            diff = target - now
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return CommandResult(
                success=True,
                message=f"⏰ *Countdown to {target.strftime('%Y-%m-%d %H:%M:%S')}*\n\n{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
            )
        except ValueError:
            return CommandResult(
                success=False,
                message="❌ Usage: !countdown YYYY-MM-DD [HH:MM:SS]"
            )


@command("color", description="Get color information", min_args=1, category="utilities")
class ColorCommand(Command):
    usage_examples = [
        "!color #FF5733",
        "!color red",
        "!color rgb(255,0,0)",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        color_input = ctx.args_str
        
        # Simple color lookup
        colors = {
            "red": "#FF0000",
            "green": "#00FF00",
            "blue": "#0000FF",
            "yellow": "#FFFF00",
            "cyan": "#00FFFF",
            "magenta": "#FF00FF",
            "black": "#000000",
            "white": "#FFFFFF",
            "gray": "#808080",
            "orange": "#FFA500",
            "purple": "#800080",
            "pink": "#FFC0CB",
        }
        
        hex_color = colors.get(color_input.lower())
        
        if not hex_color and color_input.startswith("#"):
            hex_color = color_input
        
        if hex_color:
            # Convert hex to RGB
            hex_clean = hex_color.lstrip("#")
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            
            return CommandResult(
                success=True,
                message=f"🎨 *Color: {color_input}*\n\nHex: {hex_color.upper()}\nRGB: rgb({r}, {g}, {b})\n\n■ Block preview of color"
            )
        
        return CommandResult(success=False, message="❌ Color not found. Try: red, green, blue, #FF5733, etc.")


@command("qr", description="Generate QR code URL", min_args=1, category="utilities")
class QRCommand(Command):
    usage_examples = [
        "!qr https://example.com",
        "!qr Hello World",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str
        encoded = urllib.parse.quote(text)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded}"
        
        return CommandResult(
            success=True,
            message=f"📱 *QR Code for:*\n{text}\n\n{qr_url}"
        )


@command("shorten", description="Get shortened URL", min_args=1, category="utilities")
class ShortenCommand(Command):
    usage_examples = [
        "!shorten https://example.com/very/long/url",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        url = ctx.args_str
        
        if not url.startswith(("http://", "https://")):
            return CommandResult(success=False, message="❌ Please provide a valid URL starting with http:// or https://")
        
        # Return a shortened URL using TinyURL API
        encoded = urllib.parse.quote(url)
        short_url = f"https://tinyurl.com/api-create.php?url={encoded}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(short_url, timeout=10.0)
                if response.status_code == 200:
                    return CommandResult(
                        success=True,
                        message=f"🔗 *Shortened URL:*\nOriginal: {url}\nShort: {response.text}"
                    )
        except:
            pass
        
        # Fallback
        return CommandResult(
            success=True,
            message=f"🔗 *URL Shortener:*\nOriginal: {url}\n\nUse: https://tinyurl.com/create.php?url={encoded}"
        )
