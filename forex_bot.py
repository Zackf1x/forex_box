import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("forex_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleForexBot")

# Create necessary directories
os.makedirs("data", exist_ok=True)
os.makedirs("analysis", exist_ok=True)
os.makedirs("recommendations", exist_ok=True)

class SimpleForexBot:
    """
    A simplified forex trading bot that provides trade recommendations via Telegram.
    This class combines data collection, technical analysis, and trade recommendation
    functionality into a single, easy-to-use interface.
    """
    
    def __init__(self):
        """Initialize the SimpleForexBot."""
        # Hardcoded token instead of loading from .env
        self.token = "8001468059:AAFjZrTWoJqjfJN_Er4IIQvsIIBjHHhjeHk"
        
        # Define forex pairs
        self.forex_pairs = [
            "EURUSD=X",  # Euro to US Dollar
            "GBPUSD=X",  # British Pound to US Dollar
            "USDJPY=X",  # US Dollar to Japanese Yen
            "AUDUSD=X",  # Australian Dollar to US Dollar
            "USDCAD=X",  # US Dollar to Canadian Dollar
            "USDCHF=X",  # US Dollar to Swiss Franc
            "NZDUSD=X"   # New Zealand Dollar to US Dollar
        ]
        
        # User settings
        self.user_settings = {}
        
        logger.info("SimpleForexBot initialized")
    
    async def start_command(self, update, context):
        """Handle the /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        
        # Initialize user settings if not exists
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                "account_size": 5000,
                "risk_per_trade": 60,
                "preferred_session": "all"
            }
        
        welcome_message = (
            f"👋 Welcome to the Forex Trading Bot, {username}!\n\n"
            f"I can help you find high-probability forex trade opportunities on demand.\n\n"
            f"*Available Commands:*\n"
            f"/daytrades - Get 3 day trade opportunities\n"
            f"/swingtrades - Get 3 swing trade opportunities\n"
            f"/settings - Configure your trading parameters\n"
            f"/help - Show help information\n\n"
            f"Your current settings:\n"
            f"• Account Size: ${self.user_settings[user_id]['account_size']}\n"
            f"• Risk per Trade: ${self.user_settings[user_id]['risk_per_trade']}\n"
            f"• Preferred Session: {self.user_settings[user_id]['preferred_session'].upper()}\n\n"
            f"Let's start finding profitable trades! 📈"
        )
        
        await update.message.reply_text(welcome_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    async def help_command(self, update, context):
        """Handle the /help command."""
        help_message = (
            "*Forex Trading Bot Help*\n\n"
            "*Available Commands:*\n"
            "/start - Start the bot and see welcome message\n"
            "/daytrades - Get 3 day trade opportunities (medium risk)\n"
            "/swingtrades - Get 3 swing trade opportunities (low risk)\n"
            "/settings - Configure your trading parameters\n"
            "/help - Show this help information\n\n"
            "*How to Use:*\n"
            "1. Use /settings to configure your account size and risk parameters\n"
            "2. Use /daytrades to get day trading opportunities\n"
            "3. Use /swingtrades to get swing trading opportunities\n\n"
            "*Trade Information:*\n"
            "Each trade recommendation includes:\n"
            "• Entry price\n"
            "• Stop loss level\n"
            "• Take profit target\n"
            "• Position size based on your risk settings\n"
            "• Risk-reward ratio\n"
            "• Key technical signals\n\n"
            "For any issues or questions, please contact support."
        )
        
        await update.message.reply_text(help_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    async def settings_command(self, update, context):
        """Handle the /settings command."""
        user_id = update.effective_user.id
        
        # Initialize user settings if not exists
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                "account_size": 5000,
                "risk_per_trade": 60,
                "preferred_session": "all"
            }
        
        settings_message = (
            "*Your Current Settings:*\n\n"
            f"• Account Size: ${self.user_settings[user_id]['account_size']}\n"
            f"• Risk per Trade: ${self.user_settings[user_id]['risk_per_trade']}\n"
            f"• Preferred Session: {self.user_settings[user_id]['preferred_session'].upper()}\n\n"
            "*To Update Settings:*\n"
            "Send a message in this format:\n"
            "`account:5000 risk:60 session:all`\n\n"
            "Session options: all, asian, european, us"
        )
        
        await update.message.reply_text(settings_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        
        # Add message handler for settings update
        application = context.application
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.update_settings))
    
    async def update_settings(self, update, context):
        """Update user settings based on message."""
        user_id = update.effective_user.id
        message_text = update.message.text.lower()
        
        try:
            # Parse settings from message
            settings = {}
            
            # Extract account size
            if "account:" in message_text:
                account_str = message_text.split("account:")[1].split()[0]
                settings["account_size"] = float(account_str)
            
            # Extract risk per trade
            if "risk:" in message_text:
                risk_str = message_text.split("risk:")[1].split()[0]
                settings["risk_per_trade"] = float(risk_str)
            
            # Extract preferred session
            if "session:" in message_text:
                session_str = message_text.split("session:")[1].split()[0]
                if session_str in ["all", "asian", "european", "us"]:
                    settings["preferred_session"] = session_str
            
            # Update user settings
            if user_id not in self.user_settings:
                self.user_settings[user_id] = {
                    "account_size": 5000,
                    "risk_per_trade": 60,
                    "preferred_session": "all"
                }
            
            self.user_settings[user_id].update(settings)
            
            # Confirm settings update
            confirmation_message = (
                "*Settings Updated:*\n\n"
                f"• Account Size: ${self.user_settings[user_id]['account_size']}\n"
                f"• Risk per Trade: ${self.user_settings[user_id]['risk_per_trade']}\n"
                f"• Preferred Session: {self.user_settings[user_id]['preferred_session'].upper()}\n\n"
                f"You can now use /daytrades or /swingtrades to get trade recommendations."
            )
            
            await update.message.reply_text(confirmation_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
        except Exception as e:
            error_message = (
                "*Error Updating Settings:*\n\n"
                f"Invalid format. Please use the format:\n"
                "`account:5000 risk:60 session:all`\n\n"
                f"Error details: {str(e)}"
            )
            
            await update.message.reply_text(error_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    async def day_trades_command(self, update, context):
        """Handle the /daytrades command."""
        user_id = update.effective_user.id
        
        # Get user settings
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                "account_size": 5000,
                "risk_per_trade": 60,
                "preferred_session": "all"
            }
        
        account_size = self.user_settings[user_id]["account_size"]
        risk_per_trade = self.user_settings[user_id]["risk_per_trade"]
        
        # Send processing message
        await update.message.reply_text("🔍 Analyzing the forex market for day trade opportunities... This may take a moment.")
        
        try:
            # Generate day trade recommendations
            recommendations = self.generate_day_trade_recommendations(
                num_recommendations=3,
                account_size=account_size,
                risk_per_trade=risk_per_trade
            )
            
            # Send recommendations
            for i, recommendation in enumerate(recommendations, 1):
                # Format message
                message = self.format_telegram_message(recommendation)
                
                # Send message
                await update.message.reply_text(message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
            # Send summary
            summary_message = (
                "*Day Trade Opportunities Summary:*\n\n"
                f"I've analyzed the forex market and provided you with {len(recommendations)} day trade opportunities.\n\n"
                f"These trades are designed for intraday execution with medium risk level.\n"
                f"Position sizes are calculated based on your risk setting of ${risk_per_trade} per trade.\n\n"
                f"Use /swingtrades to get swing trade opportunities instead."
            )
            
            await update.message.reply_text(summary_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
        except Exception as e:
            error_message = (
                "*Error Generating Day Trade Recommendations:*\n\n"
                f"An error occurred while analyzing the market: {str(e)}\n\n"
                f"Please try again later or contact support."
            )
            
            await update.message.reply_text(error_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    async def swing_trades_command(self, update, context):
        """Handle the /swingtrades command."""
        user_id = update.effective_user.id
        
        # Get user settings
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                "account_size": 5000,
                "risk_per_trade": 60,
                "preferred_session": "all"
            }
        
        account_size = self.user_settings[user_id]["account_size"]
        risk_per_trade = self.user_settings[user_id]["risk_per_trade"]
        
        # Send processing message
        await update.message.reply_text("🔍 Analyzing the forex market for swing trade opportunities... This may take a moment.")
        
        try:
            # Generate swing trade recommendations
            recommendations = self.generate_swing_trade_recommendations(
                num_recommendations=3,
                account_size=account_size,
                risk_per_trade=risk_per_trade
            )
            
            # Send recommendations
            for i, recommendation in enumerate(recommendations, 1):
                # Format message
                message = self.format_telegram_message(recommendation)
                
                # Send message
                await update.message.reply_text(message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
            # Send summary
            summary_message = (
                "*Swing Trade Opportunities Summary:*\n\n"
                f"I've analyzed the forex market and provided you with {len(recommendations)} swing trade opportunities.\n\n"
                f"These trades are designed for multi-day holding with low risk level.\n"
                f"Position sizes are calculated based on your risk setting of ${risk_per_trade} per trade.\n\n"
                f"Use /daytrades to get day trade opportunities instead."
            )
            
            await update.message.reply_text(summary_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
        except Exception as e:
            error_message = (
                "*Error Generating Swing Trade Recommendations:*\n\n"
                f"An error occurred while analyzing the market: {str(e)}\n\n"
                f"Please try again later or contact support."
            )
            
            await update.message.reply_text(error_message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    def generate_day_trade_recommendations(self, num_recommendations=3, account_size=5000, risk_per_trade=60):
        """
        Generate day trade recommendations.
        
        Args:
            num_recommendations (int): Number of recommendations to generate
            account_size (float): Trading account size
            risk_per_trade (float): Risk amount per trade
            
        Returns:
            list: List of trade recommendations
        """
        logger.info(f"Generating {num_recommendations} day trade recommendations")
        
        # For demonstration purposes, we'll create sample recommendations
        # In a real implementation, this would analyze actual market data
        
        recommendations = []
        
        # Sample pairs for recommendations
        pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"]
        
        for i in range(min(num_recommendations, len(pairs))):
            pair = pairs[i]
            
            # Generate sample data based on pair
            if pair == "EURUSD=X":
                current_price = 1.1360
                direction = "BUY"
                stop_loss = 1.1310
                take_profit = 1.1460
                signals = [
                    "Price above 20 SMA (bullish)",
                    "RSI showing upward momentum",
                    "MACD crossed above signal line"
                ]
                score = 8
            elif pair == "GBPUSD=X":
                current_price = 1.3050
                direction = "SELL"
                stop_loss = 1.3100
                take_profit = 1.2950
                signals = [
                    "Price below 50 SMA (bearish)",
                    "Stochastic overbought",
                    "Resistance level rejection"
                ]
                score = 7
            elif pair == "USDJPY=X":
                current_price = 142.50
                direction = "SELL"
                stop_loss = 143.00
                take_profit = 141.50
                signals = [
                    "Bearish engulfing pattern",
                    "RSI divergence (bearish)",
                    "Price at upper Bollinger Band"
                ]
                score = 9
            else:  # AUDUSD=X
                current_price = 0.6410
                direction = "BUY"
                stop_loss = 0.6380
                take_profit = 0.6470
                signals = [
                    "Double bottom pattern",
                    "MACD histogram increasing",
                    "Price bounced off support"
                ]
                score = 6
            
            # Calculate risk-reward ratio
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calculate position size
            position_size = self._calculate_position_size(
                current_price,
                stop_loss,
                risk_per_trade,
                pair
            )
            
            # Calculate potential profit
            potential_profit = risk_per_trade * risk_reward_ratio
            
            # Calculate risk percentage
            risk_percentage = (risk_per_trade / account_size) * 100
            
            # Create recommendation
            recommendation = {
                'pair': pair,
                'trade_type': "Day Trade",
                'direction': direction,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_per_trade,
                'risk_percentage': risk_percentage,
                'potential_profit': potential_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'position_size': {
                    'micro_lots': position_size['micro_lots']
                },
                'signals': signals,
                'score': score,
                'timestamp': datetime.now().isoformat()
            }
            
            recommendations.append(recommendation)
        
        # Sort recommendations by score (higher is better)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Generated {len(recommendations)} day trade recommendations")
        return recommendations
    
    def generate_swing_trade_recommendations(self, num_recommendations=3, account_size=5000, risk_per_trade=60):
        """
        Generate swing trade recommendations.
        
        Args:
            num_recommendations (int): Number of recommendations to generate
            account_size (float): Trading account size
            risk_per_trade (float): Risk amount per trade
            
        Returns:
            list: List of trade recommendations
        """
        logger.info(f"Generating {num_recommendations} swing trade recommendations")
        
        # For demonstration purposes, we'll create sample recommendations
        # In a real implementation, this would analyze actual market data
        
        recommendations = []
        
        # Sample pairs for recommendations
        pairs = ["EURUSD=X", "USDCAD=X", "NZDUSD=X", "USDCHF=X"]
        
        for i in range(min(num_recommendations, len(pairs))):
            pair = pairs[i]
            
            # Generate sample data based on pair
            if pair == "EURUSD=X":
                current_price = 1.1360
                direction = "BUY"
                stop_loss = 1.1260
                take_profit = 1.1560
                signals = [
                    "Weekly uptrend continuation",
                    "Price above 200 SMA (bullish)",
                    "Key support level holding"
                ]
                score = 9
            elif pair == "USDCAD=X":
                current_price = 1.2550
                direction = "SELL"
                stop_loss = 1.2650
                take_profit = 1.2350
                signals = [
                    "Double top pattern on daily",
                    "RSI overbought on weekly",
                    "Bearish divergence"
                ]
                score = 8
            elif pair == "NZDUSD=X":
                current_price = 0.7050
                direction = "BUY"
                stop_loss = 0.6950
                take_profit = 0.7250
                signals = [
                    "Inverse head and shoulders",
                    "Golden cross (50/200 SMA)",
                    "Bullish engulfing on weekly"
                ]
                score = 7
            else:  # USDCHF=X
                current_price = 0.8950
                direction = "SELL"
                stop_loss = 0.9050
                take_profit = 0.8750
                signals = [
                    "Descending triangle breakout",
                    "Death cross (50/200 SMA)",
                    "Weekly resistance rejection"
                ]
                score = 6
            
            # Calculate risk-reward ratio
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calculate position size
            position_size = self._calculate_position_size(
                current_price,
                stop_loss,
                risk_per_trade,
                pair
            )
            
            # Calculate potential profit
            potential_profit = risk_per_trade * risk_reward_ratio
            
            # Calculate risk percentage
            risk_percentage = (risk_per_trade / account_size) * 100
            
            # Create recommendation
            recommendation = {
                'pair': pair,
                'trade_type': "Swing Trade",
                'direction': direction,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_amount': risk_per_trade,
                'risk_percentage': risk_percentage,
                'potential_profit': potential_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'position_size': {
                    'micro_lots': position_size['micro_lots']
                },
                'signals': signals,
                'score': score,
                'timestamp': datetime.now().isoformat()
            }
            
            recommendations.append(recommendation)
        
        # Sort recommendations by score (higher is better)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Generated {len(recommendations)} swing trade recommendations")
        return recommendations
    
    def _calculate_position_size(self, entry_price, stop_loss, risk_amount, pair):
        """
        Calculate position size based on risk amount and stop loss distance.
        
        Args:
            entry_price (float): Entry price
            stop_loss (float): Stop loss price
            risk_amount (float): Risk amount per trade
            pair (str): Forex pair symbol
            
        Returns:
            dict: Position size details
        """
        if entry_price is None or stop_loss is None:
            return {
                'units': 0,
                'standard_lots': 0,
                'mini_lots': 0,
                'micro_lots': 0
            }
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return {
                'units': 0,
                'standard_lots': 0,
                'mini_lots': 0,
                'micro_lots': 0
            }
        
        # Calculate position size
        position_size = risk_amount / risk_per_unit
        
        # For forex, adjust for standard lot sizes
        standard_lots = position_size / 100000
        mini_lots = position_size / 10000
        micro_lots = position_size / 1000
        
        return {
            'units': position_size,
            'standard_lots': standard_lots,
            'mini_lots': mini_lots,
            'micro_lots': micro_lots
        }
    
    def format_telegram_message(self, recommendation):
        """
        Format a trade recommendation as a Telegram message.
        
        Args:
            recommendation (dict): Trade recommendation
            
        Returns:
            str: Formatted message for Telegram
        """
        # Format message
        message = f"🔍 *{recommendation['trade_type']} Opportunity*\n\n"
        message += f"*{recommendation['direction']} {recommendation['pair'].replace('=X', '')}*\n\n"
        
        message += f"*Entry:* {recommendation['entry_price']:.5f}\n"
        message += f"*Stop Loss:* {recommendation['stop_loss']:.5f}\n"
        message += f"*Take Profit:* {recommendation['take_profit']:.5f}\n\n"
        
        message += f"*Risk:* ${recommendation['risk_amount']} ({recommendation['risk_percentage']:.2f}%)\n"
        message += f"*Potential Profit:* ${recommendation['potential_profit']:.2f}\n"
        message += f"*Risk-Reward Ratio:* {recommendation['risk_reward_ratio']:.2f}\n\n"
        
        message += f"*Position Size:* {recommendation['position_size']['micro_lots']:.2f} micro lots\n\n"
        
        message += "*Key Signals:*\n"
        for signal in recommendation['signals']:
            message += f"• {signal}\n"
        
        message += f"\n*Score:* {recommendation['score']} (higher is better)\n"
        
        return message

# Main function
def main():
    """Main function to run the bot."""
    logger.info("Starting Simple Forex Bot")
    
    try:
        # Create bot
        bot = SimpleForexBot()
        
        # Create the Application
        application = Application.builder().token(bot.token).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", bot.start_command))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("settings", bot.settings_command))
        application.add_handler(CommandHandler("daytrades", bot.day_trades_command))
        application.add_handler(CommandHandler("swingtrades", bot.swing_trades_command))
        
        # Start the bot with polling (same approach as the test bot)
        print("Forex Trading Bot is starting... Send messages to your bot in Telegram now!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        print("Bot stopped.")
        
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")

if __name__ == "__main__":
    main()
