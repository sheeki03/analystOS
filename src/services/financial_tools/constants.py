"""
Constants for SEC filing items and other tool-related data.

Migrated from Dexter's tools/finance/constants.ts
"""

from typing import Dict


# 10-K filing items (annual reports)
ITEMS_10K_MAP: Dict[str, str] = {
    'Item-1': 'Business',
    'Item-1A': 'Risk Factors',
    'Item-1B': 'Unresolved Staff Comments',
    'Item-2': 'Properties',
    'Item-3': 'Legal Proceedings',
    'Item-4': 'Mine Safety Disclosures',
    'Item-5': "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    'Item-6': '[Reserved]',
    'Item-7': "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    'Item-7A': 'Quantitative and Qualitative Disclosures About Market Risk',
    'Item-8': 'Financial Statements and Supplementary Data',
    'Item-9': 'Changes in and Disagreements With Accountants on Accounting and Financial Disclosure',
    'Item-9A': 'Controls and Procedures',
    'Item-9B': 'Other Information',
    'Item-10': 'Directors, Executive Officers and Corporate Governance',
    'Item-11': 'Executive Compensation',
    'Item-12': 'Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters',
    'Item-13': 'Certain Relationships and Related Transactions, and Director Independence',
    'Item-14': 'Principal Accounting Fees and Services',
    'Item-15': 'Exhibits, Financial Statement Schedules',
    'Item-16': 'Form 10-K Summary',
}

# 10-Q filing items (quarterly reports)
ITEMS_10Q_MAP: Dict[str, str] = {
    'Item-1': 'Financial Statements',
    'Item-2': "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    'Item-3': 'Quantitative and Qualitative Disclosures About Market Risk',
    'Item-4': 'Controls and Procedures',
}


def format_items_description(items_map: Dict[str, str]) -> str:
    """
    Format items map as description string for tool schemas.

    Args:
        items_map: Dictionary of item codes to descriptions

    Returns:
        Formatted string with each item on a new line
    """
    return '\n'.join(
        f"  - {item}: {description}"
        for item, description in items_map.items()
    )
