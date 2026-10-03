"""Compatibility entry point for the maintained Sandbox launcher.

Use ``deploy_sandbox_demo.py --private-capture`` directly for explicit CLI
options. This wrapper keeps older documentation and bookmarks functional while
using the same bounded implementation.
"""

from deploy_sandbox_demo import main

if __name__ == "__main__":
    main()
