import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/playlist_live_pilot.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name('playlist_live_pilot.py')
spec = importlib.util.spec_from_file_location('playlist_live_pilot', SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class FakeWriteClient:
    def __init__(self, malformed_insert=False):
        self.items=[]; self.number=0; self.deleted=False; self.old_removed=False
        self.malformed_insert=malformed_insert

    def request(self,path,method='GET',body=None):
        assert pilot.PLAYLIST not in path
        if path=='/playlists':
            return {'data':{'id':'scratch'}}
        if path=='/playlists/scratch':
            self.deleted=True; return {}
        if method=='POST':
            new=[]
            for item in body['data']:
                self.number+=1
                new.append({**item,'meta':{'itemId':str(self.number)}})
            anchor=body.get('meta',{}).get('positionBefore')
            index=next((i for i,item in enumerate(self.items) if item['meta']['itemId']==anchor),len(self.items))
            if self.malformed_insert and anchor:
                index=len(self.items)
            self.items[index:index]=new
        if method=='DELETE':
            occurrence=body['data'][0]['meta']['itemId']
            self.items=[item for item in self.items if item['meta']['itemId']!=occurrence]
            self.old_removed=True
        return {}

    def snapshot(self,pid):
        return {'items':self.items.copy()}


class PilotTests(unittest.TestCase):
    def test_all_duplicate_occurrences_and_videos(self):
        original=[{'type':'tracks','id':'a'},{'type':'tracks','id':'b'},{'type':'tracks','id':'a'},{'type':'videos','id':'a'}]
        output=pilot.replaced_items(original,{'a':'c'})
        self.assertEqual([i['id'] for i in output],['c','b','c','a'])
        self.assertEqual(original[0]['id'],'a')

    def test_occurrence_specific_replacement(self):
        client=FakeWriteClient()
        self.assertTrue(pilot.write_test(client)['passed'])
        self.assertTrue(client.deleted)
        self.assertEqual([i['id'] for i in client.items],['283191455','283191455','283191456'])

    def test_bad_insert_does_not_delete_old_occurrence(self):
        client=FakeWriteClient(malformed_insert=True)
        with self.assertRaisesRegex(ValueError,'Insert verification failed'):
            pilot.write_test(client)
        self.assertFalse(client.old_removed)
        self.assertTrue(client.deleted)

    def test_credentials_not_sent_to_unexpected_host(self):
        client=pilot.Client('test-token')
        for url in ['https://other.example/v2/playlists/x','https://openapi.tidal.com@other.example/v2/x','http://openapi.tidal.com/v2/x','https://openapi.tidal.com/v1/x']:
            with self.assertRaisesRegex(ValueError,'Unexpected API URL'):
                client.request(url)

    def test_snapshot_aborts_on_concurrent_change(self):
        class Changing(pilot.Client):
            def __init__(self): self.calls=0
            def request(self,path,*args):
                if '/relationships/items' in path:
                    return {'data':[],'links':{}}
                self.calls+=1
                return {'data':{'id':'scratch','attributes':{'lastModifiedAt':str(self.calls)}}}
        with self.assertRaisesRegex(ValueError,'Playlist changed'):
            Changing().snapshot('scratch')


if __name__=='__main__':
    unittest.main()
