"""Bundled mock data for the Helpdesk Agent.

Contains sample support tickets and knowledge base articles used when
data_source is set to "bundled" (the default).
"""

from typing import Any, Dict, List

TICKETS: List[Dict[str, Any]] = [
    {
        "id": "TKT-001",
        "slug": "login-2fa-not-working",
        "summary": "Two-factor authentication codes are rejected at login",
        "description": (
            "User reports that TOTP codes from Google Authenticator are rejected. "
            "Issue occurs on both mobile and desktop browsers. Account is locked after "
            "5 failed attempts. Workaround: request a backup code via email."
        ),
        "status": "open",
        "tags": ["auth", "2fa", "totp", "login"],
    },
    {
        "id": "TKT-002",
        "slug": "billing-invoice-not-received",
        "summary": "Monthly invoice email not delivered",
        "description": (
            "Customer did not receive the invoice for the current billing cycle. "
            "Payment was processed successfully. Invoice is visible in the billing portal "
            "but the automated email was not sent. Check spam filters and email delivery logs."
        ),
        "status": "open",
        "tags": ["billing", "invoice", "email"],
    },
    {
        "id": "TKT-003",
        "slug": "data-export-timeout",
        "summary": "CSV data export times out for large datasets",
        "description": (
            "Exporting more than 50,000 records via the dashboard causes a 504 gateway timeout. "
            "Smaller exports (< 10,000 records) work correctly. Workaround: use the API with "
            "pagination or split exports by date range."
        ),
        "status": "in_progress",
        "tags": ["export", "csv", "performance", "timeout"],
    },
    {
        "id": "TKT-004",
        "slug": "password-reset-link-expired",
        "summary": "Password reset links expire too quickly",
        "description": (
            "Users report that password reset links expire within minutes, making it impossible "
            "to reset passwords on mobile where switching between email and browser is slow. "
            "Current expiry is 15 minutes; increasing to 60 minutes is under consideration."
        ),
        "status": "open",
        "tags": ["auth", "password", "reset", "expiry"],
    },
    {
        "id": "TKT-005",
        "slug": "api-rate-limit-unexpected",
        "summary": "API rate limit hit unexpectedly on free tier",
        "description": (
            "Developer reports hitting the 1,000 requests/day API limit within a few hours "
            "of normal usage. Investigation shows certain SDKs retry on transient errors without "
            "exponential backoff, causing rapid request multiplication."
        ),
        "status": "resolved",
        "tags": ["api", "rate-limit", "sdk", "free-tier"],
    },
]

ARTICLES: List[Dict[str, Any]] = [
    {
        "id": "KB-001",
        "title": "Setting Up Two-Factor Authentication",
        "content": (
            "Two-factor authentication (2FA) adds a second layer of security to your account. "
            "We support TOTP authenticator apps (Google Authenticator, Authy, 1Password) and "
            "SMS codes. To enable 2FA: go to Account Settings > Security > Enable 2FA. "
            "Scan the QR code with your authenticator app and enter the 6-digit code to confirm. "
            "Save your backup codes in a secure location — these are used if you lose access to your app."
        ),
        "tags": ["auth", "2fa", "security", "setup"],
    },
    {
        "id": "KB-002",
        "title": "Troubleshooting Login Issues",
        "content": (
            "Common login problems and solutions: "
            "1. Wrong password — use 'Forgot Password' to reset. "
            "2. 2FA codes rejected — ensure your device clock is synchronized (TOTP is time-sensitive). "
            "3. Account locked — contact support after 5 failed attempts. "
            "4. Browser issues — try clearing cookies or using incognito mode. "
            "5. SSO problems — verify your organization's SSO configuration with your admin."
        ),
        "tags": ["auth", "login", "troubleshooting", "2fa"],
    },
    {
        "id": "KB-003",
        "title": "Understanding Your Invoice",
        "content": (
            "Invoices are generated on the 1st of each month and emailed to the billing contact. "
            "Each invoice includes: subscription plan, usage charges, taxes, and payment method. "
            "Invoices are also available in the Billing Portal under Account > Billing > Invoices. "
            "If you did not receive an invoice, check your spam folder or verify the billing email "
            "address under Account Settings > Billing > Billing Contact."
        ),
        "tags": ["billing", "invoice", "email"],
    },
    {
        "id": "KB-004",
        "title": "Exporting Your Data",
        "content": (
            "You can export your data as CSV from the dashboard or via API. "
            "Dashboard exports: navigate to Reports > Export, select date range and fields, click Export. "
            "For large datasets (> 10,000 records), we recommend using the API with pagination: "
            "GET /api/v1/records?page=1&limit=1000. "
            "Rate limits apply to API exports. For very large exports, contact support for a bulk export."
        ),
        "tags": ["export", "csv", "api", "data"],
    },
    {
        "id": "KB-005",
        "title": "Resetting Your Password",
        "content": (
            "To reset your password: click 'Forgot Password' on the login page, enter your email address, "
            "and check your inbox for a reset link (valid for 60 minutes). "
            "If you do not receive the email within 5 minutes, check your spam folder. "
            "For security, reset links are single-use. If the link has expired, request a new one. "
            "If you have 2FA enabled, you will need your authenticator app after setting a new password."
        ),
        "tags": ["auth", "password", "reset"],
    },
    {
        "id": "KB-006",
        "title": "API Rate Limits",
        "content": (
            "Rate limits by plan: Free — 1,000 requests/day; Starter — 10,000 requests/day; "
            "Pro — 100,000 requests/day; Enterprise — custom. "
            "Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset. "
            "When you exceed the limit, the API returns HTTP 429. "
            "Best practices: implement exponential backoff, cache responses, and batch requests. "
            "Monitor usage in the Developer Dashboard under API > Usage."
        ),
        "tags": ["api", "rate-limit", "limits"],
    },
    {
        "id": "KB-007",
        "title": "Managing Billing and Subscriptions",
        "content": (
            "To update your billing plan: Account > Billing > Change Plan. "
            "Upgrades take effect immediately; downgrades apply at the next billing cycle. "
            "To update payment method: Account > Billing > Payment Methods > Add New. "
            "Cancellation: Account > Billing > Cancel Subscription. "
            "Your data is retained for 30 days after cancellation. "
            "For billing disputes, contact billing@support.example.com."
        ),
        "tags": ["billing", "subscription", "payment"],
    },
    {
        "id": "KB-008",
        "title": "API Authentication",
        "content": (
            "API requests are authenticated using API keys. "
            "Generate an API key: Developer Settings > API Keys > Create Key. "
            "Include the key in requests: Authorization: Bearer <your-api-key>. "
            "Keep keys secret — do not commit them to source control. "
            "Rotate keys regularly; revoke compromised keys immediately from the Developer Dashboard. "
            "API keys do not expire but can be revoked at any time."
        ),
        "tags": ["api", "auth", "security", "api-key"],
    },
    {
        "id": "KB-009",
        "title": "Account Security Best Practices",
        "content": (
            "Protect your account: enable 2FA, use a strong unique password, review active sessions regularly. "
            "Active sessions: Account > Security > Active Sessions — revoke any unrecognized sessions. "
            "Security alerts: Account > Notifications > Security Alerts — enable email alerts for logins "
            "from new devices. If you suspect unauthorized access, change your password and revoke all "
            "sessions immediately. Contact security@support.example.com for security incidents."
        ),
        "tags": ["security", "auth", "2fa", "account"],
    },
    {
        "id": "KB-010",
        "title": "Contacting Support",
        "content": (
            "Support channels: "
            "Live chat: available weekdays 9am–6pm UTC via the Help button in the dashboard. "
            "Email: support@example.com — response within 24 hours on business days. "
            "Emergency (outages): status.example.com and @ExampleStatus on Twitter. "
            "Enterprise customers have dedicated Slack support and a named account manager. "
            "When contacting support, include your account email, ticket/error IDs, and steps to reproduce."
        ),
        "tags": ["support", "contact", "help"],
    },
]


def build_article_index() -> Dict[str, Dict[str, Any]]:
    """Return a dict of articles keyed by article ID."""
    return {article["id"]: article for article in ARTICLES}


def build_ticket_index() -> Dict[str, Dict[str, Any]]:
    """Return a dict of tickets keyed by both ticket ID and slug."""
    index: Dict[str, Dict[str, Any]] = {}
    for ticket in TICKETS:
        index[ticket["id"]] = ticket
        index[ticket["slug"]] = ticket
    return index
