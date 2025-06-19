"""
Authentication and user management
"""

import os
import jwt
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

class AuthManager:
    """Handles user authentication and token management"""
    
    def __init__(self):
        self.base_url = os.getenv('SIGNALOS_API_URL', 'https://api.signalos.com')
        self.token_file = Path.home() / ".signalos" / "auth_token"
        self.current_token = None
        self.user_data = None
        
        # Load existing token
        self.load_token()
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate user with username/password
        Returns: (success, message)
        """
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={'username': username, 'password': password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = data.get('token')
                self.user_data = data.get('user')
                
                if self.current_token:
                    self.save_token()
                    return True, "Login successful"
                else:
                    return False, "Invalid response from server"
            else:
                error_msg = response.json().get('message', 'Login failed')
                return False, error_msg
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def login_with_token(self, token: str) -> tuple[bool, str]:
        """
        Authenticate using existing token
        Returns: (success, message)
        """
        try:
            response = requests.get(
                f"{self.base_url}/auth/verify",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = token
                self.user_data = data.get('user')
                self.save_token()
                return True, "Token authentication successful"
            else:
                return False, "Invalid or expired token"
                
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Token verification error: {str(e)}"
    
    def logout(self):
        """Log out the current user"""
        try:
            if self.current_token:
                # Notify server about logout
                requests.post(
                    f"{self.base_url}/auth/logout",
                    headers={'Authorization': f'Bearer {self.current_token}'},
                    timeout=5
                )
        except:
            pass  # Ignore logout errors
        
        # Clear local data
        self.current_token = None
        self.user_data = None
        self.clear_token()
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        if not self.current_token:
            return False
        
        try:
            # Decode token to check expiration (without verification for speed)
            payload = jwt.decode(self.current_token, options={"verify_signature": False})
            exp_timestamp = payload.get('exp', 0)
            
            if exp_timestamp > datetime.utcnow().timestamp():
                return True
        except:
            pass
        
        return False
    
    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return self.user_data
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.current_token:
            return {'Authorization': f'Bearer {self.current_token}'}
        return {}
    
    def save_token(self):
        """Save authentication token to file"""
        try:
            if self.current_token:
                self.token_file.parent.mkdir(exist_ok=True)
                with open(self.token_file, 'w') as f:
                    f.write(self.current_token)
        except Exception as e:
            print(f"Error saving token: {e}")
    
    def load_token(self):
        """Load authentication token from file"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        # Try to authenticate with saved token
                        success, _ = self.login_with_token(token)
                        if not success:
                            self.clear_token()
        except Exception as e:
            print(f"Error loading token: {e}")
            self.clear_token()
    
    def clear_token(self):
        """Clear saved authentication token"""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
        except Exception as e:
            print(f"Error clearing token: {e}")
    
    def sync_user_config(self) -> tuple[bool, Optional[Dict]]:
        """Sync user configuration from server"""
        if not self.current_token:
            return False, None
        
        try:
            response = requests.get(
                f"{self.base_url}/user/config",
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, None
                
        except Exception as e:
            print(f"Error syncing config: {e}")
            return False, None
    
    def upload_config(self, config_data: Dict) -> bool:
        """Upload configuration to server"""
        if not self.current_token:
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/user/config",
                json=config_data,
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error uploading config: {e}")
            return False

# Global auth manager instance
auth_manager = AuthManager()
