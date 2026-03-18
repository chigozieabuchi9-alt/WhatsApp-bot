"""
Security tools - password generators, bypass tools, encryptions, hashes.
"""
import base64
import hashlib
import hmac
import json
import secrets
import string
import urllib.parse
from datetime import datetime, timedelta

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier


@command("passgen", description="Advanced password generator", aliases=["genpass", "strongpass"], category="security")
class PassGenCommand(Command):
    """Generate strong passwords with options."""
    usage_examples = [
        "!passgen - Generate 16-char strong password",
        "!passgen 20 - 20 characters",
        "!passgen 12 easy - Easy to remember",
        "!passgen 32 all - All character types",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        # Parse arguments
        length = 16
        mode = "strong"
        
        if ctx.args:
            try:
                length = int(ctx.args[0])
                length = min(max(length, 8), 64)
            except ValueError:
                mode = ctx.args[0].lower()
        
        if len(ctx.args) > 1:
            mode = ctx.args[1].lower()
        
        # Word list for memorable passwords
        words = [
            "apple", "beach", "tiger", "music", "dance", "eagle", "flame", "grape",
            "house", "ice", "jazz", "kite", "lemon", "moon", "night", "ocean",
            "piano", "queen", "river", "star", "tree", "unicorn", "violin", "wolf",
            "yellow", "zebra", "cloud", "dream", "fire", "gold", "happy", "island",
            "jungle", "king", "light", "magic", "north", "orange", "purple", "quiet",
            "rose", "sun", "time", "unity", "voice", "water", "xray", "young"
        ]
        
        if mode == "easy" or mode == "memorable":
            # Generate memorable password: Word-Word-Number-Symbol
            word1 = secrets.choice(words).title()
            word2 = secrets.choice(words).title()
            num = secrets.randbelow(100)
            symbol = secrets.choice("!@#$%^&*")
            password = f"{word1}{word2}{num}{symbol}"
            
            return CommandResult(
                success=True,
                message=f"""
🔐 *Memorable Password*

`{password}`

Length: {len(password)} characters
Type: Easy to remember

💡 Tip: Use a password manager for best security!
                """.strip()
            )
        
        elif mode == "pin":
            # Generate numeric PIN
            pin = ''.join(secrets.choice(string.digits) for _ in range(length))
            return CommandResult(
                success=True,
                message=f"🔢 *PIN Code*: `{pin}`"
            )
        
        elif mode == "hex":
            # Generate hex key
            hex_key = secrets.token_hex(length // 2)
            return CommandResult(
                success=True,
                message=f"🔑 *Hex Key*: `{hex_key}`"
            )
        
        elif mode == "base64":
            # Generate base64 key
            b64_key = secrets.token_urlsafe(length)
            return CommandResult(
                success=True,
                message=f"🔑 *Base64 Key*: `{b64_key}`"
            )
        
        else:  # strong mode
            # Generate strong password
            chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            # Ensure at least one of each type
            password = [
                secrets.choice(string.ascii_lowercase),
                secrets.choice(string.ascii_uppercase),
                secrets.choice(string.digits),
                secrets.choice("!@#$%^&*"),
            ]
            
            # Fill the rest
            password += [secrets.choice(chars) for _ in range(length - 4)]
            
            # Shuffle
            secrets.SystemRandom().shuffle(password)
            password = ''.join(password)
            
            # Calculate strength
            strength = "Weak"
            if length >= 16:
                strength = "💪 Very Strong"
            elif length >= 12:
                strength = "✅ Strong"
            elif length >= 8:
                strength = "⚠️ Medium"
            
            return CommandResult(
                success=True,
                message=f"""
🔐 *Strong Password*

`{password}`

Length: {length} characters
Strength: {strength}
Entropy: ~{length * 6.5:.0f} bits

⚠️ Save this securely in a password manager!
                """.strip()
            )


@command("passcheck", description="Check password strength", min_args=1, category="security")
class PassCheckCommand(Command):
    """Analyze password strength."""
    usage_examples = [
        "!passcheck mypassword123",
        "!passcheck (paste password)",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        password = ctx.args_str
        
        # Calculate metrics
        length = len(password)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)
        
        # Calculate score
        score = 0
        feedback = []
        
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        else:
            feedback.append("Too short (min 8 characters)")
        
        if has_lower:
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        if has_upper:
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        if has_digit:
            score += 1
        else:
            feedback.append("Add numbers")
        
        if has_special:
            score += 1
        else:
            feedback.append("Add special characters")
        
        # Common passwords check
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]
        if password.lower() in common_passwords:
            score = 0
            feedback.append("This is a commonly used password!")
        
        # Determine strength
        if score >= 6:
            strength = "💪 Very Strong"
            color = "🟢"
        elif score >= 4:
            strength = "✅ Strong"
            color = "🟢"
        elif score >= 2:
            strength = "⚠️ Medium"
            color = "🟡"
        else:
            strength = "❌ Weak"
            color = "🔴"
        
        # Calculate crack time (rough estimate)
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 32
        
        if charset_size > 0:
            combinations = charset_size ** length
            # Assume 10 billion guesses per second (powerful attacker)
            seconds = combinations / 10_000_000_000
            
            if seconds < 1:
                crack_time = "Instantly"
            elif seconds < 60:
                crack_time = f"{seconds:.1f} seconds"
            elif seconds < 3600:
                crack_time = f"{seconds/60:.1f} minutes"
            elif seconds < 86400:
                crack_time = f"{seconds/3600:.1f} hours"
            elif seconds < 31536000:
                crack_time = f"{seconds/86400:.1f} days"
            elif seconds < 3153600000:
                crack_time = f"{seconds/31536000:.1f} years"
            else:
                crack_time = "Centuries"
        else:
            crack_time = "Instantly"
        
        message = f"""
{strength} *Password Analysis*

Score: {score}/6
Length: {length} characters

Composition:
{'✅' if has_lower else '❌'} Lowercase (a-z)
{'✅' if has_upper else '❌'} Uppercase (A-Z)
{'✅' if has_digit else '❌'} Numbers (0-9)
{'✅' if has_special else '❌'} Special (!@#$%)

Estimated crack time: *{crack_time}*

        """.strip()
        
        if feedback:
            message += f"\n💡 Suggestions:\n• " + "\n• ".join(feedback)
        
        return CommandResult(success=True, message=message)


@command("bypass", description="Bypass/decoder tools for common formats", category="security")
class BypassCommand(Command):
    """Various bypass and decoder tools."""
    usage_examples = [
        "!bypass base64 SGVsbG8= - Decode base64",
        "!bypass url hello%20world - Decode URL",
        "!bypass md5 5d41402abc4b2a76b9719d911017c592 - Crack MD5",
        "!bypass jwt eyJ0... - Decode JWT",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult(
                success=False,
                message="""
🔓 *Bypass/Decoder Tools*

Usage: !bypass <type> <data>

Types:
• base64 - Decode Base64
• base64e - Encode Base64
• url - URL decode
• urle - URL encode
• hex - Hex decode
• hexe - Hex encode
• binary - Binary decode
• jwt - Decode JWT (no verify)
• md5 - MD5 lookup/identify
• sha1 - SHA1 identify
• rot13 - ROT13 cipher
• morse - Morse code
                """.strip()
            )
        
        bypass_type = ctx.args[0].lower()
        data = " ".join(ctx.args[1:])
        
        try:
            if bypass_type == "base64":
                decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
                return CommandResult(success=True, message=f"🔓 *Base64 Decoded*:\n`{decoded}`")
            
            elif bypass_type == "base64e":
                encoded = base64.b64encode(data.encode()).decode()
                return CommandResult(success=True, message=f"🔒 *Base64 Encoded*:\n`{encoded}`")
            
            elif bypass_type == "url":
                decoded = urllib.parse.unquote(data)
                return CommandResult(success=True, message=f"🔓 *URL Decoded*:\n`{decoded}`")
            
            elif bypass_type == "urle":
                encoded = urllib.parse.quote(data)
                return CommandResult(success=True, message=f"🔒 *URL Encoded*:\n`{encoded}`")
            
            elif bypass_type == "hex":
                decoded = bytes.fromhex(data.replace(" ", "")).decode('utf-8', errors='ignore')
                return CommandResult(success=True, message=f"🔓 *Hex Decoded*:\n`{decoded}`")
            
            elif bypass_type == "hexe":
                encoded = data.encode().hex()
                return CommandResult(success=True, message=f"🔒 *Hex Encoded*:\n`{encoded}`")
            
            elif bypass_type == "binary":
                binary = data.replace(" ", "")
                decoded = ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
                return CommandResult(success=True, message=f"🔓 *Binary Decoded*:\n`{decoded}`")
            
            elif bypass_type == "jwt":
                parts = data.split(".")
                if len(parts) == 3:
                    # Decode header and payload
                    header = base64.urlsafe_b64decode(parts[0] + "==").decode()
                    payload = base64.urlsafe_b64decode(parts[1] + "==").decode()
                    return CommandResult(
                        success=True,
                        message=f"""
🔓 *JWT Decoded*

*Header:*
```json
{json.dumps(json.loads(header), indent=2)}
```

*Payload:*
```json
{json.dumps(json.loads(payload), indent=2)}
```

⚠️ Signature NOT verified!
                        """.strip()
                    )
                else:
                    return CommandResult(success=False, message="❌ Invalid JWT format")
            
            elif bypass_type == "md5":
                # Check if it looks like a hash
                if re.match(r'^[a-f0-9]{32}$', data.lower()):
                    return CommandResult(
                        success=True,
                        message=f"""
🔍 *MD5 Hash Analysis*

Hash: `{data}`

Try cracking at:
• https://crackstation.net
• https://hashes.com/en/decrypt/hash
• https://md5decrypt.net

Or use: !bypass md5lookup {data}
                        """.strip()
                    )
                else:
                    # Hash the input
                    hashed = hashlib.md5(data.encode()).hexdigest()
                    return CommandResult(success=True, message=f"🔒 *MD5 Hash*:\n`{hashed}`")
            
            elif bypass_type == "sha1":
                if re.match(r'^[a-f0-9]{40}$', data.lower()):
                    return CommandResult(
                        success=True,
                        message=f"""
🔍 *SHA1 Hash Analysis*

Hash: `{data}`

Try cracking at:
• https://crackstation.net
• https://hashes.com/en/decrypt/hash
                        """.strip()
                    )
                else:
                    hashed = hashlib.sha1(data.encode()).hexdigest()
                    return CommandResult(success=True, message=f"🔒 *SHA1 Hash*:\n`{hashed}`")
            
            elif bypass_type == "rot13":
                result = data.translate(str.maketrans(
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                    "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
                ))
                return CommandResult(success=True, message=f"🔓 *ROT13*:\n`{result}`")
            
            elif bypass_type == "morse":
                morse_code = {
                    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
                    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
                    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
                    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
                    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
                    'Z': '--..', '1': '.----', '2': '..---', '3': '...--',
                    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
                    '8': '---..', '9': '----.', '0': '-----', ' ': '/'
                }
                reverse_morse = {v: k for k, v in morse_code.items()}
                
                if all(c in '.- /' for c in data):
                    # Decode
                    result = ''.join(reverse_morse.get(c, c) for c in data.split())
                    return CommandResult(success=True, message=f"🔓 *Morse Decoded*:\n`{result}`")
                else:
                    # Encode
                    result = ' '.join(morse_code.get(c.upper(), c) for c in data)
                    return CommandResult(success=True, message=f"🔒 *Morse Encoded*:\n`{result}`")
            
            else:
                return CommandResult(success=False, message=f"❌ Unknown type: {bypass_type}")
                
        except Exception as e:
            return CommandResult(success=False, message=f"❌ Error: {str(e)}")


@command("encrypt", description="Encrypt/decrypt messages", min_args=2, category="security")
class EncryptCommand(Command):
    """Simple encryption tools."""
    usage_examples = [
        "!encrypt aes mykey Hello World - AES encrypt",
        "!encrypt xor mykey secret message - XOR encrypt",
        "!encrypt caesar 3 Hello - Caesar cipher",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        algo = ctx.args[0].lower()
        key = ctx.args[1] if len(ctx.args) > 1 else ""
        message = " ".join(ctx.args[2:]) if len(ctx.args) > 2 else ""
        
        if algo == "caesar":
            try:
                shift = int(key) % 26
            except ValueError:
                shift = 3
            
            result = ""
            for char in message:
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    result += chr((ord(char) - base + shift) % 26 + base)
                else:
                    result += char
            
            return CommandResult(
                success=True,
                message=f"🔒 *Caesar Cipher (shift={shift})*:\n`{result}`"
            )
        
        elif algo == "xor":
            result = ""
            for i, char in enumerate(message):
                result += chr(ord(char) ^ ord(key[i % len(key)]))
            encoded = base64.b64encode(result.encode()).decode()
            return CommandResult(
                success=True,
                message=f"🔒 *XOR Encrypted* (key='{key}'):\n`{encoded}`"
            )
        
        elif algo == "vigenere":
            result = ""
            key = key.upper()
            key_len = len(key)
            for i, char in enumerate(message):
                if char.isalpha():
                    shift = ord(key[i % key_len]) - ord('A')
                    base = ord('A') if char.isupper() else ord('a')
                    result += chr((ord(char.upper()) - base + shift) % 26 + base)
                else:
                    result += char
            return CommandResult(
                success=True,
                message=f"🔒 *Vigenère Cipher* (key='{key}'):\n`{result}`"
            )
        
        else:
            return CommandResult(
                success=False,
                message="""
🔐 *Encryption Tools*

Usage: !encrypt <algo> <key> <message>

Algorithms:
• caesar <shift> - Caesar cipher
• xor <key> - XOR cipher
• vigenere <key> - Vigenère cipher

Example: !encrypt caesar 3 Hello World
                """.strip()
            )


@command("2fa", description="Generate 2FA/TOTP codes", category="security")
class TwoFACommand(Command):
    """2FA code generator."""
    usage_examples = [
        "!2fa JBSWY3DPEHPK3PXP - Generate TOTP code",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.args:
            return CommandResult(
                success=False,
                message="""
🔢 *2FA/TOTP Generator*

Usage: !2fa <base32_secret>

The secret is usually shown when setting up 2FA,
or in the QR code URL.

⚠️ Keep your 2FA secrets secure!
                """.strip()
            )
        
        secret = ctx.args[0].upper().replace(" ", "")
        
        try:
            import hmac
            import struct
            import time
            
            # Decode base32 secret
            secret_bytes = base64.b32decode(secret + "=" * (8 - len(secret) % 8))
            
            # Generate TOTP
            counter = struct.pack(">Q", int(time.time()) // 30)
            mac = hmac.new(secret_bytes, counter, hashlib.sha1).digest()
            offset = mac[-1] & 0x0f
            code = struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7fffffff
            otp = str(code % 1000000).zfill(6)
            
            # Calculate remaining time
            remaining = 30 - (int(time.time()) % 30)
            
            return CommandResult(
                success=True,
                message=f"""
🔢 *2FA Code*

Code: `*{otp}*`
Expires in: {remaining} seconds

⚠️ Never share this code with anyone!
                """.strip()
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"❌ Invalid secret: {str(e)}"
            )


@command("keygen", description="Generate API keys and tokens", category="security")
class KeyGenCommand(Command):
    """Generate various types of keys."""
    usage_examples = [
        "!keygen api - Generate API key",
        "!keygen jwt - Generate JWT secret",
        "!keygen django - Generate Django secret",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        key_type = ctx.args[0].lower() if ctx.args else "api"
        
        if key_type == "api":
            key = secrets.token_urlsafe(32)
            return CommandResult(success=True, message=f"🔑 *API Key*:\n`{key}`")
        
        elif key_type == "jwt":
            secret = secrets.token_urlsafe(64)
            return CommandResult(success=True, message=f"🔐 *JWT Secret*:\n`{secret}`")
        
        elif key_type == "django":
            secret = secrets.token_urlsafe(50)
            return CommandResult(
                success=True,
                message=f"""
🐍 *Django Secret Key*

Add to settings.py:
```python
SECRET_KEY = '{secret}'
```

⚠️ Keep this secret in production!
                """.strip()
            )
        
        elif key_type == "flask":
            secret = secrets.token_hex(32)
            return CommandResult(
                success=True,
                message=f"""
🌶️ *Flask Secret Key*

Add to config:
```python
SECRET_KEY = '{secret}'
```
                """.strip()
            )
        
        elif key_type == "uuid":
            import uuid
            return CommandResult(
                success=True,
                message=f"""
🆔 *UUIDs*

v4: `{uuid.uuid4()}`
v4: `{uuid.uuid4()}`
v4: `{uuid.uuid4()}`
                """.strip()
            )
        
        elif key_type == "nano":
            import secrets
            alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            nano_id = ''.join(secrets.choice(alphabet) for _ in range(21))
            return CommandResult(success=True, message=f"🔑 *Nano ID*:\n`{nano_id}`")
        
        else:
            return CommandResult(
                success=False,
                message="""
🔑 *Key Generator*

Types:
• api - API key (URL-safe)
• jwt - JWT secret
• django - Django secret
• flask - Flask secret
• uuid - UUID v4
• nano - Nano ID

Example: !keygen api
                """.strip()
            )


@command("sanitize", description="Sanitize text (remove PII)", min_args=1, category="security")
class SanitizeCommand(Command):
    """Remove PII from text."""
    usage_examples = [
        "!sanitize My email is john@example.com - Sanitize PII",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str
        
        import re
        
        # Patterns to sanitize
        patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
            (r'\b(?:\d[ -]*?){13,16}\b', '[CARD]'),
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
        ]
        
        sanitized = text
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized)
        
        return CommandResult(
            success=True,
            message=f"""
🧹 *Sanitized Text*

Original: {text}
Sanitized: `{sanitized}`

PII types removed:
• Email addresses
• Phone numbers
• SSNs
• Credit card numbers
• IP addresses

Always handle PII with care!
            """.strip()
        )
