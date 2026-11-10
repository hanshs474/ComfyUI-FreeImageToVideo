if __package__:  # ComfyUI loads this folder as a package; a bare import (e.g. by a test runner) skips the nodes
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
