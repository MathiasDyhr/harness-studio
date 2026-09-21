import json
import tempfile
import unittest
from pathlib import Path
import server


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = server.DB
        server.DB = Path(self.temp.name) / 'test.sqlite'
        server.init()
        with server.connect() as connection:
            key = connection.execute('SELECT id FROM harness').fetchone()[0]
            self.doc = server.load(connection, key)

    def tearDown(self):
        server.DB = self.previous_db
        self.temp.cleanup()

    def test_lengths_and_allowance(self):
        wire = self.doc['wires'][0]
        self.assertEqual(server.wire_result(self.doc, wire)['length_cm'], 244)
        self.doc['segments'][0]['length_cm'] += 5
        wire['allowance_cm'] = 20
        self.assertEqual(server.wire_result(self.doc, wire)['length_cm'], 269)

    def test_geometry_does_not_change_measurements(self):
        wire = self.doc['wires'][0]
        before = server.wire_result(self.doc, wire)
        self.doc['points'][0]['y'] = 250
        self.assertEqual(server.wire_result(self.doc, wire), before)

    def test_save_history_and_stale_version(self):
        self.doc['segments'][0]['length_cm'] = 65
        saved = server.save(self.doc, self.doc['id'], self.doc['version'])
        self.assertEqual(saved['version'], 2)
        with server.connect() as connection:
            loaded = server.load(connection, self.doc['id'])
            self.assertEqual(loaded['segments'][0]['length_cm'], 65)
            row = connection.execute('SELECT document FROM revision WHERE harness_id=? AND version=1', (self.doc['id'],)).fetchone()
            self.assertEqual(json.loads(row[0])['segments'][0]['length_cm'], 60)
        with self.assertRaises(server.Conflict):
            server.save(self.doc, self.doc['id'], 1)

    def test_invalid_save_is_atomic(self):
        self.doc['points'][0]['x'] = 999
        with self.assertRaises(ValueError):
            server.save(self.doc, self.doc['id'], 1)
        with server.connect() as connection:
            self.assertEqual(server.load(connection, self.doc['id'])['version'], 1)

    def test_disconnected_route_blocks_review(self):
        self.doc['wires'][0]['route'] = ['M1', 'M4']
        self.assertIsNone(server.wire_result(self.doc, self.doc['wires'][0])['length_cm'])
        server.validate(self.doc)
        self.doc['status'] = 'reviewed'
        with self.assertRaises(ValueError):
            server.validate(self.doc)

    def test_duplicate_wires_preserved(self):
        copied = server.save(self.doc)
        self.assertNotEqual(copied['id'], self.doc['id'])
        self.assertEqual(sum(w['a'] == 'X1' and w['b'] == 'X2' for w in copied['wires']), 2)

    def test_missing_measurement(self):
        self.doc['segments'][0]['length_cm'] = None
        self.assertIsNone(server.wire_result(self.doc, self.doc['wires'][0])['length_cm'])

    def test_combined_measurement_and_partial_route(self):
        self.doc['segments'][0]['length_cm'] = None
        self.doc['segments'][1]['length_cm'] = None
        self.doc['bundles'] = [{'ids': ['M1', 'M2'], 'length_cm': 116}]
        self.assertEqual(server.wire_result(self.doc, self.doc['wires'][0])['length_cm'], 244)
        self.doc['points'].append({'id': 'X5', 'x': 20, 'y': 210})
        self.doc['segments'][0]['b'] = 'X5'
        wire = dict(self.doc['wires'][0], b='X5', route=['M1'])
        self.assertIsNone(server.wire_result(self.doc, wire)['length_cm'])


if __name__ == '__main__':
    unittest.main()
