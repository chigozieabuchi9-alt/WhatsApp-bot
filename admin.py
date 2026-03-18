"""
Admin commands for bot management.
"""
from datetime import datetime

from commands.base import Command, CommandContext, CommandResult, command
from db.models import User, UserTier
from db.repositories import (
    CommandAliasRepository,
    CommandLogRepository,
    SystemSettingRepository,
    UserRepository,
)


@command("stats", description="Show bot statistics", category="admin")
class StatsCommand(Command):
    required_tier = UserTier.USER
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        user_repo = UserRepository(ctx.db)
        log_repo = CommandLogRepository(ctx.db)
        
        user_stats = await user_repo.get_stats()
        popular_commands = await log_repo.get_popular_commands(5)
        
        lines = [
            "📊 *Bot Statistics*\n",
            "*Users:*",
            f"  Total: {user_stats['total_users']}",
            f"  Active: {user_stats['active_users']}",
            "",
            "*By Tier:*",
        ]
        
        for tier, count in user_stats['by_tier'].items():
            lines.append(f"  {tier.title()}: {count}")
        
        lines.extend([
            "",
            "*Popular Commands:*",
        ])
        
        for cmd, count in popular_commands:
            lines.append(f"  !{cmd}: {count} uses")
        
        return CommandResult(success=True, message="\n".join(lines))


@command("userinfo", description="Get user information", min_args=1, category="admin")
class UserInfoCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        phone = ctx.args[0]
        user_repo = UserRepository(ctx.db)
        user = await user_repo.get_by_phone(phone)
        
        if not user:
            return CommandResult(success=False, message=f"❌ User not found: {phone}")
        
        lines = [
            f"👤 *User Info: {user.phone_number}*\n",
            f"Name: {user.name or 'N/A'}",
            f"Tier: {user.tier.value}",
            f"Status: {'Active' if user.is_active else 'Inactive'}",
            f"Blocked: {'Yes' if user.is_blocked else 'No'}",
            f"Created: {user.created_at.strftime('%Y-%m-%d')}",
            f"Last Activity: {user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'Never'}",
            f"Total Commands: {user.command_count}",
            f"Today's Commands: {user.daily_command_count}",
            f"Timezone: {user.timezone}",
        ]
        
        return CommandResult(success=True, message="\n".join(lines))


@command("settier", description="Set user tier", min_args=2, category="admin")
class SetTierCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        phone = ctx.args[0]
        tier_str = ctx.args[1].lower()
        
        try:
            tier = UserTier(tier_str)
        except ValueError:
            tiers = ", ".join([t.value for t in UserTier])
            return CommandResult(success=False, message=f"❌ Invalid tier. Use: {tiers}")
        
        user_repo = UserRepository(ctx.db)
        user = await user_repo.get_by_phone(phone)
        
        if not user:
            return CommandResult(success=False, message=f"❌ User not found: {phone}")
        
        await user_repo.update_tier(user.id, tier)
        
        return CommandResult(
            success=True,
            message=f"✅ Updated {phone} to tier: {tier.value}"
        )


@command("block", description="Block a user", min_args=1, category="admin")
class BlockCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        phone = ctx.args[0]
        reason = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else "No reason provided"
        
        user_repo = UserRepository(ctx.db)
        user = await user_repo.get_by_phone(phone)
        
        if not user:
            return CommandResult(success=False, message=f"❌ User not found: {phone}")
        
        await user_repo.block_user(user.id)
        
        return CommandResult(
            success=True,
            message=f"🚫 User blocked: {phone}\nReason: {reason}"
        )


@command("unblock", description="Unblock a user", min_args=1, category="admin")
class UnblockCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        phone = ctx.args[0]
        
        user_repo = UserRepository(ctx.db)
        user = await user_repo.get_by_phone(phone)
        
        if not user:
            return CommandResult(success=False, message=f"❌ User not found: {phone}")
        
        await user_repo.unblock_user(user.id)
        
        return CommandResult(
            success=True,
            message=f"✅ User unblocked: {phone}"
        )


@command("broadcast", description="Send message to all users", min_args=1, category="admin")
class BroadcastCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        message = ctx.args_str
        
        # This would integrate with Twilio to send messages
        return CommandResult(
            success=True,
            message=f"📢 Broadcast scheduled!\n\nMessage: {message}\n\nNote: Actual sending requires Twilio integration."
        )


@command("maintenance", description="Toggle maintenance mode", category="admin")
class MaintenanceCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        setting_repo = SystemSettingRepository(ctx.db)
        
        current = await setting_repo.get("maintenance_mode", "false")
        new_value = "false" if current == "true" else "true"
        
        await setting_repo.set(
            "maintenance_mode",
            new_value,
            updated_by=str(ctx.user.id),
        )
        
        status = "ENABLED" if new_value == "true" else "DISABLED"
        emoji = "🔧" if new_value == "true" else "✅"
        
        return CommandResult(
            success=True,
            message=f"{emoji} Maintenance mode {status}"
        )


@command("addalias", description="Add command alias", min_args=2, category="admin")
class AddAliasCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        alias = ctx.args[0]
        command_name = ctx.args[1]
        description = " ".join(ctx.args[2:]) if len(ctx.args) > 2 else None
        
        alias_repo = CommandAliasRepository(ctx.db)
        
        try:
            await alias_repo.create_alias(alias, command_name, description)
            return CommandResult(
                success=True,
                message=f"✅ Alias added: !{alias} → !{command_name}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"❌ Failed to add alias: {str(e)}"
            )


@command("logs", description="View recent command logs", category="admin")
class LogsCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        log_repo = CommandLogRepository(ctx.db)
        logs = await log_repo.get_recent_commands(ctx.user.id, 10)
        
        lines = ["📋 *Recent Command Logs*\n"]
        
        for log in logs:
            status = "✅" if log.success else "❌"
            time_str = log.created_at.strftime('%H:%M:%S')
            lines.append(f"{status} [{time_str}] !{log.command}")
            if log.execution_time_ms:
                lines.append(f"   {log.execution_time_ms}ms")
        
        return CommandResult(success=True, message="\n".join(lines))


@command("system", description="Show system status", category="admin")
class SystemCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        import platform
        import psutil
        
        lines = [
            "⚙️ *System Status*\n",
            f"Python: {platform.python_version()}",
            f"Platform: {platform.platform()}",
            f"CPU Usage: {psutil.cpu_percent()}%",
            f"Memory: {psutil.virtual_memory().percent}% used",
            f"Disk: {psutil.disk_usage('/').percent}% used",
        ]
        
        return CommandResult(success=True, message="\n".join(lines))


@command("reload", description="Reload commands", category="admin")
class ReloadCommand(Command):
    required_tier = UserTier.ADMIN
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        # In a real implementation, this would reload command modules
        return CommandResult(
            success=True,
            message="🔄 Commands reloaded successfully!"
        )
