"""
GLib-GIO Warning Suppression Utility

This module provides utilities to suppress GLib-GIO warnings that appear
when using WeasyPrint on Windows. These warnings are harmless but can
clutter the console output.

Usage:
    from src.glib_suppression import suppress_glib_warnings
    suppress_glib_warnings()
"""

import os
import warnings
import logging


def suppress_glib_warnings():
    """
    Suppress GLib-GIO warnings from WeasyPrint/GTK on Windows.
    
    This function should be called before importing WeasyPrint to prevent
    console spam from GLib-GIO warnings about UWP apps.
    """
    # Set environment variables to suppress GLib warnings
    os.environ['GIO_USE_VFS'] = 'local'
    os.environ['G_MESSAGES_DEBUG'] = '0'
    os.environ['G_DEBUG'] = '0'
    
    # Suppress specific warning categories
    warnings.filterwarnings('ignore', category=UserWarning, module='gi')
    warnings.filterwarnings('ignore', message='.*GLib-GIO.*')
    warnings.filterwarnings('ignore', message='.*UWP app.*')
    warnings.filterwarnings('ignore', message='.*supports.*extensions.*')
    warnings.filterwarnings('ignore', message='.*Unexpectedly.*')
    
    # Set logging level for gi module to ERROR
    logging.getLogger('gi').setLevel(logging.ERROR)
    
    # Additional suppression for GLib warnings
    logging.getLogger('gi.repository.GLib').setLevel(logging.ERROR)
    logging.getLogger('gi.repository.Gio').setLevel(logging.ERROR)
    
    # Redirect GLib warnings to null
    import sys
    from contextlib import redirect_stderr
    from io import StringIO
    
    # Create a null device for stderr
    null_stderr = StringIO()
    
    # This won't work for GLib warnings that go directly to stderr
    # but we'll try to suppress what we can


def setup_weasyprint_environment():
    """
    Set up the environment for WeasyPrint with GLib warning suppression.
    
    This is a convenience function that combines GLib suppression
    with WeasyPrint-specific environment setup.
    """
    suppress_glib_warnings()
    
    # Additional WeasyPrint-specific environment variables
    os.environ.setdefault('WEASYPRINT_DEBUG', '0')
    os.environ.setdefault('WEASYPRINT_LOGGER', 'weasyprint')
    
    # Suppress WeasyPrint's own logging if not in debug mode
    if os.getenv('DEBUG', 'false').lower() != 'true':
        logging.getLogger('weasyprint').setLevel(logging.WARNING)


# Auto-suppress when module is imported
suppress_glib_warnings()
