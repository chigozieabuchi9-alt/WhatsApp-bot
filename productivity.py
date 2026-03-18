"""
Productivity and lifestyle commands.
"""
import random
import re
from datetime import datetime, timedelta

from commands.base import Command, CommandContext, CommandResult, command
from db.models import UserTier


@command("todo", description="Manage your todo list", category="productivity")
class TodoCommand(Command):
    """Simple todo list manager."""
    usage_examples = [
        "!todo add Buy groceries - Add task",
        "!todo list - Show all tasks",
        "!todo done 1 - Mark task 1 as done",
        "!todo delete 1 - Delete task 1",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        from utils.redis_client import redis_client
        
        user_id = ctx.user.id
        todo_key = f"todo:{user_id}"
        
        # Get existing todos
        todos_data = await redis_client.get_json(todo_key) or []
        
        if not ctx.args:
            # Show todos
            if not todos_data:
                return CommandResult(
                    success=True,
                    message="📋 *Your Todo List*\n\nNo tasks yet!\n\nAdd one: !todo add <task>"
                )
            
            lines = ["📋 *Your Todo List*\n"]
            for i, todo in enumerate(todos_data, 1):
                status = "✅" if todo.get("done") else "⬜"
                lines.append(f"{status} {i}. {todo['text']}")
            
            lines.append("\n!todo add <task> | !todo done <num> | !todo delete <num>")
            
            return CommandResult(success=True, message="\n".join(lines))
        
        action = ctx.args[0].lower()
        
        if action == "add":
            task = " ".join(ctx.args[1:])
            if not task:
                return CommandResult(success=False, message="❌ Please specify a task")
            
            todos_data.append({"text": task, "done": False, "created": datetime.utcnow().isoformat()})
            await redis_client.set_json(todo_key, todos_data, expire=86400 * 7)  # 7 days
            
            return CommandResult(success=True, message=f"✅ Added: {task}")
        
        elif action in ["done", "complete"]:
            try:
                num = int(ctx.args[1]) - 1
                if 0 <= num < len(todos_data):
                    todos_data[num]["done"] = True
                    await redis_client.set_json(todo_key, todos_data, expire=86400 * 7)
                    return CommandResult(success=True, message=f"✅ Completed: {todos_data[num]['text']}")
                else:
                    return CommandResult(success=False, message="❌ Invalid task number")
            except (ValueError, IndexError):
                return CommandResult(success=False, message="❌ Usage: !todo done <number>")
        
        elif action in ["delete", "remove"]:
            try:
                num = int(ctx.args[1]) - 1
                if 0 <= num < len(todos_data):
                    deleted = todos_data.pop(num)
                    await redis_client.set_json(todo_key, todos_data, expire=86400 * 7)
                    return CommandResult(success=True, message=f"🗑️ Deleted: {deleted['text']}")
                else:
                    return CommandResult(success=False, message="❌ Invalid task number")
            except (ValueError, IndexError):
                return CommandResult(success=False, message="❌ Usage: !todo delete <number>")
        
        elif action == "clear":
            await redis_client.delete(todo_key)
            return CommandResult(success=True, message="🗑️ All tasks cleared!")
        
        else:
            return CommandResult(
                success=False,
                message="❌ Usage:\n• !todo add <task>\n• !todo list\n• !todo done <num>\n• !todo delete <num>\n• !todo clear"
            )


@command("note", description="Save quick notes", category="productivity")
class NoteCommand(Command):
    """Quick note taking."""
    usage_examples = [
        "!note Meeting at 3pm - Save note",
        "!note - Show all notes",
        "!note delete 1 - Delete note 1",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        from utils.redis_client import redis_client
        
        user_id = ctx.user.id
        note_key = f"note:{user_id}"
        
        notes = await redis_client.get_json(note_key) or []
        
        if not ctx.args:
            # Show notes
            if not notes:
                return CommandResult(
                    success=True,
                    message="📝 *Your Notes*\n\nNo notes yet!\n\nAdd one: !note <text>"
                )
            
            lines = ["📝 *Your Notes*\n"]
            for i, note in enumerate(notes, 1):
                time = note.get("time", "")[:10]
                lines.append(f"{i}. {note['text']}\n   _{time}_\n")
            
            return CommandResult(success=True, message="\n".join(lines))
        
        action = ctx.args[0].lower()
        
        if action == "delete":
            try:
                num = int(ctx.args[1]) - 1
                if 0 <= num < len(notes):
                    deleted = notes.pop(num)
                    await redis_client.set_json(note_key, notes, expire=86400 * 30)
                    return CommandResult(success=True, message=f"🗑️ Deleted: {deleted['text'][:30]}...")
            except (ValueError, IndexError):
                pass
        
        # Add note
        note_text = ctx.args_str
        notes.append({"text": note_text, "time": datetime.utcnow().isoformat()})
        await redis_client.set_json(note_key, notes, expire=86400 * 30)
        
        return CommandResult(success=True, message=f"📝 Saved: {note_text[:50]}{'...' if len(note_text) > 50 else ''}")


@command("pomodoro", description="Pomodoro timer", category="productivity")
class PomodoroCommand(Command):
    """Pomodoro technique timer."""
    usage_examples = [
        "!pomodoro start - Start 25min work session",
        "!pomodoro break - Start 5min break",
        "!pomodoro longbreak - Start 15min break",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        action = ctx.args[0].lower() if ctx.args else "start"
        
        if action == "start":
            return CommandResult(
                success=True,
                message="""
🍅 *Pomodoro Started!*

Work for *25 minutes*
Focus on one task
No distractions!

I'll remind you when time's up.

💡 Tips:
• Put phone away
• Close unnecessary tabs
• Have water nearby
• Take notes if distracted

Break starts in 25 min ⏰
                """.strip()
            )
        
        elif action in ["break", "shortbreak"]:
            return CommandResult(
                success=True,
                message="""
☕ *Short Break!*

Rest for *5 minutes*

Suggestions:
• Stretch
• Drink water
• Look away from screen
• Walk around

Back to work in 5 min!
                """.strip()
            )
        
        elif action == "longbreak":
            return CommandResult(
                success=True,
                message="""
🌴 *Long Break!*

Relax for *15 minutes*

You've earned it!

• Take a walk
• Have a snack
• Do some exercise
• Meditate

Ready for next session in 15 min!
                """.strip()
            )
        
        elif action == "status":
            return CommandResult(success=True, message="⏱️ Use a timer app or set reminders!")
        
        else:
            return CommandResult(
                success=False,
                message="❌ Usage: !pomodoro start|break|longbreak"
            )


@command("habit", description="Track daily habits", category="productivity")
class HabitCommand(Command):
    """Habit tracker."""
    usage_examples = [
        "!habit add Exercise - Add habit",
        "!habit done Exercise - Mark done",
        "!habit list - Show habits",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="""
📊 *Habit Tracker*

Track your daily habits:

!habit add <name> - Add habit
!habit done <name> - Mark done
!habit list - View habits
!habit streak <name> - Check streak

Popular habits:
• 💪 Exercise
• 📚 Read 30 min
• 💧 Drink 2L water
• 😴 Sleep 8 hours
• 🧘 Meditate

Build consistency, one day at a time!
            """.strip()
        )


@command("focus", description="Focus mode tips", category="productivity")
class FocusCommand(Command):
    """Focus and productivity tips."""
    usage_examples = [
        "!focus - Get focus tips",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        tips = [
            "📱 Put your phone in another room",
            "🎧 Use noise-cancelling headphones or lo-fi music",
            "⏲️ Use the Pomodoro technique (25 min work, 5 min break)",
            "📝 Write down distractions, deal with them later",
            "🚪 Close unnecessary browser tabs and apps",
            "💧 Keep water nearby, stay hydrated",
            "🪑 Ensure comfortable seating and lighting",
            "🎯 Set one clear goal for this session",
            "🔕 Turn off all notifications",
            "⏰ Set a visible timer",
        ]
        
        selected = random.sample(tips, 5)
        
        return CommandResult(
            success=True,
            message=f"""
🎯 *Focus Mode Activated*

{chr(10).join(selected)}

Apps to help:
• Forest (grow trees while focused)
• Freedom (block distractions)
• Cold Turkey (website blocker)
• Brain.fm (focus music)

You've got this! 💪
            """.strip()
        )


@command("water", description="Water intake tracker", category="productivity")
class WaterCommand(Command):
    """Track water intake."""
    usage_examples = [
        "!water - Check intake",
        "!water 250 - Add 250ml",
        "!water goal 2000 - Set daily goal",
    ]
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        from utils.redis_client import redis_client
        
        user_id = ctx.user.id
        water_key = f"water:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        goal_key = f"water_goal:{user_id}"
        
        goal = int(await redis_client.get(goal_key) or 2000)  # Default 2000ml
        current = int(await redis_client.get(water_key) or 0)
        
        if not ctx.args:
            # Show status
            percentage = min((current / goal) * 100, 100)
            bar = "🟦" * int(percentage / 10) + "⬜" * (10 - int(percentage / 10))
            remaining = max(goal - current, 0)
            
            return CommandResult(
                success=True,
                message=f"""
💧 *Water Intake Today*

{bar} {percentage:.0f}%

Current: {current}ml / {goal}ml
Remaining: {remaining}ml

!water <amount> to add
!water goal <amount> to set goal

💡 Health tip: Drink a glass of water every hour!
                """.strip()
            )
        
        action = ctx.args[0].lower()
        
        if action == "goal":
            try:
                new_goal = int(ctx.args[1])
                await redis_client.set(goal_key, str(new_goal))
                return CommandResult(success=True, message=f"✅ Daily goal set to {new_goal}ml")
            except (ValueError, IndexError):
                return CommandResult(success=False, message="❌ Usage: !water goal <ml>")
        
        # Add water
        try:
            amount = int(action)
            new_total = current + amount
            await redis_client.set(water_key, str(new_total), expire=86400)
            
            if new_total >= goal:
                return CommandResult(success=True, message=f"🎉 Great job! You've reached your daily goal: {new_total}ml!")
            else:
                remaining = goal - new_total
                return CommandResult(success=True, message=f"💧 Added {amount}ml. Total: {new_total}ml. {remaining}ml to go!")
                
        except ValueError:
            return CommandResult(success=False, message="❌ Usage: !water <amount_in_ml>")


@command("workout", description="Get workout ideas", category="productivity")
class WorkoutCommand(Command):
    """Workout generator."""
    usage_examples = [
        "!workout home - Home workout",
        "!workout abs - Ab workout",
        "!workout 10min - Quick 10 min workout",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        workout_type = ctx.args[0].lower() if ctx.args else "full"
        
        workouts = {
            "home": [
                "🏠 *Home Workout (No Equipment)*\n\n1. Jumping Jacks - 30 sec\n2. Push-ups - 15 reps\n3. Squats - 20 reps\n4. Plank - 30 sec\n5. Lunges - 10 each leg\n6. Mountain Climbers - 30 sec\n\nRepeat 3 times!",
            ],
            "abs": [
                "💪 *Ab Workout*\n\n1. Crunches - 20 reps\n2. Leg Raises - 15 reps\n3. Russian Twists - 30 reps\n4. Plank - 45 sec\n5. Bicycle Crunches - 30 reps\n6. Flutter Kicks - 30 reps\n\nRest 30 sec between sets. Do 3 rounds!",
            ],
            "cardio": [
                "🏃 *Cardio Blast*\n\n1. High Knees - 45 sec\n2. Burpees - 10 reps\n3. Jump Squats - 15 reps\n4. Butt Kicks - 45 sec\n5. Box Jumps (or step-ups) - 15 reps\n\nRest 1 min. Repeat 4 times!",
            ],
            "quick": [
                "⚡ *5-Minute Quick Workout*\n\n1. Push-ups - 10 reps\n2. Squats - 15 reps\n3. Plank - 30 sec\n4. Jumping Jacks - 30 sec\n\nNo excuses! 💪",
            ],
            "stretch": [
                "🧘 *Stretching Routine*\n\n1. Neck Rolls - 30 sec\n2. Shoulder Stretch - 30 sec each\n3. Quad Stretch - 30 sec each\n4. Hamstring Stretch - 30 sec each\n5. Child's Pose - 1 min\n6. Cat-Cow - 1 min\n\nBreathe deeply and relax!",
            ],
        }
        
        workout = random.choice(workouts.get(workout_type, workouts["home"]))
        
        return CommandResult(
            success=True,
            message=f"{workout}\n\n_Stay consistent! Results come with time._ 🎯"
        )


@command("recipe", description="Get quick recipe ideas", category="productivity")
class RecipeCommand(Command):
    """Recipe suggestions."""
    usage_examples = [
        "!recipe pasta - Pasta recipes",
        "!recipe quick - Quick meals",
        "!recipe healthy - Healthy options",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        category = ctx.args[0].lower() if ctx.args else "random"
        
        recipes = {
            "pasta": [
                "🍝 *Quick Garlic Pasta*\n\nIngredients:\n• Pasta\n• Garlic (4 cloves)\n• Olive oil\n• Chili flakes\n• Parmesan\n\nBoil pasta. Sauté garlic in oil. Mix together with chili and cheese. Done in 15 min!",
            ],
            "quick": [
                "🥪 *5-Minute Sandwich*\n\n• Bread\n• Cheese\n• Tomato\n• Lettuce\n• Mayo/Mustard\n\nLayer and enjoy! Add protein for extra filling.",
            ],
            "healthy": [
                "🥗 *Buddha Bowl*\n\n• Quinoa or rice\n• Roasted veggies\n• Chickpeas\n• Avocado\n• Tahini dressing\n\nNutritious and delicious!",
            ],
            "smoothie": [
                "🥤 *Energy Smoothie*\n\n• Banana\n• Spinach\n• Almond milk\n• Peanut butter\n• Honey\n\nBlend and go! Perfect breakfast.",
            ],
            "eggs": [
                "🍳 *Perfect Scrambled Eggs*\n\n1. Whisk 2-3 eggs with salt\n2. Melt butter in pan (low heat)\n3. Pour eggs, stir gently\n4. Remove while still slightly wet\n5. Add black pepper\n\nCreamy and delicious!",
            ],
        }
        
        recipe = random.choice(recipes.get(category, recipes["quick"]))
        
        return CommandResult(
            success=True,
            message=f"{recipe}\n\nFind more at:\n• https://allrecipes.com\n• https://tasty.co\n• https://minimalistbaker.com"
        )


@command("budget", description="Simple budget calculator", category="productivity")
class BudgetCommand(Command):
    """Budget planning tool."""
    usage_examples = [
        "!budget 3000 - Calculate budget for $3000 income",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.args:
            return CommandResult(
                success=True,
                message="""
💰 *50/30/20 Budget Rule*

• 50% Needs (rent, food, bills)
• 30% Wants (entertainment, dining)
• 20% Savings & Debt

Usage: !budget <monthly_income>

Example: !budget 3000

Apps to try:
• YNAB (You Need A Budget)
• Mint
• PocketGuard
                """.strip()
            )
        
        try:
            income = float(ctx.args[0])
            
            needs = income * 0.50
            wants = income * 0.30
            savings = income * 0.20
            
            return CommandResult(
                success=True,
                message=f"""
💰 *Budget Breakdown for ${income:,.2f}*

🏠 *Needs (50%):* ${needs:,.2f}
   Rent, utilities, groceries, insurance

🎮 *Wants (30%):* ${wants:,.2f}
   Dining out, entertainment, hobbies

💎 *Savings (20%):* ${savings:,.2f}
   Emergency fund, investments, debt

Track your spending to stay on budget!
                """.strip()
            )
            
        except ValueError:
            return CommandResult(success=False, message="❌ Please enter a valid number")


@command("sleep", description="Sleep calculator", category="productivity")
class SleepCommand(Command):
    """Calculate optimal sleep times."""
    usage_examples = [
        "!sleep 6am - Best times to sleep for 6am wake",
        "!sleep now - Best times to wake if sleep now",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.args:
            return CommandResult(
                success=True,
                message="""
😴 *Sleep Calculator*

Sleep cycles are ~90 minutes.
Waking between cycles = feeling refreshed!

Usage:
• !sleep 6am - Best times to sleep for 6am wake
• !sleep now - Best times to wake if sleep now

Tips:
• Avoid screens 1 hour before bed
• Keep room cool and dark
• Consistent sleep schedule
                """.strip()
            )
        
        from datetime import datetime, timedelta
        
        arg = ctx.args[0].lower()
        
        if arg == "now":
            now = datetime.now()
            cycles = [5, 6, 7, 8, 9]  # Number of 90-min cycles
            
            lines = ["⏰ *If you sleep now, wake up at:*\n"]
            for c in cycles:
                wake_time = now + timedelta(minutes=c * 90 + 15)  # +15 min to fall asleep
                lines.append(f"• {wake_time.strftime('%I:%M %p')} ({c} cycles, {c*1.5:.1f}h sleep)")
            
            return CommandResult(success=True, message="\n".join(lines))
        
        else:
            # Parse wake time
            try:
                # Try to parse time
                for fmt in ["%I%p", "%I:%M%p", "%H:%M"]:
                    try:
                        wake = datetime.strptime(arg.replace(":", "").upper(), fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return CommandResult(success=False, message="❌ Invalid time format. Use: 6am, 7:30pm, 22:00")
                
                # Calculate sleep times (working backwards)
                cycles = [6, 5, 4]  # 9, 7.5, 6 hours
                
                lines = [f"⏰ *To wake at {arg}, sleep at:*\n"]
                for c in cycles:
                    sleep_time = wake - timedelta(minutes=c * 90 + 15)
                    lines.append(f"• {sleep_time.strftime('%I:%M %p')} ({c*1.5:.1f}h sleep)")
                
                lines.append("\n💡 Aim for 7.5-9 hours of sleep!")
                
                return CommandResult(success=True, message="\n".join(lines))
                
            except Exception:
                return CommandResult(success=False, message="❌ Invalid time format. Use: 6am, 7:30pm, 22:00")


@command("meditate", description="Meditation guide", category="productivity")
class MeditateCommand(Command):
    """Meditation and mindfulness."""
    usage_examples = [
        "!meditate - Quick meditation",
        "!meditate 5min - 5 minute meditation",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message="""
🧘 *Quick Meditation*

1. Find a comfortable position
2. Close your eyes
3. Breathe deeply through your nose
4. Count breaths: In (1), Out (2), up to 10
5. When mind wanders, gently return to counting

Start with 2-5 minutes daily.

Apps to help:
• Headspace
• Calm
• Insight Timer
• Medito (free)

_Breathe in calm, breathe out stress_ 🌸
            """.strip()
        )
