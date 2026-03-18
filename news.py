"""
News and information commands.
"""
import httpx

from commands.base import Command, CommandContext, CommandResult, command
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@command("news", description="Get latest news headlines", aliases=["n"], category="news")
class NewsCommand(Command):
    usage_examples = [
        "!news - Get top headlines",
        "!news technology - Get tech news",
        "!news business - Get business news",
    ]
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not settings.NEWS_API_KEY:
            return CommandResult(
                success=False,
                message="⚠️ News service is not configured."
            )
        
        category = ctx.args[0].lower() if ctx.args else "general"
        valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        
        if category not in valid_categories:
            category = "general"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={
                        "category": category,
                        "apiKey": settings.NEWS_API_KEY,
                        "pageSize": 5,
                        "language": "en",
                    },
                    timeout=10.0,
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data["status"] != "ok":
                    return CommandResult(
                        success=False,
                        message="❌ Failed to fetch news."
                    )
                
                articles = data["articles"]
                if not articles:
                    return CommandResult(
                        success=False,
                        message=f"❌ No news found for category: {category}"
                    )
                
                lines = [f"📰 *Top {category.title()} News*\n"]
                
                for i, article in enumerate(articles[:5], 1):
                    title = article["title"] or "No title"
                    source = article["source"]["name"] or "Unknown"
                    lines.append(f"{i}. *{title}*")
                    lines.append(f"   📎 {source}\n")
                
                return CommandResult(success=True, message="\n".join(lines))
                
        except httpx.HTTPError as e:
            logger.error("news_api_error", error=str(e))
            return CommandResult(
                success=False,
                message="❌ Failed to fetch news. Please try again later."
            )


@command("search", description="Search the web", min_args=1, category="news")
class SearchCommand(Command):
    usage_examples = [
        "!search python programming",
        "!search latest iphone",
    ]
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        query = ctx.args_str
        
        # Using DuckDuckGo instant answer API (free, no key required)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                    timeout=10.0,
                )
                
                # DuckDuckGo returns JavaScript, try alternative
                return CommandResult(
                    success=True,
                    message=f"🔍 Search query: *{query}*\n\nTry searching on:\n• Google: https://google.com/search?q={query.replace(' ', '+')}\n• DuckDuckGo: https://duckduckgo.com/?q={query.replace(' ', '+')}"
                )
                
        except httpx.HTTPError:
            return CommandResult(
                success=True,
                message=f"🔍 Search: *{query}*\n\n• https://google.com/search?q={query.replace(' ', '+')}"
            )


@command("wiki", description="Search Wikipedia", min_args=1, category="news")
class WikiCommand(Command):
    usage_examples = [
        "!wiki Python programming",
        "!wiki Albert Einstein",
    ]
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        query = ctx.args_str
        
        try:
            async with httpx.AsyncClient() as client:
                # Search for page
                search_response = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": 1,
                    },
                    timeout=10.0,
                )
                
                search_data = search_response.json()
                
                if not search_data["query"]["search"]:
                    return CommandResult(
                        success=False,
                        message=f"❌ No Wikipedia article found for: {query}"
                    )
                
                page_title = search_data["query"]["search"][0]["title"]
                snippet = search_data["query"]["search"][0]["snippet"]
                
                # Clean snippet
                snippet = snippet.replace("<span class=\"searchmatch\">", "*").replace("</span>", "*")
                
                url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                
                message = f"""
📚 *{page_title}*

{snippet}...

🔗 Read more: {url}
                """.strip()
                
                return CommandResult(success=True, message=message)
                
        except httpx.HTTPError as e:
            logger.error("wiki_api_error", error=str(e))
            return CommandResult(
                success=False,
                message="❌ Failed to search Wikipedia. Please try again later."
            )


@command("define", description="Get word definition", min_args=1, category="news")
class DefineCommand(Command):
    usage_examples = [
        "!define serendipity",
        "!define algorithm",
    ]
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        word = ctx.args[0].lower()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    return CommandResult(
                        success=False,
                        message=f"❌ No definition found for: {word}"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                entry = data[0]
                word_text = entry["word"]
                phonetic = entry.get("phonetic", "")
                
                lines = [f"📖 *{word_text.title()}* {phonetic}\n"]
                
                for meaning in entry["meanings"][:3]:
                    part_of_speech = meaning["partOfSpeech"]
                    lines.append(f"*{part_of_speech}:*")
                    
                    for i, definition in enumerate(meaning["definitions"][:2], 1):
                        lines.append(f"  {i}. {definition['definition']}")
                        if definition.get("example"):
                            lines.append(f'     _"{definition["example"]}"_')
                    lines.append("")
                
                return CommandResult(success=True, message="\n".join(lines))
                
        except httpx.HTTPError as e:
            logger.error("dictionary_api_error", error=str(e))
            return CommandResult(
                success=False,
                message="❌ Failed to get definition. Please try again later."
            )


@command("fact", description="Get a random fact", aliases=["facts"], category="news")
class FactCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        facts = [
            "🧠 Octopuses have three hearts and blue blood.",
            "🍌 Bananas are berries, but strawberries aren't.",
            "🐝 Honey never spoils. Archaeologists found 3000-year-old honey still edible!",
            "🦒 A giraffe's tongue is about 20 inches long and blue-black in color.",
            "🌌 There are more stars in the universe than grains of sand on Earth.",
            "🦘 Kangaroos can't walk backwards.",
            "🐘 Elephants are the only mammals that can't jump.",
            "🌙 The Moon is drifting away from Earth at about 1.6 inches per year.",
            "🦈 Sharks have been around longer than trees.",
            "⚡ A bolt of lightning is five times hotter than the surface of the sun.",
            "🐌 Some snails can sleep for up to three years.",
            "🦋 Butterflies taste with their feet.",
            "🐙 An octopus can squeeze through any hole larger than its beak.",
            "🌊 About 71% of Earth's surface is covered by water.",
            "🦅 Eagles can see up to 8 times farther than humans.",
        ]
        import random
        return CommandResult(success=True, message=random.choice(facts))


@command("quote", description="Get an inspirational quote", aliases=["q"], category="news")
class QuoteCommand(Command):
    cooldown_seconds = 3
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        quotes = [
            ('"The only way to do great work is to love what you do."', "Steve Jobs"),
            ('"Innovation distinguishes between a leader and a follower."', "Steve Jobs"),
            ('"Life is what happens when you\'re busy making other plans."', "John Lennon"),
            ('"The future belongs to those who believe in the beauty of their dreams."', "Eleanor Roosevelt"),
            ('"It is during our darkest moments that we must focus to see the light."', "Aristotle"),
            ('"The only impossible journey is the one you never begin."', "Tony Robbins"),
            ('"Success is not final, failure is not fatal: it is the courage to continue that counts."', "Winston Churchill"),
            ('"Believe you can and you\'re halfway there."', "Theodore Roosevelt"),
            ('"The best way to predict the future is to create it."', "Peter Drucker"),
            ('"Everything you\'ve ever wanted is on the other side of fear."', "George Addair"),
            ('"Hardships often prepare ordinary people for an extraordinary destiny."', "C.S. Lewis"),
            ('"Dream big and dare to fail."', "Norman Vaughan"),
            ('"It does not matter how slowly you go as long as you do not stop."', "Confucius"),
            ('"Everything has beauty, but not everyone can see."', "Confucius"),
            ('"The journey of a thousand miles begins with one step."', "Lao Tzu"),
        ]
        import random
        quote, author = random.choice(quotes)
        return CommandResult(success=True, message=f"💬 {quote}\n\n— {author}")


@command("joke", description="Get a random joke", aliases=["jokes"], category="news")
class JokeCommand(Command):
    cooldown_seconds = 3
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything! 😄",
            "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
            "Why don't eggs tell jokes? They'd crack each other up! 🥚",
            "What do you call a fake noodle? An impasta! 🍝",
            "Why did the math book look sad? Because it had too many problems! 📚",
            "What do you call a bear with no teeth? A gummy bear! 🐻",
            "Why did the cookie go to the doctor? Because it was feeling crumbly! 🍪",
            "What do you call a sleeping dinosaur? A dino-snore! 🦕",
            "Why can't you give Elsa a balloon? Because she'll let it go! ❄️",
            "What do you call a boomerang that doesn't come back? A stick! 🪃",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one! ⛳",
            "What do you call a fish with no eyes? Fsh! 🐟",
            "Why did the picture go to jail? Because it was framed! 🖼️",
            "What do you call a can opener that doesn't work? A can't opener! 🥫",
            "Why did the bicycle fall over? Because it was two tired! 🚲",
        ]
        import random
        return CommandResult(success=True, message=random.choice(jokes))
