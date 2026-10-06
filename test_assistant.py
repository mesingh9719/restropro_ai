"""Compatibility runner for the assistant contract suite."""
import unittest

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover("tests"))
