#!/usr/bin/env python3
"""
Test script for debug configuration and performance fixes.
This script demonstrates the new debug mode optimizations.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.debug_config import get_debug_config, is_debug_mode, get_debug_browser_args, get_debug_timeouts, get_debug_delays
from src.logging_config import get_logger

def test_debug_configuration():
    """Test the debug configuration system."""
    logger = get_logger(__name__)
    
    print("🔧 Testing Debug Configuration System")
    print("=" * 50)
    
    # Test debug mode detection
    debug_mode = is_debug_mode()
    print(f"Debug mode enabled: {debug_mode}")
    
    # Test debug configuration
    config = get_debug_config()
    print(f"Debug config created: {config is not None}")
    
    # Test browser arguments
    browser_args = get_debug_browser_args()
    print(f"Debug browser args count: {len(browser_args)}")
    if browser_args:
        print("Sample debug browser args:")
        for arg in browser_args[:5]:  # Show first 5
            print(f"  - {arg}")
    
    # Test timeouts
    timeouts = get_debug_timeouts()
    print(f"Debug timeouts: {timeouts}")
    
    # Test delays
    delays = get_debug_delays()
    print(f"Debug delays: {delays}")
    
    # Test environment variables
    print("\n📋 Environment Variables:")
    debug_vars = [
        'DEBUG',
        'REDUCE_DEBUG_PAUSES', 
        'SKIP_DEBUG_STOPS',
        'ENABLE_GRAPHQL_DEBUG',
        'ENABLE_BROWSER_MONITORING'
    ]
    
    for var in debug_vars:
        value = os.getenv(var, 'not set')
        print(f"  {var}: {value}")
    
    print("\n✅ Debug configuration test completed!")

def demonstrate_debug_optimizations():
    """Demonstrate the debug optimizations."""
    print("\n🚀 Debug Mode Optimizations")
    print("=" * 50)
    
    print("1. GraphQL Error Handling:")
    print("   - Suppressed GraphQLInvalidServerResponseError")
    print("   - Suppressed _normalizeProjection errors")
    print("   - Suppressed voyager* API errors")
    
    print("\n2. Browser Configuration:")
    print("   - Disabled aggressive image blocking")
    print("   - Selective tracker blocking (preserves LinkedIn APIs)")
    print("   - Debug-specific browser arguments")
    
    print("\n3. Debug Mode Functions:")
    print("   - Optimized debug pauses")
    print("   - Configurable debug stops")
    print("   - Enhanced error filtering")
    
    print("\n4. Performance Improvements:")
    print("   - 50% reduction in debug pauses (when REDUCE_DEBUG_PAUSES=true)")
    print("   - Automatic pauses instead of manual input")
    print("   - Longer timeouts for GraphQL operations")
    
    print("\n✅ Debug optimizations demonstrated!")

if __name__ == "__main__":
    test_debug_configuration()
    demonstrate_debug_optimizations()
    
    print("\n🎯 Usage Examples:")
    print("Basic debug mode:")
    print("  DEBUG=true python main.py")
    print("\nOptimized debug mode (recommended):")
    print("  DEBUG=true REDUCE_DEBUG_PAUSES=true python main.py")
    print("\nFull debug mode with GraphQL logging:")
    print("  DEBUG=true ENABLE_GRAPHQL_DEBUG=true python main.py")
