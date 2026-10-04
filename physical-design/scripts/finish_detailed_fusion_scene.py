"""Complete the visual scene after the asynchronous STEP import updates Fusion."""
import sys


def run(_context: str):
    sys.path.insert(0,'/Users/piotrek/Desktop/RaspberryPi-Hackathon/physical-design/scripts')
    import importlib
    import build_detailed_fusion_scene
    importlib.reload(build_detailed_fusion_scene).finish(_context)
