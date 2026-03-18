"""
AI-powered commands and integrations.
"""
import json
import random
import urllib.parse

import httpx

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier


@command("ai", description="Chat with AI assistant", min_args=1, category="ai")
class AIChatCommand(Command):
    """AI chat interface."""
    usage_examples = [
        "!ai What is Python?",
        "!ai Write a poem about coding",
        "!ai Explain quantum computing simply",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        prompt = ctx.args_str
        
        # Since we don't have actual API keys, provide helpful responses
        # In production, this would call OpenAI, Claude, etc.
        
        responses = {
            "hello": "Hello! 👋 I'm your AI assistant. How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "help": "I can help with:\n• Answering questions\n• Writing content\n• Explaining concepts\n• Code help\n• And more!",
            "python": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's great for beginners and used in web dev, data science, AI, and more! 🐍",
            "coding": "Coding is the process of writing instructions for computers. It's like learning a new language that computers understand! 💻",
            "ai": "AI (Artificial Intelligence) is technology that enables machines to learn from data and perform tasks that typically require human intelligence. 🤖",
        }
        
        prompt_lower = prompt.lower()
        
        # Check for exact matches
        for key, response in responses.items():
            if key in prompt_lower:
                return CommandResult(
                    success=True,
                    message=f"🤖 *AI Response*\n\n{response}\n\n_This is a demo response. Add OpenAI API key for full functionality._"
                )
        
        # Generic response
        return CommandResult(
            success=True,
            message=f"""
🤖 *AI Response*

You asked: "{prompt}"

To enable full AI responses, add your OpenAI API key to the environment variables:
```
OPENAI_API_KEY=your-key-here
```

Then I can provide intelligent responses using GPT-4!

_Free alternatives:_
• https://chat.openai.com
• https://claude.ai
• https://bard.google.com
            """.strip()
        )


@command("image", description="Generate AI images", min_args=1, category="ai")
class ImageGenCommand(Command):
    """AI image generation."""
    usage_examples = [
        "!image a cat wearing sunglasses",
        "!image futuristic city at night",
    ]
    required_tier = UserTier.PREMIUM
    cooldown_seconds = 30
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        prompt = ctx.args_str
        
        encoded_prompt = urllib.parse.quote(prompt)
        
        return CommandResult(
            success=True,
            message=f"""
🎨 *AI Image Generation*

Prompt: "{prompt}"

Free AI image generators:
• https://www.bing.com/create (DALL-E 3)
• https://leonardo.ai
• https://playgroundai.com
• https://clipdrop.co/stable-diffusion

Search for existing images:
• https://lexica.art/?q={encoded_prompt}

_Add OPENAI_API_KEY for direct generation!_
            """.strip()
        )


@command("summarize", description="Summarize long text", min_args=1, category="ai")
class SummarizeCommand(Command):
    """Text summarization."""
    usage_examples = [
        "!summarize <paste long text>",
        "!summarize https://example.com/article",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        text = ctx.args_str
        
        # Check if it's a URL
        if text.startswith(("http://", "https://")):
            return CommandResult(
                success=True,
                message=f"""
📄 *Article Summarizer*

URL: {text}

Summarization tools:
• https://smmry.com
• https://www.summarizebot.com
• https://chrome.google.com/webstore/detail/glarity-summary-for-googl/cmnlolelipjlhfkhpohphpedmkfbobjc

Or use the TLDR bot on Telegram!
                """.strip()
            )
        
        # If text is short, just return it
        if len(text) < 200:
            return CommandResult(
                success=False,
                message="❌ Text too short to summarize (min 200 characters)"
            )
        
        # Simple extractive summarization (first and last sentences)
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) >= 3:
            summary = f"{sentences[0]}. ... {sentences[-1]}."
        else:
            summary = text[:200] + "..."
        
        return CommandResult(
            success=True,
            message=f"""
📝 *Summary*

Original length: {len(text)} characters
Summary length: {len(summary)} characters

*{summary}*

_For better summaries, use:_
• https://smmry.com
• https://quillbot.com/summarize
            """.strip()
        )


@command("translate", description="Translate text to any language", min_args=2, category="ai")
class TranslateCommand(Command):
    """Language translation."""
    usage_examples = [
        "!translate es Hello World - Translate to Spanish",
        "!translate ja How are you - Translate to Japanese",
        "!translate auto fr text - Auto-detect to French",
    ]
    required_tier = UserTier.USER
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        lang = ctx.args[0].lower()
        text = " ".join(ctx.args[1:])
        
        # Language codes
        languages = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
            "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi",
            "tr": "Turkish", "pl": "Polish", "nl": "Dutch", "sv": "Swedish",
            "auto": "Auto-detect",
        }
        
        lang_name = languages.get(lang, lang)
        encoded_text = urllib.parse.quote(text)
        
        return CommandResult(
            success=True,
            message=f"""
🌐 *Translation*

From: Auto-detect
To: {lang_name}
Text: "{text}"

Google Translate:
https://translate.google.com/?sl=auto&tl={lang}&text={encoded_text}

DeepL (better quality):
https://www.deepl.com/translator#en/{lang}/{encoded_text}

_Add GOOGLE_TRANSLATE_API_KEY for direct translation!_
            """.strip()
        )


@command("code", description="Get code help and examples", min_args=1, category="ai")
class CodeCommand(Command):
    """Programming help."""
    usage_examples = [
        "!code python hello world",
        "!code javascript fetch api",
        "!code sql select query",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        query = ctx.args_str.lower()
        
        # Code snippets database
        snippets = {
            "python hello": """
```python
# Hello World in Python
print("Hello, World!")

# Or with a function
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```
            """,
            "python read file": """
```python
# Read a file in Python
# Method 1: Using with statement (recommended)
with open('file.txt', 'r') as f:
    content = f.read()

# Method 2: Read lines
with open('file.txt', 'r') as f:
    lines = f.readlines()

# Method 3: Read line by line
with open('file.txt', 'r') as f:
    for line in f:
        print(line.strip())
```
            """,
            "javascript fetch": """
```javascript
// Fetch API example
fetch('https://api.example.com/data')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));

// Async/await version
async function getData() {
    try {
        const response = await fetch('https://api.example.com/data');
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}
```
            """,
            "sql select": """
```sql
-- Basic SELECT query
SELECT * FROM users;

-- SELECT with conditions
SELECT name, email FROM users WHERE age > 18;

-- SELECT with JOIN
SELECT u.name, o.order_date
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
```
            """,
            "python list": """
```python
# Python list operations
my_list = [1, 2, 3, 4, 5]

# Add element
my_list.append(6)

# Remove element
my_list.remove(3)

# List comprehension
squares = [x**2 for x in my_list]

# Filter
evens = [x for x in my_list if x % 2 == 0]

# Sort
my_list.sort(reverse=True)
```
            """,
            "python dict": """
```python
# Python dictionary operations
my_dict = {"name": "John", "age": 30}

# Access value
print(my_dict["name"])

# Add/update
my_dict["city"] = "New York"

# Safe access
age = my_dict.get("age", 0)

# Iterate
for key, value in my_dict.items():
    print(f"{key}: {value}")

# Dictionary comprehension
squares = {x: x**2 for x in range(5)}
```
            """,
            "python function": """
```python
# Python function examples

def greet(name, greeting="Hello"):
    """Greet a person."""
    return f"{greeting}, {name}!"

# Lambda function
square = lambda x: x ** 2

# Function with *args
def sum_all(*args):
    return sum(args)

# Function with **kwargs
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

# Decorator
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Time: {time.time() - start}")
        return result
    return wrapper
```
            """,
            "python class": """
```python
# Python class example

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hi, I'm {self.name}"
    
    @property
    def is_adult(self):
        return self.age >= 18

# Inheritance
class Employee(Person):
    def __init__(self, name, age, salary):
        super().__init__(name, age)
        self.salary = salary
    
    def greet(self):
        base = super().greet()
        return f"{base} and I work here!"

# Usage
john = Employee("John", 30, 50000)
print(john.greet())
```
            """,
            "regex": """
```python
# Regular expressions in Python
import re

# Match pattern
if re.match(r'\d+', '123'):
    print("It's a number!")

# Search
match = re.search(r'(\w+)@(\w+)', 'email@example.com')
if match:
    print(match.group(1))  # 'email'
    print(match.group(2))  # 'example'

# Find all
emails = re.findall(r'[\w.]+@[\w.]+', 'a@b.com c@d.com')

# Replace
text = re.sub(r'\d+', 'X', 'Age: 25')  # 'Age: X'

# Split
parts = re.split(r'\s+', 'a  b   c')  # ['a', 'b', 'c']
```
            """,
            "git": """
```bash
# Common Git commands

git init                    # Initialize repository
git clone <url>             # Clone repository
git add <file>              # Stage changes
git add .                   # Stage all changes
git commit -m "message"     # Commit changes
git push                    # Push to remote
git pull                    # Pull from remote
git status                  # Check status
git log                     # View commit history
git branch                  # List branches
git checkout -b <branch>    # Create and switch branch
git merge <branch>          # Merge branch
git stash                   # Stash changes
git stash pop               # Apply stashed changes
```
            """,
        }
        
        # Find matching snippet
        for key, code in snippets.items():
            if all(k in query for k in key.split()):
                return CommandResult(
                    success=True,
                    message=f"💻 *Code Snippet: {key.title()}*\n{code}\n_Need more help? Try:_\n• https://stackoverflow.com\n• https://github.com"
                )
        
        # Default response
        return CommandResult(
            success=True,
            message=f"""
💻 *Code Help: "{ctx.args_str}"*

Try these resources:
• https://stackoverflow.com/search?q={urllib.parse.quote(ctx.args_str)}
• https://github.com/search?q={urllib.parse.quote(ctx.args_str)}
• https://www.w3schools.com
• https://developer.mozilla.org

Or ask more specifically:
• !code python hello world
• !code javascript fetch
• !code sql select
            """.strip()
        )


@command("explain", description="Explain code or concept", min_args=1, category="ai")
class ExplainCommand(Command):
    """Explain programming concepts."""
    usage_examples = [
        "!explain recursion",
        "!explain list comprehension python",
        "!explain REST API",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        topic = ctx.args_str.lower()
        
        explanations = {
            "recursion": """
*Recursion* is when a function calls itself to solve a problem.

Example (factorial):
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

Key points:
• Must have a base case (stops recursion)
• Each call should move toward base case
• Can be less efficient than loops
• Great for tree/graph problems
            """,
            "list comprehension": """
*List Comprehension* is a concise way to create lists.

Basic syntax:
```python
[expression for item in iterable]

# Examples:
squares = [x**2 for x in range(5)]
# [0, 1, 4, 9, 16]

evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]
```

Benefits:
• More readable
• Often faster than loops
• One-liner solutions
            """,
            "rest api": """
*REST API* (Representational State Transfer) is an architectural style for designing networked applications.

Key principles:
• **Stateless**: Each request contains all info needed
• **HTTP Methods**: GET, POST, PUT, DELETE
• **Resources**: URLs represent resources (/users/123)
• **JSON**: Common data format

Example endpoints:
• GET /users - List users
• GET /users/1 - Get user 1
• POST /users - Create user
• PUT /users/1 - Update user 1
• DELETE /users/1 - Delete user 1
            """,
            "async": """
*Async/Await* allows writing asynchronous code that looks synchronous.

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)  # Non-blocking
    return "data"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

Benefits:
• Non-blocking I/O
• Better performance for I/O-bound tasks
• Easier to read than callbacks
            """,
        }
        
        for key, explanation in explanations.items():
            if key in topic:
                return CommandResult(
                    success=True,
                    message=f"📚 *Explanation: {key.title()}*\n{explanation}"
                )
        
        return CommandResult(
            success=True,
            message=f"""
📚 *Explanation Request: "{ctx.args_str}"*

Try these resources:
• https://dev.to/search?q={urllib.parse.quote(ctx.args_str)}
• https://www.freecodecamp.org/news/search/?query={urllib.parse.quote(ctx.args_str)}
• https://en.wikipedia.org/wiki/{urllib.parse.quote(ctx.args_str.replace(' ', '_'))}

Or ask about:
• !explain recursion
• !explain list comprehension
• !explain REST API
• !explain async
            """.strip()
        )


@command("detect", description="Detect language or content type", min_args=1, category="ai")
class DetectCommand(Command):
    """Content detection."""
    usage_examples = [
        "!detect language Hello world - Detect language",
        "!detect sentiment I love this! - Detect sentiment",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        detect_type = ctx.args[0].lower() if ctx.args else "language"
        text = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else ""
        
        if detect_type == "language":
            # Simple language detection based on common words
            lang_indicators = {
                "spanish": ["el", "la", "de", "que", "en", "un", "es", "y", "a", "los"],
                "french": ["le", "la", "de", "et", "un", "est", "que", "en", "a", "les"],
                "german": ["der", "die", "und", "den", "von", "zu", "das", "mit", "sich", "des"],
                "italian": ["il", "di", "che", "è", "la", "un", "a", "per", "non", "con"],
                "portuguese": ["o", "de", "a", "que", "e", "do", "da", "em", "um", "para"],
                "japanese": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
                "chinese": ["的", "一", "是", "不", "了", "在", "人", "有", "我", "他"],
                "arabic": ["في", "من", "إلى", "على", "هذا", "أن", "هو", "التي", "عن", "لا"],
            }
            
            text_lower = text.lower()
            scores = {}
            
            for lang, words in lang_indicators.items():
                score = sum(1 for word in words if word in text_lower)
                if score > 0:
                    scores[lang] = score
            
            if scores:
                detected = max(scores, key=scores.get)
                confidence = min(scores[detected] * 10, 100)
                return CommandResult(
                    success=True,
                    message=f"🌍 *Language Detection*\n\nDetected: {detected.title()}\nConfidence: {confidence}%\n\nText: \"{text[:100]}\""
                )
            else:
                return CommandResult(
                    success=True,
                    message=f"🌍 *Language Detection*\n\nDetected: English (default)\n\nText: \"{text[:100]}\""
                )
        
        elif detect_type == "sentiment":
            # Simple sentiment analysis
            positive_words = ["love", "great", "awesome", "good", "happy", "excellent", "amazing", "best", "fantastic", "wonderful"]
            negative_words = ["hate", "bad", "terrible", "awful", "worst", "sad", "angry", "horrible", "disgusting", "pathetic"]
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                sentiment = "😊 Positive"
            elif neg_count > pos_count:
                sentiment = "😞 Negative"
            else:
                sentiment = "😐 Neutral"
            
            return CommandResult(
                success=True,
                message=f"📊 *Sentiment Analysis*\n\nResult: {sentiment}\nPositive indicators: {pos_count}\nNegative indicators: {neg_count}\n\nText: \"{text[:100]}\""
            )
        
        else:
            return CommandResult(
                success=False,
                message="❌ Usage: !detect language <text> OR !detect sentiment <text>"
            )
