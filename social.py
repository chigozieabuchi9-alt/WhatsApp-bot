"""
Social media and productivity commands.
"""
import random
import urllib.parse

from commands.base import Command, CommandContext, CommandResult, command


@command("social", description="Get social media links and tools", category="social")
class SocialCommand(Command):
    """Social media utilities."""
    usage_examples = [
        "!social instagram username - Get Instagram link",
        "!social tiktok @user - Get TikTok link",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult(
                success=True,
                message="""
📱 *Social Media Tools*

Usage: !social <platform> <username>

Platforms:
• instagram <user> - Instagram profile
• twitter/x <user> - Twitter/X profile
• tiktok <user> - TikTok profile
• youtube <channel> - YouTube channel
• github <user> - GitHub profile
• linkedin <name> - LinkedIn search
• reddit <user> - Reddit profile
• twitch <user> - Twitch channel

Example: !social instagram nasa
                """.strip()
            )
        
        platform = ctx.args[0].lower()
        username = ctx.args[1]
        
        urls = {
            "instagram": f"https://instagram.com/{username}",
            "ig": f"https://instagram.com/{username}",
            "twitter": f"https://twitter.com/{username}",
            "x": f"https://x.com/{username}",
            "tiktok": f"https://tiktok.com/@{username}",
            "youtube": f"https://youtube.com/@{username}",
            "yt": f"https://youtube.com/@{username}",
            "github": f"https://github.com/{username}",
            "gh": f"https://github.com/{username}",
            "linkedin": f"https://linkedin.com/in/{username}",
            "reddit": f"https://reddit.com/u/{username}",
            "twitch": f"https://twitch.tv/{username}",
            "facebook": f"https://facebook.com/{username}",
            "fb": f"https://facebook.com/{username}",
        }
        
        url = urls.get(platform)
        if url:
            return CommandResult(
                success=True,
                message=f"🔗 *{platform.title()} Profile*\n\n{url}"
            )
        else:
            return CommandResult(
                success=False,
                message=f"❌ Unknown platform: {platform}"
            )


@command("downloader", description="Download from social media", aliases=["dl"], category="social")
class DownloaderCommand(Command):
    """Social media downloaders."""
    usage_examples = [
        "!dl youtube https://youtube.com/watch?v=...",
        "!dl tiktok https://tiktok.com/@user/video/...",
        "!dl instagram https://instagram.com/p/...",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 15
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult(
                success=True,
                message="""
⬇️ *Social Media Downloader*

Usage: !dl <platform> <url>

Platforms:
• youtube/yt - YouTube videos
• tiktok/tt - TikTok videos
• instagram/ig - Instagram posts
• twitter/x - Twitter videos
• facebook/fb - Facebook videos
• reddit - Reddit videos
• soundcloud/sc - SoundCloud tracks
• spotify - Spotify songs (metadata)

Example: !dl youtube https://youtube.com/watch?v=dQw4w9WgXcQ

⚠️ Respect copyright and terms of service!
                """.strip()
            )
        
        platform = ctx.args[0].lower()
        url = " ".join(ctx.args[1:])
        
        downloaders = {
            "youtube": [
                "https://y2mate.is",
                "https://yt1s.com",
                "https://savefrom.net",
            ],
            "yt": [
                "https://y2mate.is",
                "https://yt1s.com",
            ],
            "tiktok": [
                "https://ssstik.io",
                "https://snaptik.app",
                "https://tiktokdownloader.io",
            ],
            "tt": [
                "https://ssstik.io",
                "https://snaptik.app",
            ],
            "instagram": [
                "https://snapinsta.app",
                "https://instadownloader.co",
                "https://saveinsta.app",
            ],
            "ig": [
                "https://snapinsta.app",
                "https://instadownloader.co",
            ],
            "twitter": [
                "https://ssstwitter.com",
                "https://twittervideodownloader.com",
            ],
            "x": [
                "https://ssstwitter.com",
                "https://twittervideodownloader.com",
            ],
            "facebook": [
                "https://fdown.net",
                "https://fbdownloader.net",
            ],
            "fb": [
                "https://fdown.net",
                "https://fbdownloader.net",
            ],
            "reddit": [
                "https://redditsave.com",
                "https://viddit.red",
            ],
            "soundcloud": [
                "https://sclouddownloader.net",
                "https://soundcloudmp3.org",
            ],
            "spotify": [
                "https://spotifydown.com",
                "Note: Downloads metadata only",
            ],
        }
        
        services = downloaders.get(platform)
        if services:
            return CommandResult(
                success=True,
                message=f"""
⬇️ *{platform.title()} Downloader*

URL: {url}

Download services:
{chr(10).join(f"• {s}" for s in services)}

⚠️ Respect copyright!
Only download content you have permission to use.
                """.strip()
            )
        else:
            return CommandResult(
                success=False,
                message=f"❌ Unknown platform: {platform}"
            )


@command("trending", description="Get trending topics", category="social")
class TrendingCommand(Command):
    """Get trending topics from various platforms."""
    usage_examples = [
        "!trending twitter - Twitter trends",
        "!trending youtube - YouTube trending",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        platform = ctx.args[0].lower() if ctx.args else "twitter"
        
        trends = {
            "twitter": {
                "url": "https://twitter.com/explore/tabs/trending",
                "alternatives": [
                    "https://trends.google.com/trends/trendingsearches/daily",
                    "https://getdaytrends.com",
                ],
            },
            "x": {
                "url": "https://x.com/explore/tabs/trending",
                "alternatives": [],
            },
            "youtube": {
                "url": "https://youtube.com/feed/trending",
                "alternatives": [
                    "https://trends.google.com/youtube",
                ],
            },
            "yt": {
                "url": "https://youtube.com/feed/trending",
                "alternatives": [],
            },
            "google": {
                "url": "https://trends.google.com/trending",
                "alternatives": [],
            },
            "tiktok": {
                "url": "https://tiktok.com/discover",
                "alternatives": [
                    "https://tiktokhashtags.com",
                ],
            },
            "reddit": {
                "url": "https://reddit.com/r/popular",
                "alternatives": [
                    "https://reddit.com/r/all",
                ],
            },
        }
        
        trend_info = trends.get(platform)
        if trend_info:
            alts = "\n".join(f"• {a}" for a in trend_info["alternatives"]) if trend_info["alternatives"] else ""
            
            return CommandResult(
                success=True,
                message=f"""
🔥 *{platform.title()} Trending*

{trend_info['url']}

{alts}

Stay up to date with what's happening!
                """.strip()
            )
        else:
            return CommandResult(
                success=False,
                message=f"❌ Unknown platform: {platform}"
            )


@command("profile", description="Generate social media bio", min_args=1, category="social")
class ProfileCommand(Command):
    """Generate social media bios."""
    usage_examples = [
        "!profile developer - Developer bio",
        "!profile funny - Funny bio",
        "!profile professional - Professional bio",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        style = ctx.args[0].lower() if ctx.args else "general"
        
        bios = {
            "developer": [
                "💻 Turning coffee into code since 2010",
                "🚀 Building the future, one bug at a time",
                "⚡ Full-stack developer | Open source enthusiast",
                "🐛 Professional bug creator and fixer",
                "📱 Mobile developer | iOS & Android",
            ],
            "funny": [
                "Professional overthinker 🧠",
                "Currently pretending to be an adult 👔",
                "My life is a work of fiction 📚",
                "Professional nap taker 😴",
                "I put the 'pro' in procrastination",
            ],
            "professional": [
                "Helping businesses grow through innovation",
                "Results-driven professional | Team leader",
                "Passionate about creating value",
                "Strategic thinker | Problem solver",
                "Connecting people and opportunities",
            ],
            "creative": [
                "🎨 Creating art that speaks",
                "✨ Turning imagination into reality",
                "📸 Capturing moments that matter",
                "🎵 Music is my therapy",
                "🎬 Storyteller through visuals",
            ],
            "minimal": [
                "Less is more",
                "Living simply",
                "Here for a good time",
                "Just vibing ✌️",
                "Keep it simple",
            ],
        }
        
        style_bios = bios.get(style, bios["minimal"])
        bio = random.choice(style_bios)
        
        return CommandResult(
            success=True,
            message=f"""
✨ *{style.title()} Bio*

{bio}

Copy and use on your profiles!
Instagram, Twitter, TikTok, LinkedIn...
            """.strip()
        )


@command("hashtag", description="Generate trending hashtags", min_args=1, category="social")
class HashtagCommand(Command):
    """Generate hashtags for posts."""
    usage_examples = [
        "!hashtag travel - Travel hashtags",
        "!hashtag food 5 - Get 5 food hashtags",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        category = ctx.args[0].lower()
        count = 10
        
        if len(ctx.args) > 1:
            try:
                count = min(int(ctx.args[1]), 30)
            except ValueError:
                pass
        
        hashtags_db = {
            "travel": ["#travel", "#wanderlust", "#adventure", "#explore", "#vacation", "#trip", "#travelgram", "#instatravel", "#travelphotography", "#backpacking"],
            "food": ["#food", "#foodie", "#foodporn", "#instafood", "#yummy", "#delicious", "#foodphotography", "#homemade", "#cooking", "#foodstagram"],
            "fitness": ["#fitness", "#gym", "#workout", "#fit", "#bodybuilding", "#training", "#health", "#fitfam", "#lifestyle", "#muscle"],
            "fashion": ["#fashion", "#style", "#ootd", "#instafashion", "#fashionblogger", "#outfit", "#streetstyle", "#fashionista", "#lookbook", "#trendy"],
            "photography": ["#photography", "#photo", "#photooftheday", "#photographer", "#picoftheday", "#instagood", "#camera", "#art", "#portrait", "#nature"],
            "love": ["#love", "#couple", "#relationship", "#romance", "#together", "#happy", "#smile", "#instalove", "#couplegoals", "#bae"],
            "motivation": ["#motivation", "#inspiration", "#success", "#goals", "#mindset", "#hustle", "#grind", "#dreambig", "#nevergiveup", "#believe"],
            "tech": ["#tech", "#technology", "#innovation", "#coding", "#programming", "#developer", "#software", "#ai", "#gadgets", "#startup"],
            "gaming": ["#gaming", "#gamer", "#videogames", "#game", "#playstation", "#xbox", "#nintendo", "#twitch", "#streamer", "#esports"],
            "music": ["#music", "#song", "#musician", "#artist", "#hiphop", "#rap", "#pop", "#rock", "#concert", "#spotify"],
            "business": ["#business", "#entrepreneur", "#marketing", "#success", "#smallbusiness", "#branding", "#digitalmarketing", "#leadership", "#money", "#investment"],
            "nature": ["#nature", "#landscape", "#sunset", "#sky", "#mountains", "#ocean", "#forest", "#wildlife", "#flowers", "#earth"],
        }
        
        tags = hashtags_db.get(category, ["#instagood", "#photooftheday", "#beautiful", "#happy", "#picoftheday"])
        selected = random.sample(tags, min(count, len(tags)))
        
        return CommandResult(
            success=True,
            message=f"""
🏷️ *Hashtags for #{category}*

{' '.join(selected)}

Copy and paste into your post!

Find more at:
• https://displaypurposes.com
• https://all-hashtag.com
            """.strip()
        )


@command("linktree", description="Create a simple link page", min_args=1, category="social")
class LinkTreeCommand(Command):
    """Create a linktree-style page."""
    usage_examples = [
        "!linktree instagram.com/user twitter.com/user",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        links = ctx.args
        
        link_list = "\n".join(f"• {link}" for link in links)
        
        return CommandResult(
            success=True,
            message=f"""
🔗 *Your Link Page*

{link_list}

Create a professional link page:
• https://linktr.ee (most popular)
• https://carrd.co
• https://bio.link
• https://taplink.at

These let you share multiple links with one URL!
            """.strip()
        )


@command("analytics", description="Social media analytics tools", category="social")
class AnalyticsCommand(Command):
    """Social media analytics."""
    usage_examples = [
        "!analytics instagram - Instagram analytics tools",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        platform = ctx.args[0].lower() if ctx.args else "general"
        
        tools = {
            "instagram": [
                "https://iconosquare.com",
                "https://socialblade.com/instagram",
                "https://phlanx.com/engagement-calculator",
            ],
            "twitter": [
                "https://analytics.twitter.com",
                "https://socialblade.com/twitter",
                "https://tweetreach.com",
            ],
            "youtube": [
                "https://studio.youtube.com",
                "https://socialblade.com/youtube",
                "https://vidIQ.com",
                "https://tubebuddy.com",
            ],
            "tiktok": [
                "https://analytics.tiktok.com",
                "https://socialblade.com/tiktok",
                "https://exolyt.com",
            ],
            "general": [
                "https://hootsuite.com",
                "https://buffer.com",
                "https://sproutsocial.com",
                "https://later.com",
            ],
        }
        
        platform_tools = tools.get(platform, tools["general"])
        
        return CommandResult(
            success=True,
            message=f"""
📊 *{platform.title()} Analytics Tools*

{chr(10).join(f"• {t}" for t in platform_tools)}

Track your:
• Follower growth
• Engagement rates
• Best posting times
• Content performance
• Audience demographics
            """.strip()
        )


@command("schedule", description="Best times to post", category="social")
class ScheduleCommand(Command):
    """Best posting times for social media."""
    usage_examples = [
        "!schedule instagram - Best Instagram posting times",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        platform = ctx.args[0].lower() if ctx.args else "general"
        
        best_times = {
            "instagram": {
                "best": "Tuesday 11 AM - 2 PM, Monday-Friday 11 AM",
                "good": "Weekdays 10 AM - 3 PM",
                "avoid": "Late night and early morning",
            },
            "facebook": {
                "best": "Tuesday-Thursday 8 AM - 12 PM",
                "good": "Weekdays 9 AM - 3 PM",
                "avoid": "Weekends and late nights",
            },
            "twitter": {
                "best": "Tuesday-Thursday 9 AM",
                "good": "Weekdays 8 AM - 4 PM",
                "avoid": "Friday evenings",
            },
            "linkedin": {
                "best": "Tuesday-Thursday 8-10 AM",
                "good": "Tuesday & Wednesday 8 AM - 2 PM",
                "avoid": "Weekends",
            },
            "tiktok": {
                "best": "Tuesday 9 AM, Thursday 12 PM, Friday 5 AM",
                "good": "Tuesday-Friday 7-11 AM",
                "avoid": "Late night",
            },
            "youtube": {
                "best": "Thursday-Friday 2-4 PM",
                "good": "Weekdays 2-6 PM",
                "avoid": "Early mornings",
            },
        }
        
        times = best_times.get(platform, {
            "best": "Tuesday-Thursday 9-11 AM",
            "good": "Weekdays 9 AM - 3 PM",
            "avoid": "Late nights and weekends",
        })
        
        return CommandResult(
            success=True,
            message=f"""
⏰ *Best Times to Post on {platform.title()}*

🟢 *Best:* {times['best']}
🟡 *Good:* {times['good']}
🔴 *Avoid:* {times['avoid']}

💡 Tips:
• Post consistently
• Engage with comments quickly
• Use relevant hashtags
• Post when YOUR audience is active

Use scheduling tools:
• https://later.com
• https://buffer.com
• https://hootsuite.com
            """.strip()
        )


@command("viral", description="Viral content ideas", category="social")
class ViralCommand(Command):
    """Get viral content ideas."""
    usage_examples = [
        "!viral tiktok - TikTok viral ideas",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        platform = ctx.args[0].lower() if ctx.args else "general"
        
        ideas = {
            "tiktok": [
                "Day in the life videos",
                "Before & after transformations",
                "Quick tutorials/hacks",
                "Reacting to trends",
                "POV videos",
                "Behind the scenes",
                "Storytime videos",
                "Duet with popular videos",
            ],
            "instagram": [
                "Carousel educational posts",
                "Reels with trending audio",
                "User-generated content",
                "Behind-the-scenes Stories",
                "Before/after posts",
                "Memes related to niche",
                "Inspirational quotes",
                "Product demonstrations",
            ],
            "youtube": [
                "How-to tutorials",
                "List videos (Top 10)",
                "Reaction videos",
                "Challenge videos",
                "Product reviews",
                "Day in the life",
                "Myth busting",
                "Collaboration videos",
            ],
            "twitter": [
                "Hot takes on trending topics",
                "Thread storytelling",
                "Memes and humor",
                "Polls and questions",
                "Breaking news commentary",
                "Educational threads",
                "Relatable observations",
            ],
        }
        
        platform_ideas = ideas.get(platform, ideas["tiktok"])
        selected = random.sample(platform_ideas, min(5, len(platform_ideas)))
        
        return CommandResult(
            success=True,
            message=f"""
🔥 *Viral Content Ideas for {platform.title()}*

{chr(10).join(f"{i+1}. {idea}" for i, idea in enumerate(selected))}

💡 Remember:
• Hook viewers in first 3 seconds
• Use trending sounds/hashtags
• Post consistently
• Engage with your audience
• Quality over quantity
            """.strip()
        )
