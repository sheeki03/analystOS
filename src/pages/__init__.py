# Pages package for AI Research Agent

from .base_page import BasePage
from .interactive_research import InteractiveResearchPage
from .notion_automation import NotionAutomationPage
from .crypto_chatbot import CryptoChatbotPage
from .voice_cloner_page import VoiceClonerPage
from .market_intelligence import MarketIntelligencePage
from .financial_research import FinancialResearchPage

__all__ = [
    'BasePage',
    'InteractiveResearchPage',
    'NotionAutomationPage',
    'CryptoChatbotPage',
    'VoiceClonerPage',
    'MarketIntelligencePage',
    'FinancialResearchPage',
]
