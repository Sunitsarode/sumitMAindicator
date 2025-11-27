"""
Notification System for Trading Dashboard
Supports Telegram and Ntfy
"""
import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages notifications via Telegram or Ntfy"""
    
    def __init__(self):
        self.enabled = os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.method = os.getenv('NOTIFICATION_METHOD', 'telegram')
        
        # Telegram config
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Ntfy config
        self.ntfy_endpoint = os.getenv('NTFY_ENDPOINT')
        
        if self.enabled:
            if self.method == 'telegram' and (not self.telegram_token or not self.telegram_chat_id):
                logger.warning("Telegram enabled but missing credentials")
                self.enabled = False
            elif self.method == 'ntfy' and not self.ntfy_endpoint:
                logger.warning("Ntfy enabled but missing endpoint")
                self.enabled = False
    
    def send_trade_notification(self, symbol, direction, action, price, pl=None, reason=None, details=None):
        """
        Send trade notification
        
        Args:
            symbol: Trading symbol
            direction: LONG/SHORT
            action: OPENED/CLOSED
            price: Entry/Exit price
            pl: Profit/Loss (for CLOSED)
            reason: Exit reason (for CLOSED)
            details: Additional details dict
        """
        if not self.enabled:
            return
        
        try:
            # Format message
            emoji = "📈" if direction == "LONG" else "📉"
            action_emoji = "🟢" if action == "OPENED" else ("✅" if pl and pl > 0 else "❌")
            
            message = f"{action_emoji} {action} {emoji} {direction}\n"
            message += f"Symbol: {symbol}\n"
            message += f"Price: ${price:.2f}\n"
            
            if action == "CLOSED" and pl is not None:
                pl_emoji = "💰" if pl > 0 else "💸"
                message += f"{pl_emoji} P/L: {pl:+.2f} pts\n"
                if reason:
                    message += f"Reason: {reason}\n"
            
            if details:
                message += "\nIndicators:\n"
                if 'rsi' in details:
                    message += f"RSI: {details['rsi']:.0f}\n"
                if 'supertrend' in details:
                    message += f"ST: {details['supertrend']:.0f}\n"
                if 'buy_signal_count' in details:
                    message += f"BUY: {details['buy_signal_count']}/18\n"
                if 'sell_signal_count' in details:
                    message += f"SELL: {details['sell_signal_count']}/18\n"
            
            message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
            
            # Send notification
            if self.method == 'telegram':
                self._send_telegram(message)
            elif self.method == 'ntfy':
                self._send_ntfy(message, f"{action} {direction}")
            
            logger.info(f"Notification sent: {action} {direction} {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _send_telegram(self, message):
        """Send via Telegram"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
    
    def _send_ntfy(self, message, title):
        """Send via Ntfy"""
        response = requests.post(
            self.ntfy_endpoint,
            data=message.encode('utf-8'),
            headers={'Title': title},
            timeout=10
        )
        response.raise_for_status()
    
    def send_error_alert(self, error_msg):
        """Send error alert"""
        if not self.enabled:
            return
        
        try:
            message = f"⚠️ TRADING ERROR\n{error_msg}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
            
            if self.method == 'telegram':
                self._send_telegram(message)
            elif self.method == 'ntfy':
                self._send_ntfy(message, "Trading Error")
                
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")

# Global instance
notification_manager = NotificationManager()
