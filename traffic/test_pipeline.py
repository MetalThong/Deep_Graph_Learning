"""Tests of leakage boundaries, missing-target metrics, and graph ablation semantics."""
import unittest
import numpy as np
from train import ROOT,score,KMH

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=np.load(ROOT/'data'/'prepared.npz')
    def test_chronological_targets(self):
        d=self.d
        self.assertLess(d['train'][-1]+3,d['val'][0]+3)
        self.assertLess(d['val'][-1]+3,d['test'][0]+3)
        self.assertLessEqual(d['train'][-1]+3,d['val'][0])
        self.assertLessEqual(d['val'][-1]+3,d['test'][0])
        for name in ['train','val','test']:
            self.assertTrue((d[name]-11>=0).all())
            self.assertTrue((d[name]+3<len(d['raw'])).all())
    def test_train_only_scaler(self):
        d=self.d; stop=d['train'][-1]+4
        observed=d['raw'][:stop][d['valid'][:stop]]
        self.assertAlmostEqual(float(observed.mean()),float(d['mean']),places=5)
        self.assertAlmostEqual(float(observed.std()),float(d['std']),places=5)
    def test_forward_fill_preserves_latest_observation(self):
        d=self.d; raw=d['raw']; fill=d['filled']; mask=d['valid']
        np.testing.assert_array_equal(raw[mask],fill[mask])
        later=~mask[1:]
        np.testing.assert_array_equal(fill[1:][later],fill[:-1][later])
    def test_missing_targets_excluded(self):
        p=np.array([[11.,900.]]);y=np.array([[10.,0.]])
        s=score(p,y,y>0)
        self.assertAlmostEqual(s['mae_kmh'],KMH,places=5)
        self.assertEqual(s['valid_targets'],1)
    def test_graph_and_aggregation(self):
        d=self.d; A=d['adj']; norm=d['norm']
        np.testing.assert_allclose(A,A.T); self.assertTrue((np.diag(A)==1).all())
        np.testing.assert_allclose(norm@d['node'][100],d['neighbor'][100],atol=2e-6)
    def test_staleness_uses_full_history(self):
        d=self.d;n=int(np.flatnonzero(d['sensor_ids'].astype(str)=='774067')[0])
        t=int(np.flatnonzero(d['timestamps']=='2012-06-09 13:45:00')[0])
        self.assertEqual(int(d['age_minutes'][t,n]),585)
        self.assertTrue((d['age_minutes'][d['valid']]==0).all())
        p=np.flatnonzero(d['valid'][:t+1,n])[-1]
        self.assertEqual(t-int(d['age_minutes'][t,n])/5,p)

if __name__=='__main__':unittest.main()
