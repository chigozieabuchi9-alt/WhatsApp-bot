"""
General utility commands.
"""
import random
from datetime import datetime

import httpx

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier


@command("help", description="Show help information", aliases=["h", "?"], category="general")
class HelpCommand(Command):
    usage_examples = [
        "!help - Show all commands",
        "!help weather - Show help for weather command",
        "!help games - Show commands in games category",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        from commands.base import registry
        
        if not ctx.args:
            # Show all categories
            categories = registry.get_all_categories()
            lines = [
                "📚 *WhatsApp Bot Commands*",
                "",
                "Use !help <category> for specific commands",
                "",
                "*Categories:*",
            ]
            for cat in sorted(categories):
                cmd_count = len(registry.get_by_category(cat))
                lines.append(f"  • {cat.title()} ({cmd_count} commands)")
            
            lines.extend([
                "",
                "Your tier: " + ctx.user.tier.value,
                "Commands used today: " + str(ctx.user.daily_command_count),
            ])
            
            return CommandResult(success=True, message="\n".join(lines))
        
        query = ctx.args[0].lower()
        
        # Check if it's a category
        if query in registry.get_all_categories():
            commands = registry.get_by_category(query)
            lines = [f"📂 *{query.title()} Commands*", ""]
            
            for cmd in sorted(commands, key=lambda c: c.name):
                lines.append(f"  !{cmd.name} - {cmd.description}")
            
            return CommandResult(success=True, message="\n".join(lines))
        
        # Check if it's a command
        cmd = registry.get(query)
        if cmd:
            return CommandResult(success=True, message=cmd.get_help_text())
        
        return CommandResult(
            success=False,
            message=f"❌ No command or category found: {query}"
        )


@command("start", description="Start using the bot", category="general")
class StartCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        message = """
🎉 *Welcome to WhatsApp Bot!*

I'm your personal assistant bot with 90+ commands across 18 categories.

*Quick Start:*
• !help - See all commands
• !weather <city> - Check weather
• !joke - Get a random joke
• !reminder <time> <message> - Set a reminder

*Your Status:*
• Tier: {tier}
• Daily limit: {limit} commands

Type !help to explore all features!
        """.strip().format(
            tier=ctx.user.tier.value.title(),
            limit="Unlimited" if ctx.user.tier.value == "admin" else "varies by tier"
        )
        return CommandResult(success=True, message=message)


@command("about", description="About this bot", aliases=["info", "bot"], category="general")
class AboutCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        message = """
🤖 *WhatsApp Bot v2.0*

A powerful multi-purpose bot with:
• 90+ commands across 18 categories
• User tier system (Guest → User → Premium → Admin)
• Rate limiting & anti-spam protection
• Wordle game with state management
• Reminder system with notifications
• Weather, news, games, and more!

*Tech Stack:*
Python • FastAPI • Twilio • PostgreSQL • Redis • Docker

Built with ❤️ for the community
        """.strip()
        return CommandResult(success=True, message=message)


@command("ping", description="Check bot response time", category="general")
class PingCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(success=True, message="🏓 Pong! Bot is online and responding.")


@command("time", description="Get current time", aliases=["clock", "now"], category="general")
class TimeCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        now = datetime.now()
        message = f"""
🕐 *Current Time*

UTC: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
Local: {now.strftime('%Y-%m-%d %I:%M:%S %p')}

Day: {now.strftime('%A')}
Date: {now.strftime('%B %d, %Y')}
        """.strip()
        return CommandResult(success=True, message=message)


@command("echo", description="Echo your message back", min_args=1, category="general")
class EchoCommand(Command):
    usage_examples = [
        "!echo Hello World",
        "!echo This is a test message",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(success=True, message=f"📢 {ctx.args_str}")


@command("roll", description="Roll a dice", aliases=["dice"], category="general")
class RollCommand(Command):
    usage_examples = [
        "!roll - Roll a 6-sided die",
        "!roll 20 - Roll a 20-sided die",
        "!roll 2d6 - Roll 2 six-sided dice",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.args:
            sides = 6
            count = 1
        elif "d" in ctx.args[0].lower():
            parts = ctx.args[0].lower().split("d")
            count = int(parts[0]) if parts[0] else 1
            sides = int(parts[1]) if len(parts) > 1 else 6
        else:
            sides = int(ctx.args[0])
            count = 1
        
        count = min(count, 10)  # Max 10 dice
        sides = min(sides, 100)  # Max 100 sides
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        if count == 1:
            message = f"🎲 You rolled: *{rolls[0]}* (d{sides})"
        else:
            message = f"🎲 Rolls: {', '.join(map(str, rolls))}\n📊 Total: *{total}* ({count}d{sides})"
        
        return CommandResult(success=True, message=message)


@command("coin", description="Flip a coin", aliases=["flip", "coinflip"], category="general")
class CoinCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        result = random.choice(["Heads", "Tails"])
        emoji = "👑" if result == "Heads" else "🪙"
        return CommandResult(success=True, message=f"{emoji} *{result}*!")


@command("choose", description="Randomly choose from options", min_args=2, category="general")
class ChooseCommand(Command):
    usage_examples = [
        "!choose pizza burger sushi",
        "!choose yes no maybe",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        choice = random.choice(ctx.args)
        return CommandResult(success=True, message=f"🎯 I choose: *{choice}*")


@command("8ball", description="Ask the magic 8-ball", min_args=1, category="general")
class EightBallCommand(Command):
    responses = [
        "🎱 It is certain.",
        "🎱 It is decidedly so.",
        "🎱 Without a doubt.",
        "🎱 Yes definitely.",
        "🎱 You may rely on it.",
        "🎱 As I see it, yes.",
        "🎱 Most likely.",
        "🎱 Outlook good.",
        "🎱 Yes.",
        "🎱 Signs point to yes.",
        "🎱 Reply hazy, try again.",
        "🎱 Ask again later.",
        "🎱 Better not tell you now.",
        "🎱 Cannot predict now.",
        "🎱 Concentrate and ask again.",
        "🎱 Don't count on it.",
        "🎱 My reply is no.",
        "🎱 My sources say no.",
        "🎱 Outlook not so good.",
        "🎱 Very doubtful.",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        response = random.choice(self.responses)
        return CommandResult(success=True, message=f"Q: {ctx.args_str}\n{response}")


@command("password", description="Generate a random password", aliases=["pass", "pwd"], category="general")
class PasswordCommand(Command):
    usage_examples = [
        "!password - Generate 12-char password",
        "!password 16 - Generate 16-char password",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        import secrets
        import string
        
        length = 12
        if ctx.args:
            try:
                length = min(max(int(ctx.args[0]), 8), 32)
            except ValueError:
                pass
        
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        return CommandResult(
            success=True,
            message=f"🔐 Generated password ({length} chars):\n`{password}`\n\n⚠️ Save this securely!"
        )


@command("uuid", description="Generate a UUID", aliases=["guid"], category="general")
class UUIDCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        import uuid
        return CommandResult(
            success=True,
            message=f"🆔 UUID:\n`{str(uuid.uuid4())}`"
        )


@command("length", description="Count characters in text", min_args=1, category="general")
class LengthCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str
        chars = len(text)
        words = len(text.split())
        lines = text.count('\n') + 1
        
        return CommandResult(
            success=True,
            message=f"📏 *Text Statistics:*\n• Characters: {chars}\n• Words: {words}\n• Lines: {lines}"
        )


@command("reverse", description="Reverse text", min_args=1, category="general")
class ReverseCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        reversed_text = ctx.args_str[::-1]
        return CommandResult(success=True, message=f"🔄 Reversed:\n{reversed_text}")


@command("upper", description="Convert text to uppercase", min_args=1, category="general")
class UpperCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(success=True, message=f"🔠 {ctx.args_str.upper()}")


@command("lower", description="Convert text to lowercase", min_args=1, category="general")
class LowerCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(success=True, message=f"🔡 {ctx.args_str.lower()}")


@command("capitalize", description="Capitalize text", min_args=1, category="general")
class CapitalizeCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(success=True, message=f"✨ {ctx.args_str.title()}")
