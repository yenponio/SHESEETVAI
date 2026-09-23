"""Exercise the actual camera class without loading GPU models or a camera."""
import ast
from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import os
import unittest
from unittest.mock import Mock


class Frame(list):
    def copy(self):
        return Frame(self)


class EvidenceFrameTests(unittest.TestCase):
    def test_saved_frame_preserves_pose_without_display_text_or_banner(self):
        tree = ast.parse(Path(__file__).with_name("camera_integration.py").read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == "DressCodeInspection")
        keypoints = Mock()
        keypoints.data.cpu().numpy.return_value = [object()]
        result = SimpleNamespace(keypoints=keypoints, plot=lambda: Frame(["camera", "pose"]))
        saved = []
        cv2 = SimpleNamespace(FONT_HERSHEY_SIMPLEX=0,
            putText=lambda frame, *args: frame.append("debug text"),
            rectangle=lambda frame, *args: frame.append("black banner"),
            imwrite=lambda path, frame: saved.append(frame.copy()) or True)
        body = {part: {"visible": True} for part in (
            "Left Shoulder", "Right Shoulder", "Left Hip", "Right Hip", "Left Knee",
            "Right Knee", "Left Ankle", "Right Ankle")}
        namespace = dict(cv2=cv2, Counter=Counter, datetime=datetime, os=os,
            CAPTURE_FOLDER="captures", INSPECTION_FRAMES=1, CONF=.5, KEYPOINTS={},
            pose_model=SimpleNamespace(predict=lambda *args, **kwargs: [result]),
            parser=SimpleNamespace(predict=lambda frame: SimpleNamespace(shape=(10, 10))),
            build_body_keypoints=lambda *args: body,
            detect_shoulders=lambda *args: {"covered": True},
            detect_midriff=lambda *args: {"covered": True, "coverage": 1},
            detect_knees=lambda *args: {"covered": False},
            check_dress_code=lambda *args: {"passed": False, "violations": ["Knees exposed"]})
        exec(compile(ast.Module(body=[cls], type_ignores=[]), "camera_integration.py", "exec"), namespace)
        inspection = namespace["DressCodeInspection"]()
        inspection.inspection_state = "INSPECTING"
        display, status = inspection.process_frame(Frame(["camera"]))
        self.assertEqual(saved, [["camera", "pose"]])
        self.assertIn("black banner", display)
        self.assertIn("debug text", display)
        self.assertTrue(status["finished"])
        self.assertEqual(status["violations"], ["Knees exposed"])
        self.assertTrue(status["screenshot"].endswith(".jpg"))


if __name__ == "__main__":
    unittest.main()
