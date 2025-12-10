
import streamlit as st
from config import init_supabase

class AuthManager:
    """Manages User Authentication using Supabase."""

    def __init__(self):
        self.supabase = init_supabase()

    def is_configured(self):
        """Check if Supabase is configured."""
        return self.supabase is not None

    def sign_up(self, email, password, **data):
        """Sign up a new user."""
        if not self.is_configured():
            return {"error": "Authentication service not unavailable."}
        
        try:
            print(f"Attempting sign up for {email}")
            # Supabase Auth Sign Up
            response = self.supabase.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "data": data
                }
            })
            
            # Check if we got a session or user (depends on Supabase settings/confirmations)
            if response.user:
                return {"success": True, "message": "Account created! Please check your email for confirmation link." if response.session is None else "Account created successfully!", "user": response.user}
            else:
                 # This might happen if email confirmation is required and no session is returned immediately
                 # But usually sign_up returns a response object that might contain error if failed, or user if success.
                 # Python client raises exception on error usually? Let's catch generic exception.
                 return {"success": True, "message": "Sign up initiated. Please check your email."}

        except Exception as e:
            print(f"Sign up error: {e}")
            return {"error": str(e)}

    def sign_in(self, email, password):
        """Sign in an existing user."""
        if not self.is_configured():
             return {"error": "Authentication service not unavailable."}

        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            
            if response.session:
                return {"success": True, "session": response.session, "user": response.user}
            else:
                return {"error": "Login failed. Check your credentials."}

        except Exception as e:
            return {"error": str(e)}

    def sign_out(self):
        """Sign out the current user."""
        if not self.is_configured():
            return
        try:
            self.supabase.auth.sign_out()
        except:
            pass

    def get_current_user(self):
        """Get the currently logged in user from local session state."""
        # Note: In Streamlit, we manage session manually. 
        # Supabase client might persist session in local storage if in browser, 
        # but in Python Streamlit (server-side), we need to check Strealit's session_state.
        # This method might just be a helper to check supabase client state if needed,
        # but primarily we rely on what we stored in st.session_state after login.
        if not self.is_configured():
            return None
        
        try:
            # Check if there's an active session in the supabase client
            session = self.supabase.auth.get_session()
            if session:
                return session.user
        except:
            pass
        return None
