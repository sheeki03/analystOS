"""
Session persistence utility for maintaining authentication state across page reloads.
Uses browser localStorage to store encrypted session data.
"""

import streamlit as st
import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import os

class SessionPersistence:
    """Handles session persistence using browser localStorage."""
    
    def __init__(self):
        # Generate a key based on environment or use a default
        # In production, this should be a proper secret key
        secret_key = os.getenv('SESSION_SECRET_KEY', 'default-session-key-change-in-production')
        key = hashlib.sha256(secret_key.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
        self.session_timeout_hours = 24  # Sessions expire after 24 hours
    
    def save_session(self, username: str, role: str, system_prompt: str) -> None:
        """Save session data to browser localStorage."""
        try:
            session_data = {
                'username': username,
                'role': role,
                'system_prompt': system_prompt,
                'timestamp': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=self.session_timeout_hours)).isoformat()
            }
            
            # Encrypt the session data
            encrypted_data = self._encrypt_data(session_data)
            
            # Save to localStorage using HTML/JavaScript
            html_code = f"""
            <script>
                localStorage.setItem('ai_research_session', '{encrypted_data}');
                console.log('Session saved to localStorage');
            </script>
            """
            st.components.v1.html(html_code, height=0)
            
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from browser localStorage."""
        try:
            # Create a unique key for this load attempt
            load_key = f"session_load_{datetime.now().timestamp()}"
            
            # JavaScript to retrieve session data and store in Streamlit
            html_code = f"""
            <script>
                const sessionData = localStorage.getItem('ai_research_session');
                if (sessionData) {{
                    // Store in a temporary element that Streamlit can read
                    const hiddenDiv = document.createElement('div');
                    hiddenDiv.id = 'session-data-{load_key}';
                    hiddenDiv.style.display = 'none';
                    hiddenDiv.textContent = sessionData;
                    document.body.appendChild(hiddenDiv);
                    console.log('Session data retrieved from localStorage');
                }} else {{
                    console.log('No session data found in localStorage');
                }}
            </script>
            <div id="session-data-{load_key}" style="display: none;"></div>
            """
            
            # Use session state to track if we've already tried to load
            if f'session_load_attempted_{load_key}' not in st.session_state:
                st.components.v1.html(html_code, height=0)
                st.session_state[f'session_load_attempted_{load_key}'] = True
                return None  # Return None on first attempt, data will be available on next run
            
            # For now, return None as we can't easily read from localStorage in Streamlit
            # We'll use a different approach with query parameters
            return None
            
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def clear_session(self) -> None:
        """Clear session data from browser localStorage."""
        try:
            html_code = """
            <script>
                localStorage.removeItem('ai_research_session');
                console.log('Session cleared from localStorage');
            </script>
            """
            st.components.v1.html(html_code, height=0)
            
        except Exception as e:
            print(f"Error clearing session: {e}")
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt session data."""
        try:
            json_data = json.dumps(data)
            encrypted_bytes = self.cipher.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return ""
    
    def _decrypt_data(self, encrypted_data: str) -> Optional[Dict[str, Any]]:
        """Decrypt session data."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted_bytes.decode())
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return None
    
    def is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Check if session data is still valid (not expired)."""
        try:
            expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
            return datetime.utcnow() < expires_at
        except Exception:
            return False

# Alternative approach using URL parameters for session persistence
# SECURITY: Now uses HMAC-signed tokens to prevent forgery
import hmac
import secrets

class URLSessionPersistence:
    """
    Session persistence using URL parameters with HMAC-signed tokens.

    SECURITY IMPROVEMENTS:
    - Tokens are HMAC-signed to prevent forgery
    - Signature verification required to load session
    - Secret key derived from environment variable
    - Token contains username|role|timestamp|signature

    REMAINING RISKS (document for awareness):
    - URL tokens can leak via browser history, server logs, referrer headers
    - Consider using HTTP-only cookies for higher security applications
    """

    def __init__(self):
        self.session_timeout_hours = 24
        # SECURITY: Use environment variable for signing key
        # Falls back to a random key per process (sessions won't persist across restarts)
        secret = os.getenv('SESSION_SECRET_KEY', '')
        if not secret:
            # Generate a random key for this process instance
            # Note: This means sessions won't persist across app restarts
            secret = secrets.token_hex(32)
            print("WARNING: SESSION_SECRET_KEY not set. Using random key - sessions won't persist across restarts.")
        self._signing_key = hashlib.sha256(secret.encode()).digest()

    def _sign_data(self, data: str) -> str:
        """Create HMAC signature for data."""
        return hmac.new(self._signing_key, data.encode(), hashlib.sha256).hexdigest()

    def _verify_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self._sign_data(data)
        return hmac.compare_digest(expected, signature)

    def _create_session_token(self, username: str, role: str) -> str:
        """
        Create a cryptographically signed session token.

        SECURITY: Token format is base64(data.signature) where:
        - data = username|role|timestamp
        - signature = HMAC-SHA256(data, secret_key)
        """
        # Validate inputs to prevent injection
        if '|' in username or '|' in role:
            raise ValueError("Invalid characters in username or role")
        if '.' in username or '.' in role:
            # Additional safety for the token format
            pass  # Allow dots in username/role, just not pipe

        # Use a separator that won't appear in the timestamp
        timestamp = datetime.utcnow().isoformat().replace(':', '_')
        data = f"{username}|{role}|{timestamp}"

        # Sign the data
        signature = self._sign_data(data)

        # Combine data and signature
        token_data = f"{data}.{signature}"
        return base64.urlsafe_b64encode(token_data.encode()).decode()

    def save_session_to_url(self, username: str, role: str) -> None:
        """Save session info to URL parameters."""
        try:
            session_token = self._create_session_token(username, role)

            # Show instructions to user
            st.info(f"""
            **Session Persistence Enabled**

            To maintain your session across page reloads, bookmark this URL with the session token:
            `?session={session_token}`

            Your session will remain active for 24 hours.
            """)

        except Exception as e:
            print(f"Error creating session URL: {e}")

    def load_session_from_url(self) -> Optional[Dict[str, Any]]:
        """
        Load and verify session from URL parameters.

        SECURITY: Verifies HMAC signature before accepting token.
        """
        try:
            query_params = st.query_params
            session_token = query_params.get('session', None)

            if not session_token:
                return None

            # Decode session token
            try:
                decoded = base64.urlsafe_b64decode(session_token.encode()).decode()
            except Exception:
                print("SECURITY: Invalid base64 in session token")
                return None

            # Split data and signature
            if '.' not in decoded:
                print("SECURITY: Malformed session token (missing signature)")
                return None

            # Find the last dot (signature separator)
            last_dot_idx = decoded.rfind('.')
            data = decoded[:last_dot_idx]
            signature = decoded[last_dot_idx + 1:]

            # SECURITY: Verify signature FIRST
            if not self._verify_signature(data, signature):
                print("SECURITY: Session token signature verification failed - possible forgery attempt")
                return None

            # Parse the verified data
            parts = data.split('|')

            if len(parts) != 3:
                print("SECURITY: Malformed session token data")
                return None

            username = parts[0]
            role = parts[1]
            timestamp_str = parts[2].replace('_', ':')

            # Check if session is still valid (not expired)
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                time_diff = datetime.utcnow() - timestamp

                if time_diff >= timedelta(hours=self.session_timeout_hours):
                    print("Session token expired")
                    return None

                return {
                    'username': username,
                    'role': role,
                    'timestamp': timestamp_str
                }
            except ValueError:
                print("SECURITY: Invalid timestamp in session token")
                return None

        except Exception as e:
            print(f"Error loading session from URL: {e}")
            return None

# Global instances
session_persistence = SessionPersistence()
url_session_persistence = URLSessionPersistence() 