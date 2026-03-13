"""Run the Mock Interview Coach application."""

import os
import sys
import uvicorn
from app import app

def validate_nova_sonic_on_startup():
    """Validate Nova Sonic connectivity on server startup.
    
    In production mode: Server will not start if Nova Sonic is unavailable.
    In dev mode: Server will start with mock audio regardless of Nova Sonic availability.
    
    Returns:
        bool: True if validation passes or dev mode is enabled, False otherwise
    """
    from mock_interview_coach.voice_interface import NovaSonicClient
    
    # Check if dev mode is enabled
    dev_mode = os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true'
    
    if dev_mode:
        print("🔧 Development mode enabled - using mock audio")
        print("   Nova Sonic validation skipped")
        return True
    
    print("\n🔍 Validating Nova Sonic connectivity...")
    
    try:
        client = NovaSonicClient()
        is_available = client.validate_model_availability()
        
        if is_available:
            print("✅ Nova Sonic is available")
            print(f"   Model: {client.get_model_id()}")
            print(f"   Region: {client.get_region()}")
            return True
        else:
            print("\n❌ ERROR: Nova Sonic is not available")
            print("\nPossible causes:")
            print("  • Model not available in the configured AWS region")
            print("  • AWS credentials don't have Bedrock permissions")
            print("  • Model ID is incorrect")
            print("\nTo fix this:")
            print("  1. Check AWS_REGION environment variable")
            print("  2. Verify AWS credentials have bedrock:InvokeModel permission")
            print("  3. Confirm model is available in your region")
            print("  4. Or enable dev mode: export ENABLE_DEV_MODE=true")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: Failed to validate Nova Sonic connectivity")
        print(f"   {str(e)}")
        print("\nTo fix this:")
        print("  1. Check AWS credentials are configured")
        print("  2. Verify network connectivity to AWS")
        print("  3. Or enable dev mode: export ENABLE_DEV_MODE=true")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Mock Interview Coach - Starting Server")
    print("=" * 60)
    
    # Validate Nova Sonic connectivity on startup
    if not validate_nova_sonic_on_startup():
        print("\n" + "=" * 60)
        print("❌ Server startup aborted due to Nova Sonic validation failure")
        print("=" * 60)
        sys.exit(1)
    
    print("\nServer will start on: http://localhost:8001")
    print("Web interface: http://localhost:8001/static/index.html")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
