import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db


class NotesDbTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_notes.db")
        db.DB_PATH = self.db_path
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_create_update_and_delete_note(self):
        ok, _ = db.create_user("tester", "tester@example.com", "password123")
        self.assertTrue(ok)

        user = db.verify_user("tester", "password123")
        self.assertIsNotNone(user)

        note_id = db.create_note(user["id"], "Test title", "Body", "2026-08-01 10:00")
        self.assertIsInstance(note_id, int)

        notes = db.get_user_notes(user["id"])
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["title"], "Test title")

        db.update_note(note_id, user["id"], "Updated title", "Updated body", "2026-08-01 12:00")
        updated = db.get_note(note_id, user["id"])
        self.assertEqual(updated["title"], "Updated title")
        self.assertEqual(updated["content"], "Updated body")

        db.delete_note(note_id, user["id"])
        self.assertEqual(db.get_user_notes(user["id"]), [])


if __name__ == "__main__":
    unittest.main()
