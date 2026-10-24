import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'
if not (SCRIPTS/'scan_tidal_playlist.py').exists(): SCRIPTS=Path(__file__).parent
sys.path.insert(0,str(SCRIPTS))
import scan_tidal_playlist as scan


def track(rid='new',duration='PT7M55S',title='Geysir',code='GBYDS2000298',names=('artist',)):
    return {'id':rid,'type':'tracks','attributes':{'title':title,'isrc':code,'duration':duration,'availability':['STREAM']},
            'relationships':{'artists':{'data':[{'type':'artists','id':n} for n in names]}}}


class Tests(unittest.TestCase):
    def setUp(self):
        self.resources={('artists','artist'):{'attributes':{'name':'Mark Simpson'}}}
        self.old={'title':'Geysir','isrc':'GBYDS2000298','duration_seconds':475,'artists':['Mark Simpson']}

    def test_exact_recording(self):
        self.assertEqual(scan.assess(self.old,[track()],self.resources)[0],'CONFIRMED')

    def test_duration_title_or_artist_mismatch_requires_review(self):
        for candidate in [track(duration='PT7M56S'),track(title='Another piece'),track(names=('other',))]:
            self.assertEqual(scan.assess(self.old,[candidate],self.resources)[0],'REVIEW')

    def test_multiple_identical_manifestations_not_auto_selected(self):
        self.assertEqual(scan.assess(self.old,[track('a'),track('b')],self.resources)[0],'REVIEW')

    def test_unavailable_candidate_not_selected(self):
        candidate=track();candidate['attributes']['availability']=[]
        self.assertEqual(scan.assess(self.old,[candidate],self.resources)[0],'NOT_FOUND')

    def test_csv_recovers_deleted_track_identity(self):
        archived={'title':'Geysir','isrc':'GBYDS2000298','duration':'475s','artist':'Mark Simpson'}
        result=scan.fingerprint(None,archived,{})
        self.assertEqual(result['source'],'csv_export')
        self.assertEqual(result['duration_seconds'],475)

    def test_transient_error_is_not_unavailability_and_duplicates_retained(self):
        class Fake:
            def __init__(self):
                self.resources={**self_outer.resources,('tracks','available'):track('available')}
            def tracks(self,field,values):
                if field=='id': return []
                result=track();self.resources[('tracks','new')]=result;return [result]
            def request(self,path):
                if '/tracks/dead?' in path:raise ValueError('API GET failed (HTTP 404)')
                raise ValueError('API GET failed (HTTP 503)')
        self_outer=self
        items=[{'id':rid,'type':'tracks','meta':{'itemId':str(n)}} for n,rid in enumerate(['available','dead','error','dead'])]
        archived={'dead':{'title':'Geysir','isrc':'GBYDS2000298','duration':'475s','artist':'Mark Simpson'}}
        result=scan.scan(Fake(),{'items':items},archived)
        self.assertEqual(result['available_occurrences'],1)
        self.assertEqual(result['unavailable_occurrences'],2)
        self.assertEqual(result['uncertain_occurrences'],1)
        self.assertEqual(result['status_counts'],{'CONFIRMED':2,'UNCERTAIN':1})
        self.assertEqual([r['item_id'] for r in result['rows'] if r['status']=='CONFIRMED'],['1','3'])

    def test_included_placeholder_still_gets_individual_404_check(self):
        class Fake:
            resources={('tracks','dead'):{'id':'dead','type':'tracks','attributes':{}}}
            def tracks(self,*args):return []
            def request(self,path):raise ValueError('API GET failed (HTTP 404)')
        archived={'dead':{'title':'Geysir','isrc':'GBYDS2000298','duration':'475s','artist':'Mark Simpson'}}
        result=scan.scan(Fake(),{'items':[{'id':'dead','type':'tracks','meta':{'itemId':'one'}}]},archived)
        self.assertEqual(result['unavailable_occurrences'],1)
        self.assertEqual(result['uncertain_occurrences'],0)
        self.assertEqual(result['rows'][0]['availability_reason'],'HTTP_404_NL')
        self.assertEqual(result['rows'][0]['fingerprint']['source'],'csv_export')

    def test_no_write_interface(self):
        client=scan.ScannerClient('fake')
        with self.assertRaisesRegex(ValueError,'cannot make write'):
            client.request('/playlists/id','DELETE')

    def test_missing_old_isrc_is_not_inferred_from_title(self):
        class Fake:
            resources={('tracks','dead'):{'id':'dead','type':'tracks','attributes':{'title':'Geysir','availability':[]}}}
            def tracks(self,*args):raise AssertionError('No ISRC search should occur')
        result=scan.scan(Fake(),{'items':[{'id':'dead','type':'tracks','meta':{'itemId':'one'}}]}, {})
        self.assertEqual(result['rows'][0]['status'],'MISSING_FINGERPRINT')


if __name__=='__main__':unittest.main()
