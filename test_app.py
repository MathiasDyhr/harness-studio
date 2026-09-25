import copy,json,tempfile,unittest
from pathlib import Path
import server

class AppTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();server.DB=Path(self.temp.name)/'test.sqlite';server.init()
  with server.connect() as c:self.doc=server.load(c,c.execute('SELECT id FROM harness').fetchone()[0])
 def tearDown(self):self.temp.cleanup()
 def test_seed_and_lengths(self):
  d=self.doc;self.assertEqual((len(d['points']),len(d['segments']),len(d['wires'])),(8,7,4))
  self.assertTrue(all(server.wire_result(d,w)['length_cm'] is not None for w in d['wires']))
  self.assertTrue(all(p['color'] in server.COLORS for p in d['points'] if p['id'].startswith('X')))
  values={w['id']:server.wire_result(d,w)['length_cm'] for w in d['wires']}
  d['segments'][0]['length_cm']=4
  for w in d['wires']:self.assertEqual(server.wire_result(d,w)['length_cm'],values[w['id']])
 def test_save_reload_history_conflict(self):
  d=self.doc;d['points'][0]['x']=20;d['segments'][0]['length_cm']=210
  saved=server.save(d,d['id'],d['version']);self.assertEqual(saved['version'],2)
  with server.connect() as c:
   loaded=server.load(c,d['id']);self.assertEqual(loaded['points'][0]['x'],20);self.assertIsNone(loaded['segments'][0]['length_cm'])
   original=json.loads(c.execute('SELECT document FROM revision WHERE harness_id=? AND version=1',(d['id'],)).fetchone()[0]);self.assertIsNone(original['segments'][0]['length_cm'])
  with self.assertRaises(server.Conflict):server.save(d,d['id'],1)
 def test_geometry_drives_lengths(self):
  d=self.doc;old=[server.wire_result(d,w) for w in d['wires']];d['points'][0]['y']=10
  self.assertNotEqual(old,[server.wire_result(d,w) for w in d['wires']])
 def test_broken_route_blocks_review(self):
  d=self.doc;d['wires'][0]['route']=[];server.validate(d)
  d['status']='reviewed'
  with self.assertRaises(ValueError):server.validate(d)
 def test_physical_measures_are_removed_on_save(self):
  d=self.doc;d['segments'][0]['length_cm']=123;d['bundles']=[{'ids':['M1','M2'],'length_cm':456}]
  saved=server.save(d,d['id'],d['version'])
  self.assertIsNone(saved['segments'][0]['length_cm']);self.assertEqual(saved['bundles'],[])
 def test_invalid_save_atomic(self):
  d=self.doc;d['points'][0]['x']=999
  with self.assertRaises(ValueError):server.save(d,d['id'],1)
  with server.connect() as c:self.assertEqual(server.load(c,d['id'])['version'],1)
 def test_wire_copy_preserved(self):
  d=self.doc;copy_doc=server.save(d);self.assertNotEqual(d['id'],copy_doc['id']);self.assertEqual(len(copy_doc['wires']),4)
 def test_x_point_color_persists(self):
  d=self.doc;point=next(p for p in d['points'] if p['id'].startswith('X'));point['color']='purple';point['label']='D-stolpe højre'
  saved=server.save(d,d['id'],d['version'])
  self.assertEqual(next(p for p in saved['points'] if p['id']==point['id'])['color'],'purple')
  self.assertEqual(next(p for p in saved['points'] if p['id']==point['id'])['label'],'D-stolpe højre')

 def test_x_point_can_span_multiple_holes(self):
  d=self.doc;point=next(p for p in d['points'] if p['id'].startswith('X'));point['span_x']=3;point['span_y']=2;point['anchor_x']=2;point['anchor_y']=2
  saved=server.save(d,d['id'],d['version']);reloaded=next(p for p in saved['points'] if p['id']==point['id'])
  self.assertEqual((reloaded['span_x'],reloaded['span_y']),(3,2))
  self.assertEqual((reloaded['anchor_x'],reloaded['anchor_y']),(2,2))

if __name__=='__main__':unittest.main()
