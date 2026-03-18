"""
Fun and entertainment commands.
"""
import random

from commands.base import Command, CommandContext, CommandResult, command


@command("meme", description="Get a random meme", category="fun")
class MemeCommand(Command):
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        # Return popular meme URLs
        memes = [
            "https://i.imgflip.com/30b1gx.jpg",  # Drake
            "https://i.imgflip.com/1bij.jpg",     # One Does Not Simply
            "https://i.imgflip.com/4t0m5.jpg",    # Roll Safe
            "https://i.imgflip.com/26am.jpg",     # Y U No
            "https://i.imgflip.com/1otk96.jpg",   # Woman Yelling at Cat
            "https://i.imgflip.com/3lmzyx.jpg",   # UNO Draw 25
            "https://i.imgflip.com/1ur9b0.jpg",   # Buff Doge vs Cheems
            "https://i.imgflip.com/24y43o.jpg",   # Disaster Girl
        ]
        
        meme = random.choice(memes)
        return CommandResult(
            success=True,
            message=f"😂 *Random Meme*\n\n{meme}"
        )


@command("compliment", description="Get a compliment", category="fun")
class ComplimentCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        compliments = [
            "You're an awesome friend! 🌟",
            "You have a great sense of humor! 😄",
            "You're more helpful than you realize! 🤝",
            "You have the best laugh! 😆",
            "You're a true gift to those around you! 🎁",
            "You light up the room! 💡",
            "You have a great perspective on things! 👀",
            "You're a smart cookie! 🍪",
            "You are making a difference! 🌍",
            "You have the best ideas! 💡",
            "You're a ray of sunshine! ☀️",
            "You're more fun than bubble wrap! 🎈",
            "You're like a breath of fresh air! 🌬️",
            "You're one of a kind! 🦄",
            "You're doing great! Keep it up! 🚀",
        ]
        
        return CommandResult(
            success=True,
            message=random.choice(compliments)
        )


@command("insult", description="Get a playful insult", category="fun")
class InsultCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        insults = [
            "You're not stupid; you just have bad luck thinking. 🤔",
            "I'd agree with you but then we'd both be wrong. 🤷",
            "You're not dumb, you just have bad luck when it comes to thinking. 🧠",
            "I'm not saying you're stupid, I'm just saying you have bad luck when it comes to thinking. 💭",
            "You're like a cloud. When you disappear, it's a beautiful day. ☁️",
            "I'm not insulting you, I'm describing you. 📝",
            "You're not the dumbest person in the world, but you'd better hope they don't die. 😅",
            "I'd explain it to you, but I left my crayons at home. 🖍️",
            "You're not stupid, you just have bad luck when it comes to thinking. 🎲",
            "I'm not saying you're dumb, you just have bad luck when it comes to thinking. 🍀",
        ]
        
        return CommandResult(
            success=True,
            message=random.choice(insults)
        )


@command("roast", description="Roast someone", min_args=1, category="fun")
class RoastCommand(Command):
    usage_examples = [
        "!roast @friend",
        "!roast myself",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        target = ctx.args_str
        
        roasts = [
            f"{target}, you're like a software update. Whenever I see you, I think 'Not now'. 📱",
            f"{target}, you're the reason the gene pool needs a lifeguard. 🏊",
            f"{target}, I'm jealous of people who don't know you. 😎",
            f"{target}, you bring everyone so much joy... when you leave the room. 🚪",
            f"{target}, you're not the sharpest tool in the shed, but you're definitely a tool. 🔧",
            f"{target}, I'd roast you, but my mom said I'm not allowed to burn trash. 🗑️",
            f"{target}, you're like a slinky - not really good for much, but bring a smile when falling down stairs. 🎢",
            f"{target}, you're proof that evolution can go in reverse. 🐒",
            f"{target}, you're not stupid; you just have bad luck thinking. 🎲",
            f"{target}, I'd agree with you but then we'd both be wrong. 🤷",
        ]
        
        return CommandResult(
            success=True,
            message=random.choice(roasts)
        )


@command("showerthought", description="Get a shower thought", category="fun")
class ShowerThoughtCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        thoughts = [
            "Maybe plants are really farming us, giving us oxygen until we eventually expire and turn into mulch. 🌱",
            "The first person to fall asleep was probably like 'What happened?' when they woke up. 😴",
            "Your first birthday is technically your second birthday. 🎂",
            "Theme parks can snap a crystal-clear picture of you on a roller coaster at 70mph, but bank cameras still can't get a clear shot of a robber standing still. 🎢",
            "If my calculator had a history, it would be more embarrassing than my browser history. 🧮",
            "Lawyers hope you get sued, doctors hope you get sick, cops hope you're a criminal, mechanics hope you have car trouble. Only thieves wish you prosperity. 💰",
            "As a kid, you don't realize you're also watching your parents grow up. 👨‍👩‍👧",
            "Tall people are expected to use their reach to help short people, but if a tall person were to ask a short person to hand them something they dropped on the floor, it would be insulting. 📏",
            "What if Earth is like one of those uncontacted tribes in South America, and the aliens are just waiting for us to develop the right technology before they talk to us? 👽",
            "Every time a character dies on a TV show, it just reminds us that we're watching people at work. 🎬",
        ]
        
        return CommandResult(
            success=True,
            message=f"🚿 *Shower Thought*\n\n{random.choice(thoughts)}"
        )


@command("wouldyourather", description="Would you rather question", aliases=["wyr"], category="fun")
class WYRCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        questions = [
            "Would you rather be able to fly or be invisible? 🦅👻",
            "Would you rather be the richest person in the world or the smartest? 💰🧠",
            "Would you rather never use social media again or never watch TV/movies again? 📱📺",
            "Would you rather have the ability to read minds or the ability to see the future? 🧠🔮",
            "Would you rather be famous but poor or rich but unknown? ⭐💰",
            "Would you rather live without music or without movies? 🎵🎬",
            "Would you rather have unlimited free food or unlimited free travel? 🍕✈️",
            "Would you rather be able to speak all languages or play all instruments? 🗣️🎸",
            "Would you rather never have to sleep or never have to eat? 😴🍽️",
            "Would you rather be the best player on a losing team or the worst player on a winning team? 🏆",
            "Would you rather have a rewind button or a pause button for your life? ⏪⏸️",
            "Would you rather always be 10 minutes late or always be 20 minutes early? ⏰",
            "Would you rather lose your sense of taste or your sense of smell? 👅👃",
            "Would you rather have super strength or super speed? 💪⚡",
            "Would you rather live in the past or the future? ⏳🔮",
        ]
        
        return CommandResult(
            success=True,
            message=f"🤔 *Would You Rather?*\n\n{random.choice(questions)}"
        )


@command("truthordare", description="Truth or dare", aliases=["tod"], category="fun")
class TruthOrDareCommand(Command):
    usage_examples = [
        "!truthordare truth",
        "!truthordare dare",
    ]
    
    truths = [
        "What's the most embarrassing thing you've done? 😳",
        "What's your biggest fear? 😨",
        "What's the last lie you told? 🤥",
        "What's your biggest regret? 😔",
        "What's the worst thing you've ever done? 😈",
        "What's your deepest secret? 🤫",
        "What's the craziest thing you've done? 🤪",
        "What's your worst habit? 🚬",
        "What's the most illegal thing you've done? 🚔",
        "What's your guilty pleasure? 🍫",
    ]
    
    dares = [
        "Send a funny selfie! 📸",
        "Tell a joke in the group! 😄",
        "Do your best dance move! 💃",
        "Sing a song for 10 seconds! 🎤",
        "Send your last photo! 📷",
        "Text your crush something random! 💬",
        "Change your profile picture to something silly! 🎭",
        "Send a voice message saying 'I love broccoli'! 🥦",
        "Type with your eyes closed for the next message! 👀",
        "Send a message using only emojis! 😀🎉🌟",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.args:
            return CommandResult(
                success=False,
                message="❌ Usage: !truthordare truth|dare"
            )
        
        choice = ctx.args[0].lower()
        
        if choice == "truth":
            return CommandResult(
                success=True,
                message=f"🎯 *TRUTH*\n\n{random.choice(self.truths)}"
            )
        elif choice == "dare":
            return CommandResult(
                success=True,
                message=f"🎯 *DARE*\n\n{random.choice(self.dares)}"
            )
        else:
            return CommandResult(
                success=False,
                message="❌ Choose 'truth' or 'dare'"
            )


@command("fortune", description="Get your fortune", category="fun")
class FortuneCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        fortunes = [
            "🥠 A pleasant surprise is waiting for you.",
            "🥠 Your creativity is your greatest asset.",
            "🥠 Good news will come to you by mail.",
            "🥠 Someone is thinking of you right now.",
            "🥠 A journey of a thousand miles begins with a single step.",
            "🥠 Your hard work will soon pay off.",
            "🥠 An exciting opportunity lies ahead.",
            "🥠 Trust your intuition; it will lead you well.",
            "🥠 A friend asks only for your time, not your money.",
            "🥠 You will have a pleasant surprise today.",
            "🥠 Luck is coming your way! 🍀",
            "🥠 A new turn of events will soon come about.",
            "🥠 Your ability for accomplishment will follow with success.",
            "🥠 Fortune favors the brave.",
            "🥠 Good things come to those who wait.",
        ]
        
        return CommandResult(
            success=True,
            message=random.choice(fortunes)
        )


@command("ascii", description="Convert text to ASCII art", min_args=1, category="fun")
class ASCIICommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str[:10]  # Limit to 10 chars
        
        # Simple ASCII representation
        ascii_art = f"""
```
╔{'═' * (len(text) + 2)}╗
║ {text.upper()} ║
╚{'═' * (len(text) + 2)}╝
```
        """.strip()
        
        return CommandResult(success=True, message=ascii_art)


@command("emojify", description="Convert text to emoji letters", min_args=1, category="fun")
class EmojifyCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str.lower()[:20]  # Limit to 20 chars
        
        emoji_map = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪',
            'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
            'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴',
            'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
            'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾',
            'z': '🇿', ' ': '  ',
        }
        
        result = ''.join(emoji_map.get(c, c) for c in text)
        return CommandResult(success=True, message=result)


@command("ship", description="Ship two people", min_args=2, category="fun")
class ShipCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        person1 = ctx.args[0]
        person2 = ctx.args[1]
        
        # Generate consistent compatibility
        seed = sum(ord(c) for c in person1 + person2)
        random.seed(seed)
        compatibility = random.randint(0, 100)
        random.seed()  # Reset seed
        
        if compatibility >= 90:
            emoji = "💕"
            text = "True love!"
        elif compatibility >= 70:
            emoji = "❤️"
            text = "Great match!"
        elif compatibility >= 50:
            emoji = "💛"
            text = "Could work!"
        elif compatibility >= 30:
            emoji = "💔"
            text = "It's complicated..."
        else:
            emoji = "☠️"
            text = "Run away!"
        
        bar = "█" * (compatibility // 10) + "░" * (10 - compatibility // 10)
        
        return CommandResult(
            success=True,
            message=f"💘 *Shipping {person1} × {person2}*\n\nCompatibility: {bar} {compatibility}%\n{emoji} {text}"
        )


@command("rate", description="Rate something", min_args=1, category="fun")
class RateCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        thing = ctx.args_str
        
        # Generate consistent rating
        seed = sum(ord(c) for c in thing)
        random.seed(seed)
        rating = random.randint(1, 10)
        random.seed()
        
        stars = "⭐" * rating + "☆" * (10 - rating)
        
        return CommandResult(
            success=True,
            message=f"📊 *Rating: {thing}*\n\n{stars}\n\nI give it a {rating}/10!"
        )


@command("howgay", description="How gay are you?", category="fun")
class HowGayCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        target = ctx.args_str if ctx.args else "you"
        
        # Generate consistent percentage
        seed = sum(ord(c) for c in target)
        random.seed(seed)
        percentage = random.randint(0, 100)
        random.seed()
        
        bar = "🏳️‍🌈" * (percentage // 20) + "◽" * (5 - percentage // 20)
        
        return CommandResult(
            success=True,
            message=f"🏳️‍🌈 *How gay is {target}?*\n\n{bar} {percentage}%"
        )


@command("pp", description="PP size checker", category="fun")
class PPCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        target = ctx.args_str if ctx.args else "you"
        
        # Generate consistent size
        seed = sum(ord(c) for c in target)
        random.seed(seed)
        size = random.randint(1, 12)
        random.seed()
        
        pp = "8" + "=" * size + "D"
        
        return CommandResult(
            success=True,
            message=f"📏 *PP Size for {target}*\n\n{pp}\n\n{size} inches!"
        )
