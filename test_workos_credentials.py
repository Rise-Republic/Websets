#!/usr/bin/env python3
"""
Test script to verify WorkOS credentials and configuration
Run this after updating your credentials in docker-compose.yml
"""
import os
from workos import WorkOSClient

def test_workos_credentials():
    """Test WorkOS client creation and basic functionality"""
    
    # Get credentials from environment
    api_key = os.getenv('WORKOS_API_KEY_TEST')
    client_id = os.getenv('WORKOS_CLIENT_ID_TEST')
    redirect_uri = os.getenv('WORKOS_REDIRECT_URI', 'http://localhost:8001/api/auth/callback')
    
    print("=== WorkOS Credentials Test ===")
    print(f"API Key: {api_key[:10] + '...' if api_key else 'NOT SET'}")
    print(f"Client ID: {client_id[:10] + '...' if client_id else 'NOT SET'}")
    print(f"Redirect URI: {redirect_uri}")
    print()
    
    if not api_key or not client_id:
        print("❌ ERROR: Missing WorkOS credentials")
        print("Please set WORKOS_API_KEY_TEST and WORKOS_CLIENT_ID_TEST in docker-compose.yml")
        return False
    
    try:
        # Initialize WorkOS client
        client = WorkOSClient(
            api_key=api_key,
            client_id=client_id
        )
        print("✅ WorkOS client created successfully")
        
        # Test authorization URL generation
        auth_url = client.user_management.get_authorization_url(
            provider="authkit",
            redirect_uri=redirect_uri
        )
        print("✅ Authorization URL generated successfully")
        print(f"Auth URL: {auth_url[:50]}...")
        
        # Check if URL contains your AuthKit domain
        if "hardy-satellite-24-staging.authkit.app" in auth_url:
            print("✅ AuthKit domain matches your configuration")
        else:
            print("⚠️  WARNING: AuthKit domain might not match")
        
        print("\n=== Test Results ===")
        print("✅ All tests passed!")
        print("Your WorkOS configuration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("Please check your WorkOS credentials and try again.")
        return False

if __name__ == "__main__":
    test_workos_credentials()
