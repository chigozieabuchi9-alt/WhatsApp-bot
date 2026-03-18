"""
Weather-related commands.
"""
import httpx

from commands.base import Command, CommandContext, CommandResult, command
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@command("weather", description="Get weather information", aliases=["w"], min_args=1, category="weather")
class WeatherCommand(Command):
    usage_examples = [
        "!weather London",
        "!weather New York, US",
        "!w Tokyo",
    ]
    cooldown_seconds = 5
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not settings.OPENWEATHERMAP_API_KEY:
            return CommandResult(
                success=False,
                message="⚠️ Weather service is not configured. Please contact the administrator."
            )
        
        city = ctx.args_str
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": city,
                        "appid": settings.OPENWEATHERMAP_API_KEY,
                        "units": "metric",
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    return CommandResult(
                        success=False,
                        message=f"❌ City not found: {city}"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                weather_desc = data["weather"][0]["description"].title()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                city_name = data["name"]
                country = data["sys"]["country"]
                
                # Weather emoji mapping
                weather_emojis = {
                    "clear": "☀️",
                    "cloud": "☁️",
                    "rain": "🌧️",
                    "drizzle": "🌦️",
                    "thunder": "⛈️",
                    "snow": "🌨️",
                    "mist": "🌫️",
                    "fog": "🌫️",
                }
                
                emoji = "🌡️"
                for key, emj in weather_emojis.items():
                    if key in weather_desc.lower():
                        emoji = emj
                        break
                
                message = f"""
{emoji} *Weather in {city_name}, {country}*

🌡️ Temperature: {temp:.1f}°C (feels like {feels_like:.1f}°C)
☁️ Condition: {weather_desc}
💧 Humidity: {humidity}%
💨 Wind: {wind_speed} m/s
                """.strip()
                
                return CommandResult(success=True, message=message)
                
        except httpx.HTTPError as e:
            logger.error("weather_api_error", error=str(e))
            return CommandResult(
                success=False,
                message="❌ Failed to fetch weather data. Please try again later."
            )


@command("forecast", description="Get 5-day weather forecast", min_args=1, category="weather")
class ForecastCommand(Command):
    usage_examples = [
        "!forecast London",
        "!forecast Tokyo, JP",
    ]
    cooldown_seconds = 10
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        if not settings.OPENWEATHERMAP_API_KEY:
            return CommandResult(
                success=False,
                message="⚠️ Weather service is not configured."
            )
        
        city = ctx.args_str
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={
                        "q": city,
                        "appid": settings.OPENWEATHERMAP_API_KEY,
                        "units": "metric",
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    return CommandResult(
                        success=False,
                        message=f"❌ City not found: {city}"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                city_name = data["city"]["name"]
                country = data["city"]["country"]
                
                # Group by day (take one forecast per day at noon)
                daily_forecasts = []
                seen_days = set()
                
                for item in data["list"]:
                    date = item["dt_txt"].split()[0]
                    if date not in seen_days and "12:00" in item["dt_txt"]:
                        seen_days.add(date)
                        daily_forecasts.append(item)
                
                lines = [f"🌤️ *5-Day Forecast for {city_name}, {country}*\n"]
                
                for forecast in daily_forecasts[:5]:
                    date = forecast["dt_txt"].split()[0]
                    temp = forecast["main"]["temp"]
                    desc = forecast["weather"][0]["description"].title()
                    lines.append(f"📅 {date}: {temp:.1f}°C - {desc}")
                
                return CommandResult(success=True, message="\n".join(lines))
                
        except httpx.HTTPError as e:
            logger.error("forecast_api_error", error=str(e))
            return CommandResult(
                success=False,
                message="❌ Failed to fetch forecast data. Please try again later."
            )


@command("temp", description="Convert temperature", min_args=2, category="weather")
class TempConvertCommand(Command):
    usage_examples = [
        "!temp 32 F to C",
        "!temp 100 C to F",
        "!temp 20 C to K",
    ]
    
    async def execute(self, ctx: CommandContext) -> CommandResult:
        try:
            value = float(ctx.args[0])
            from_unit = ctx.args[1].upper()
            to_unit = ctx.args[3].upper() if len(ctx.args) > 3 else "C" if from_unit == "F" else "F"
            
            # Convert to Celsius first
            if from_unit == "F":
                celsius = (value - 32) * 5/9
            elif from_unit == "K":
                celsius = value - 273.15
            else:  # Celsius
                celsius = value
            
            # Convert from Celsius to target
            if to_unit == "F":
                result = celsius * 9/5 + 32
            elif to_unit == "K":
                result = celsius + 273.15
            else:
                result = celsius
            
            return CommandResult(
                success=True,
                message=f"🌡️ {value}°{from_unit} = *{result:.2f}°{to_unit}*"
            )
            
        except (ValueError, IndexError):
            return CommandResult(
                success=False,
                message="❌ Usage: !temp <value> <unit> to <target_unit>\nExample: !temp 32 F to C"
            )
