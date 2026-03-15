"""Tests for the persistent memory system."""

import json
import tempfile
import unittest
from pathlib import Path

import mcp_server_code_execution_mode as bridge_module


class MemorySystemTests(unittest.TestCase):
    """Test the memory functions in isolation (simulating sandbox environment)."""

    def setUp(self):
        """Create a temporary directory for memory storage."""
        self._temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self._temp_dir.name) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        self._temp_dir.cleanup()

    def _save_memory(self, key, value, metadata=None):
        """Simulate the save_memory function."""
        import re
        import time

        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key).strip())
        if not sanitized:
            raise ValueError("Memory key cannot be empty")
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        memory_file = self.memory_dir / f"{sanitized}.json"
        memory_data = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        if memory_file.exists():
            try:
                existing = json.loads(memory_file.read_text())
                memory_data["created_at"] = existing.get("created_at", memory_data["created_at"])
            except Exception:
                pass

        memory_file.write_text(json.dumps(memory_data, indent=2, default=str))
        return f"Memory '{key}' saved."

    def _load_memory(self, key, default=None):
        """Simulate the load_memory function."""
        import re

        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key).strip())
        memory_file = self.memory_dir / f"{sanitized}.json"

        if not memory_file.exists():
            return default

        try:
            data = json.loads(memory_file.read_text())
            return data.get("value", default)
        except Exception:
            return default

    def _delete_memory(self, key):
        """Simulate the delete_memory function."""
        import re

        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key).strip())
        memory_file = self.memory_dir / f"{sanitized}.json"

        if memory_file.exists():
            memory_file.unlink()
            return f"Memory '{key}' deleted."
        return f"Memory '{key}' not found."

    def _list_memories(self):
        """Simulate the list_memories function."""
        if not self.memory_dir.exists():
            return []

        memories = []
        for memory_file in sorted(self.memory_dir.glob("*.json")):
            try:
                data = json.loads(memory_file.read_text())
                memories.append({
                    "key": data.get("key", memory_file.stem),
                    "metadata": data.get("metadata", {}),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                })
            except Exception:
                memories.append({"key": memory_file.stem, "error": "Failed to read"})
        return memories

    def _memory_exists(self, key):
        """Simulate the memory_exists function."""
        import re

        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key).strip())
        memory_file = self.memory_dir / f"{sanitized}.json"
        return memory_file.exists()

    def _update_memory(self, key, updater):
        """Simulate the update_memory function."""
        current = self._load_memory(key, default=None)
        new_value = updater(current)
        self._save_memory(key, new_value)
        return new_value

    def test_save_and_load_simple_value(self):
        """Test saving and loading a simple string value."""
        result = self._save_memory("test_key", "test_value")
        self.assertIn("saved", result)

        loaded = self._load_memory("test_key")
        self.assertEqual(loaded, "test_value")

    def test_save_and_load_dict(self):
        """Test saving and loading a dictionary."""
        data = {"goal": "Build API", "progress": ["Step 1", "Step 2"]}
        self._save_memory("project_context", data)

        loaded = self._load_memory("project_context")
        self.assertEqual(loaded, data)

    def test_save_and_load_list(self):
        """Test saving and loading a list."""
        data = [1, 2, 3, "four", {"five": 5}]
        self._save_memory("my_list", data)

        loaded = self._load_memory("my_list")
        self.assertEqual(loaded, data)

    def test_load_nonexistent_returns_default(self):
        """Test that loading a nonexistent key returns the default."""
        loaded = self._load_memory("nonexistent", default="fallback")
        self.assertEqual(loaded, "fallback")

        loaded_none = self._load_memory("nonexistent")
        self.assertIsNone(loaded_none)

    def test_delete_memory(self):
        """Test deleting a memory entry."""
        self._save_memory("to_delete", "value")
        self.assertTrue(self._memory_exists("to_delete"))

        result = self._delete_memory("to_delete")
        self.assertIn("deleted", result)
        self.assertFalse(self._memory_exists("to_delete"))

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent memory."""
        result = self._delete_memory("never_existed")
        self.assertIn("not found", result)

    def test_list_memories(self):
        """Test listing all memories."""
        self._save_memory("key1", "value1")
        self._save_memory("key2", "value2")
        self._save_memory("key3", {"nested": "data"})

        memories = self._list_memories()
        self.assertEqual(len(memories), 3)

        keys = [m["key"] for m in memories]
        self.assertIn("key1", keys)
        self.assertIn("key2", keys)
        self.assertIn("key3", keys)

    def test_list_memories_empty(self):
        """Test listing memories when none exist."""
        memories = self._list_memories()
        self.assertEqual(memories, [])

    def test_memory_exists(self):
        """Test checking if a memory exists."""
        self.assertFalse(self._memory_exists("new_key"))

        self._save_memory("new_key", "value")
        self.assertTrue(self._memory_exists("new_key"))

    def test_update_memory(self):
        """Test updating a memory with a function."""
        self._save_memory("counter", 0)

        result = self._update_memory("counter", lambda x: x + 1)
        self.assertEqual(result, 1)

        result = self._update_memory("counter", lambda x: x + 1)
        self.assertEqual(result, 2)

        loaded = self._load_memory("counter")
        self.assertEqual(loaded, 2)

    def test_update_memory_list_append(self):
        """Test updating a list by appending."""
        self._save_memory("tasks", ["task1"])

        result = self._update_memory("tasks", lambda tasks: tasks + ["task2"])
        self.assertEqual(result, ["task1", "task2"])

    def test_update_nonexistent_memory(self):
        """Test updating a memory that doesn't exist."""
        result = self._update_memory("new_list", lambda x: [] if x is None else x + [1])
        self.assertEqual(result, [])

    def test_save_with_metadata(self):
        """Test saving memory with metadata."""
        self._save_memory("tagged", "value", metadata={"tags": ["important", "project-x"]})

        memories = self._list_memories()
        tagged_memory = next(m for m in memories if m["key"] == "tagged")
        self.assertEqual(tagged_memory["metadata"]["tags"], ["important", "project-x"])

    def test_key_sanitization(self):
        """Test that special characters in keys are sanitized."""
        self._save_memory("key with spaces!", "value1")
        self._save_memory("key/with/slashes", "value2")
        self._save_memory("key@special#chars", "value3")

        # Should be able to load using original keys
        self.assertEqual(self._load_memory("key with spaces!"), "value1")
        self.assertEqual(self._load_memory("key/with/slashes"), "value2")
        self.assertEqual(self._load_memory("key@special#chars"), "value3")

    def test_overwrite_preserves_created_at(self):
        """Test that overwriting a memory preserves the original created_at timestamp."""
        import time

        self._save_memory("timestamp_test", "original")
        
        # Read the original created_at
        memory_file = self.memory_dir / "timestamp_test.json"
        original_data = json.loads(memory_file.read_text())
        original_created = original_data["created_at"]

        # Wait a tiny bit and update
        time.sleep(0.01)
        self._save_memory("timestamp_test", "updated")

        # Check that created_at is preserved but updated_at changed
        updated_data = json.loads(memory_file.read_text())
        self.assertEqual(updated_data["created_at"], original_created)
        self.assertGreater(updated_data["updated_at"], original_created)


class EntrypointMemoryCodeTests(unittest.TestCase):
    """Test that the entrypoint template includes memory functions."""

    def test_entrypoint_contains_memory_functions(self):
        """Verify the entrypoint template has memory function definitions."""
        sandbox = bridge_module.RootlessContainerSandbox()
        entrypoint = sandbox._render_entrypoint([], {})

        # Check that all memory functions are defined
        self.assertIn("def save_memory(", entrypoint)
        self.assertIn("def load_memory(", entrypoint)
        self.assertIn("def delete_memory(", entrypoint)
        self.assertIn("def list_memories(", entrypoint)
        self.assertIn("def update_memory(", entrypoint)
        self.assertIn("def memory_exists(", entrypoint)
        self.assertIn("def get_memory_info(", entrypoint)

    def test_entrypoint_exports_memory_to_runtime(self):
        """Verify memory functions are exported to runtime module."""
        sandbox = bridge_module.RootlessContainerSandbox()
        entrypoint = sandbox._render_entrypoint([], {})

        self.assertIn("runtime_module.save_memory = save_memory", entrypoint)
        self.assertIn("runtime_module.load_memory = load_memory", entrypoint)
        self.assertIn("globals()[\"save_memory\"] = save_memory", entrypoint)
        self.assertIn("globals()[\"load_memory\"] = load_memory", entrypoint)

    def test_entrypoint_defines_memory_dir(self):
        """Verify MEMORY_DIR is defined in entrypoint."""
        sandbox = bridge_module.RootlessContainerSandbox()
        entrypoint = sandbox._render_entrypoint([], {})

        self.assertIn("MEMORY_DIR = Path(\"/projects/memory\")", entrypoint)

    def test_capability_summary_mentions_memory(self):
        """Verify the capability summary mentions memory functions."""
        sandbox = bridge_module.RootlessContainerSandbox()
        entrypoint = sandbox._render_entrypoint([], {})

        self.assertIn("MEMORY", entrypoint)
        self.assertIn("save_memory", entrypoint)
        self.assertIn("load_memory", entrypoint)


if __name__ == "__main__":
    unittest.main()
