"""
Game commands.
"""
import random

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier
from utils.redis_client import redis_client


@command("game", description="List available games", category="games")
class GamesListCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        message = """
🎮 *Available Games*

1. *Wordle* - Guess the 5-letter word
   !wordle - Start a new game
   !wordle <word> - Make a guess

2. *Trivia* - Test your knowledge
   !trivia - Start trivia game
   !trivia <answer> - Answer question

3. *Hangman* - Classic word guessing
   !hangman - Start new game
   !hangman <letter> - Guess a letter

4. *Number Guess* - Guess the number
   !guess - Start new game
   !guess <number> - Make a guess

5. *Rock Paper Scissors* - Classic game
   !rps <rock/paper/scissors>

Type !help <game> for more details!
        """.strip()
        return CommandResult(success=True, message=message)


@command("wordle", description="Play Wordle game", category="games")
class WordleCommand(Command):
    usage_examples = [
        "!wordle - Start new game",
        "!wordle crane - Make a guess",
        "!wordle quit - End game",
    ]
    cooldown_seconds = 2
    
    WORDS = [
        "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT", "AFTER", "AGAIN",
        "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIKE", "ALIVE", "ALLOW", "ALONE",
        "ALONG", "ALTER", "AMONG", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY", "ARENA",
        "ARGUE", "ARISE", "ARRAY", "ASIDE", "ASSET", "AUDIO", "AUDIT", "AVOID", "AWARD", "AWARE",
        "BADLY", "BAKER", "BASIS", "BEACH", "BEGAN", "BEGIN", "BEGUN", "BEING", "BELOW", "BENCH",
        "BILLY", "BIRTH", "BLACK", "BLAME", "BLIND", "BLOCK", "BLOOD", "BOARD", "BOOST", "BOOTH",
        "BOUND", "BRAIN", "BRAND", "BREAD", "BREAK", "BREED", "BRIEF", "BRING", "BROAD", "BROKE",
        "BROWN", "BUILD", "BUILT", "BUYER", "CABLE", "CALM", "CAMEL", "CAMEO", "CANDY", "CARGO",
        "CARRY", "CATCH", "CAUSE", "CHAIN", "CHAIR", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST",
        "CHIEF", "CHILD", "CHINA", "CHOSE", "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLICK",
        "CLOCK", "CLOSE", "COACH", "COAST", "COULD", "COUNT", "COURT", "COVER", "CRAFT", "CRASH",
        "CREAM", "CRIME", "CROSS", "CROWD", "CROWN", "CURVE", "CYCLE", "DAILY", "DANCE", "DATED",
        "DEALT", "DEATH", "DEBUT", "DELAY", "DEPTH", "DERBY", "DOING", "DOUBT", "DOZEN", "DRAFT",
        "DRAMA", "DREAM", "DRESS", "DRINK", "DRIVE", "DROVE", "DYING", "EARLY", "EARTH", "EIGHT",
        "ELITE", "EMPTY", "ENEMY", "ENJOY", "ENTER", "ENTRY", "EQUAL", "ERROR", "EVENT", "EVERY",
        "EXACT", "EXIST", "EXTRA", "FAITH", "FALSE", "FAULT", "FIBER", "FIELD", "FIFTH", "FIFTY",
        "FIGHT", "FINAL", "FIRST", "FIXED", "FLASH", "FLEET", "FLOOR", "FLUID", "FOCUS", "FORCE",
        "FORTH", "FORTY", "FORUM", "FOUND", "FRAME", "FRANK", "FRAUD", "FRESH", "FRONT", "FRUIT",
        "FULLY", "FUNNY", "GIANT", "GIVEN", "GLASS", "GLOBE", "GOING", "GRACE", "GRADE", "GRAND",
        "GRANT", "GRASS", "GREAT", "GREEN", "GROSS", "GROUP", "GROWN", "GUARD", "GUESS", "GUEST",
        "GUIDE", "HAPPY", "HEART", "HEAVY", "HENCE", "HENRY", "HORSE", "HOTEL", "HOUSE", "HUMAN",
        "IDEAL", "IMAGE", "INDEX", "INNER", "INPUT", "ISSUE", "JAPAN", "JIMMY", "JOINT", "JONES",
        "JUDGE", "KNOWN", "LABEL", "LARGE", "LASER", "LATER", "LAUGH", "LAYER", "LEARN", "LEASE",
        "LEAST", "LEAVE", "LEGAL", "LEVEL", "LEWIS", "LIGHT", "LIMIT", "LINKS", "LIVES", "LOCAL",
        "LOGIC", "LOOSE", "LOWER", "LUCKY", "LUNCH", "LYING", "MAGIC", "MAJOR", "MAKER", "MARCH",
        "MARIA", "MATCH", "MAYBE", "MAYOR", "MEANT", "MEDIA", "METAL", "MIGHT", "MINOR", "MINUS",
        "MIXED", "MODEL", "MONEY", "MONTH", "MORAL", "MOTOR", "MOUNT", "MOUSE", "MOUTH", "MOVIE",
        "MUSIC", "NEEDS", "NEVER", "NEWLY", "NIGHT", "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE",
        "OCCUR", "OCEAN", "OFFER", "OFTEN", "ORDER", "OTHER", "OUGHT", "PAINT", "PANEL", "PAPER",
        "PARTY", "PEACE", "PHASE", "PHONE", "PHOTO", "PIECE", "PILOT", "PITCH", "PLACE", "PLAIN",
        "PLANE", "PLANT", "PLATE", "POINT", "POUND", "POWER", "PRESS", "PRICE", "PRIDE", "PRIME",
        "PRINT", "PRIOR", "PRIZE", "PROOF", "PROUD", "PROVE", "QUEEN", "QUICK", "QUIET", "QUITE",
        "RADIO", "RAISE", "RANGE", "RAPID", "RATIO", "REACH", "READY", "REFER", "RIGHT", "RIVAL",
        "RIVER", "ROBIN", "ROBOT", "ROUND", "ROUTE", "ROYAL", "RURAL", "SCALE", "SCENE", "SCOPE",
        "SCORE", "SEAL", "SEASON", "SEAT", "SECOND", "SECRET", "SECTION", "SECTOR", "SECURE", "SEEING",
        "SELECT", "SELLER", "SENIOR", "SERIES", "SERVER", "SETTLE", "SEVERE", "SEXUAL", "SHOULD",
        "SIGNAL", "SIGNED", "SILENT", "SILVER", "SIMPLE", "SIMPLY", "SINGLE", "SISTER", "SLIGHT",
        "SMOOTH", "SOCIAL", "SOCIETY", "SOFTLY", "SOLELY", "SOUGHT", "SOURCE", "SOVIET", "SPEECH",
        "SPIRIT", "SPOKEN", "SPREAD", "SPRING", "SQUARE", "STABLE", "STATUS", "STEADY", "STOLEN",
        "STRAIN", "STREAM", "STREET", "STRESS", "STRICT", "STRIKE", "STRING", "STRONG", "STRUCK",
        "STUDIO", "SUBMIT", "SUDDEN", "SUFFER", "SUMMER", "SUMMIT", "SUPPLY", "SURELY", "SURVEY",
        "SWITCH", "SYMBOL", "SYSTEM", "TAKING", "TALENT", "TARGET", "TAUGHT", "TENANT", "TENDER",
        "TENNIS", "THANKS", "THEORY", "THIRTY", "THOUGH", "THREAT", "THROWN", "TICKET", "TIMING",
        "TISSUE", "TONGUE", "TOPICS", "TOUCH", "TOWARD", "TRAVEL", "TREATY", "TRYING", "TWELVE",
        "TWENTY", "UNABLE", "UNIQUE", "UNITED", "UNLESS", "UNLIKE", "UPDATE", "USEFUL", "VALLEY",
        "VARIED", "VENDOR", "VERSUS", "VICTIM", "VISION", "VISUAL", "VOLUME", "WALKER", "WANT", "WARNING",
        "WEALTH", "WEEKLY", "WEIGHT", "WHOLLY", "WINDOW", "WINNER", "WINTER", "WITHIN", "WONDER",
        "WORKER", "WRIGHT", "WRITER", "YELLOW", "YIELD", "YOUNG", "YOUTH",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        user_id = ctx.user.id
        
        # Check for quit command
        if ctx.args and ctx.args[0].lower() == "quit":
            await redis_client.delete_game_state(user_id, "wordle")
            return CommandResult(success=True, message="🎮 Wordle game ended. Thanks for playing!")
        
        # Get or create game state
        state = await redis_client.get_game_state(user_id, "wordle")
        
        if not state:
            # Start new game
            word = random.choice(self.WORDS)
            state = {
                "word": word,
                "guesses": [],
                "max_guesses": 6,
            }
            await redis_client.set_game_state(user_id, "wordle", state)
            
            return CommandResult(
                success=True,
                message="""
🎮 *New Wordle Game Started!*

Guess the 5-letter word in 6 tries.

Feedback:
🟩 = Correct letter, correct position
🟨 = Correct letter, wrong position
⬜ = Letter not in word

Type !wordle <word> to guess
Type !wordle quit to end
                """.strip()
            )
        
        # Process guess
        if not ctx.args:
            # Show current game state
            return await self._show_game_state(state)
        
        guess = ctx.args[0].upper()
        
        if len(guess) != 5:
            return CommandResult(
                success=False,
                message="❌ Guess must be exactly 5 letters!"
            )
        
        if not guess.isalpha():
            return CommandResult(
                success=False,
                message="❌ Guess must contain only letters!"
            )
        
        word = state["word"]
        guesses = state["guesses"]
        
        if guess in [g["word"] for g in guesses]:
            return CommandResult(
                success=False,
                message="❌ You already guessed that word!"
            )
        
        # Calculate feedback
        feedback = self._calculate_feedback(word, guess)
        guesses.append({"word": guess, "feedback": feedback})
        state["guesses"] = guesses
        
        # Check win/lose
        if guess == word:
            await redis_client.delete_game_state(user_id, "wordle")
            return CommandResult(
                success=True,
                message=f"""
🎉 *Congratulations!*

You guessed the word: *{word}*
Guesses: {len(guesses)}/{state["max_guesses"]}

{self._format_guesses(guesses)}

🏆 Well done!
                """.strip()
            )
        
        if len(guesses) >= state["max_guesses"]:
            await redis_client.delete_game_state(user_id, "wordle")
            return CommandResult(
                success=True,
                message=f"""
😢 *Game Over!*

The word was: *{word}*

{self._format_guesses(guesses)}

Type !wordle to play again!
                """.strip()
            )
        
        # Save state and show progress
        await redis_client.set_game_state(user_id, "wordle", state)
        return await self._show_game_state(state)
    
    def _calculate_feedback(self, word: str, guess: str) -> list:
        """Calculate Wordle feedback for a guess."""
        feedback = ["⬜"] * 5
        word_chars = list(word)
        guess_chars = list(guess)
        
        # First pass: correct position
        for i in range(5):
            if guess_chars[i] == word_chars[i]:
                feedback[i] = "🟩"
                word_chars[i] = None
                guess_chars[i] = None
        
        # Second pass: correct letter, wrong position
        for i in range(5):
            if guess_chars[i] is not None and guess_chars[i] in word_chars:
                feedback[i] = "🟨"
                word_chars[word_chars.index(guess_chars[i])] = None
        
        return feedback
    
    def _format_guesses(self, guesses: list) -> str:
        """Format guesses for display."""
        lines = []
        for g in guesses:
            lines.append(f"{g['word']} {' '.join(g['feedback'])}")
        return "\n".join(lines)
    
    async def _show_game_state(self, state: dict) -> CommandResult:
        """Show current game state."""
        guesses = state["guesses"]
        remaining = state["max_guesses"] - len(guesses)
        
        message = f"""
🎮 *Wordle*

{self._format_guesses(guesses) if guesses else "No guesses yet..."}

Guesses: {len(guesses)}/{state["max_guesses"]}
Remaining: {remaining}

Type !wordle <word> to guess
        """.strip()
        
        return CommandResult(success=True, message=message)


@command("trivia", description="Play trivia game", category="games")
class TriviaCommand(Command):
    QUESTIONS = [
        ("What is the capital of France?", "Paris", ["London", "Berlin", "Madrid", "Paris"]),
        ("What is 2 + 2?", "4", ["3", "4", "5", "6"]),
        ("Who painted the Mona Lisa?", "Leonardo da Vinci", ["Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo"]),
        ("What is the largest planet?", "Jupiter", ["Mars", "Jupiter", "Saturn", "Neptune"]),
        ("What year did World War II end?", "1945", ["1943", "1944", "1945", "1946"]),
        ("What is the chemical symbol for gold?", "Au", ["Ag", "Au", "Fe", "Cu"]),
        ("How many continents are there?", "7", ["5", "6", "7", "8"]),
        ("What is the speed of light?", "299,792 km/s", ["150,000 km/s", "299,792 km/s", "400,000 km/s", "1,000,000 km/s"]),
        ("Who wrote Romeo and Juliet?", "William Shakespeare", ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"]),
        ("What is the smallest prime number?", "2", ["0", "1", "2", "3"]),
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        user_id = ctx.user.id
        state = await redis_client.get_game_state(user_id, "trivia")
        
        if not state:
            # Start new game
            question_data = random.choice(self.QUESTIONS)
            state = {
                "question": question_data[0],
                "answer": question_data[1],
                "options": question_data[2],
                "answered": False,
            }
            await redis_client.set_game_state(user_id, "trivia", state)
            
            options_text = "\n".join([f"  {chr(65+i)}. {opt}" for i, opt in enumerate(state["options"])])
            
            return CommandResult(
                success=True,
                message=f"""
❓ *Trivia Question*

{state["question"]}

{options_text}

Reply with !trivia <A/B/C/D> or the answer!
                """.strip()
            )
        
        if not ctx.args:
            # Reshow question
            options_text = "\n".join([f"  {chr(65+i)}. {opt}" for i, opt in enumerate(state["options"])])
            return CommandResult(
                success=True,
                message=f"""
❓ *Trivia Question*

{state["question"]}

{options_text}
                """.strip()
            )
        
        # Process answer
        user_answer = ctx.args_str
        correct_answer = state["answer"]
        
        # Check if answer is letter (A, B, C, D)
        if len(user_answer) == 1 and user_answer.upper() in "ABCD":
            idx = ord(user_answer.upper()) - ord('A')
            if idx < len(state["options"]):
                user_answer = state["options"][idx]
        
        is_correct = user_answer.lower() == correct_answer.lower()
        
        await redis_client.delete_game_state(user_id, "trivia")
        
        if is_correct:
            return CommandResult(
                success=True,
                message=f"""
✅ *Correct!*

The answer was: *{correct_answer}*

🎉 Great job! Type !trivia for another question!
                """.strip()
            )
        else:
            return CommandResult(
                success=True,
                message=f"""
❌ *Wrong!*

Your answer: {user_answer}
Correct answer: *{correct_answer}*

Type !trivia to try again!
                """.strip()
            )


@command("hangman", description="Play Hangman", category="games")
class HangmanCommand(Command):
    WORDS = ["PYTHON", "JAVASCRIPT", "COMPUTER", "ALGORITHM", "DATABASE", "NETWORK", "SECURITY", "PROGRAMMING"]
    
    HANGMAN_STAGES = [
        "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
        "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        user_id = ctx.user.id
        state = await redis_client.get_game_state(user_id, "hangman")
        
        if not state:
            # Start new game
            word = random.choice(self.WORDS)
            state = {
                "word": word,
                "guessed": [],
                "wrong": 0,
                "max_wrong": 6,
            }
            await redis_client.set_game_state(user_id, "hangman", state)
            
            masked = " ".join(["_"] * len(word))
            return CommandResult(
                success=True,
                message=f"""
🎮 *Hangman*

{self.HANGMAN_STAGES[0]}

Word: {masked}

Guess a letter with !hangman <letter>
                """.strip()
            )
        
        if not ctx.args:
            # Show current state
            return await self._show_state(state)
        
        guess = ctx.args[0][0].upper()
        
        if not guess.isalpha():
            return CommandResult(success=False, message="❌ Please guess a letter!")
        
        if guess in state["guessed"]:
            return CommandResult(success=False, message=f"❌ You already guessed '{guess}'!")
        
        state["guessed"].append(guess)
        
        if guess not in state["word"]:
            state["wrong"] += 1
        
        # Check win
        word_letters = set(state["word"])
        if word_letters.issubset(set(state["guessed"])):
            await redis_client.delete_game_state(user_id, "hangman")
            return CommandResult(
                success=True,
                message=f"""
🎉 *You Won!*

Word: *{state["word"]}*

Wrong guesses: {state["wrong"]}/{state["max_wrong"]}

Great job! Type !hangman to play again!
                """.strip()
            )
        
        # Check lose
        if state["wrong"] >= state["max_wrong"]:
            await redis_client.delete_game_state(user_id, "hangman")
            return CommandResult(
                success=True,
                message=f"""
😢 *Game Over!*

{self.HANGMAN_STAGES[state["wrong"]]}

The word was: *{state["word"]}*

Type !hangman to try again!
                """.strip()
            )
        
        await redis_client.set_game_state(user_id, "hangman", state)
        return await self._show_state(state)
    
    async def _show_state(self, state: dict) -> CommandResult:
        word = state["word"]
        guessed = state["guessed"]
        wrong = state["wrong"]
        
        masked = " ".join([c if c in guessed else "_" for c in word])
        guessed_str = ", ".join(sorted(guessed)) if guessed else "None"
        
        return CommandResult(
            success=True,
            message=f"""
🎮 *Hangman*

{self.HANGMAN_STAGES[wrong]}

Word: {masked}
Guessed: {guessed_str}
Wrong: {wrong}/{state["max_wrong"]}

!hangman <letter> to guess
            """.strip()
        )


@command("guess", description="Guess the number game", category="games")
class GuessNumberCommand(Command):
    async def execute(self, ctx: CommandContext) -> CommandResult:
        user_id = ctx.user.id
        state = await redis_client.get_game_state(user_id, "guess")
        
        if not state:
            # Start new game
            number = random.randint(1, 100)
            state = {
                "number": number,
                "attempts": 0,
                "max_attempts": 7,
            }
            await redis_client.set_game_state(user_id, "guess", state)
            
            return CommandResult(
                success=True,
                message="""
🎮 *Guess the Number*

I'm thinking of a number between 1 and 100.
You have 7 attempts!

Type !guess <number>
                """.strip()
            )
        
        if not ctx.args:
            return CommandResult(
                success=True,
                message=f"Guess a number between 1 and 100. Attempts: {state['attempts']}/{state['max_attempts']}"
            )
        
        try:
            guess = int(ctx.args[0])
        except ValueError:
            return CommandResult(success=False, message="❌ Please enter a valid number!")
        
        state["attempts"] += 1
        number = state["number"]
        attempts = state["attempts"]
        max_attempts = state["max_attempts"]
        
        if guess == number:
            await redis_client.delete_game_state(user_id, "guess")
            return CommandResult(
                success=True,
                message=f"""
🎉 *Correct!*

The number was *{number}*!
You guessed it in {attempts} attempt(s)!

Type !guess to play again!
                """.strip()
            )
        
        if attempts >= max_attempts:
            await redis_client.delete_game_state(user_id, "guess")
            return CommandResult(
                success=True,
                message=f"""
😢 *Game Over!*

The number was *{number}*.
You used all {max_attempts} attempts.

Type !guess to try again!
                """.strip()
            )
        
        hint = "too high" if guess > number else "too low"
        remaining = max_attempts - attempts
        
        await redis_client.set_game_state(user_id, "guess", state)
        return CommandResult(
            success=True,
            message=f"{guess} is {hint}! 📊 Attempts: {attempts}/{max_attempts} ({remaining} left)"
        )


@command("rps", description="Rock Paper Scissors", min_args=1, category="games")
class RPSCommand(Command):
    usage_examples = [
        "!rps rock",
        "!rps paper",
        "!rps scissors",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        choices = ["rock", "paper", "scissors"]
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        user_choice = ctx.args[0].lower()
        
        if user_choice not in choices:
            return CommandResult(
                success=False,
                message="❌ Choose: rock, paper, or scissors"
            )
        
        bot_choice = random.choice(choices)
        
        # Determine winner
        if user_choice == bot_choice:
            result = "🤝 It's a tie!"
        elif (
            (user_choice == "rock" and bot_choice == "scissors") or
            (user_choice == "paper" and bot_choice == "rock") or
            (user_choice == "scissors" and bot_choice == "paper")
        ):
            result = "🎉 You win!"
        else:
            result = "😢 You lose!"
        
        return CommandResult(
            success=True,
            message=f"""
🎮 *Rock Paper Scissors*

You: {emojis[user_choice]} {user_choice.title()}
Bot: {emojis[bot_choice]} {bot_choice.title()}

{result}
            """.strip()
        )
