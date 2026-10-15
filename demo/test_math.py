"""Verify manual GCN gradients and label split invariants."""
import unittest
import numpy as np
import scipy.sparse as sp
from train import adjacency, load_data, loss_grads

class MathTest(unittest.TestCase):
    def test_manual_gradients_match_finite_difference(self):
        a=adjacency(4,[(0,1),(1,2),(2,3)])
        x=sp.csr_matrix([[1.,.2],[.1,.7],[.3,.9],[.8,.4]])
        b=a@x
        w1=np.array([[.3,-.8],[.5,.2]])
        w2=np.array([[.2,-.1],[-.4,.6]])
        y=np.array([0,1,0,1]);train=np.array([0,2])
        _,grads=loss_grads(b,a,w1,w2,y,train,.005)
        eps=1e-6
        for w,grad in zip([w1,w2],grads):
            for index in np.ndindex(w.shape):
                old=w[index]
                w[index]=old+eps;plus=loss_grads(b,a,w1,w2,y,train,.005)[0]
                w[index]=old-eps;minus=loss_grads(b,a,w1,w2,y,train,.005)[0]
                w[index]=old
                self.assertAlmostEqual(grad[index],(plus-minus)/(2*eps),places=7)

    def test_cora_split_and_representation(self):
        x,y,edges,train,val,test,*_=load_data()
        self.assertEqual(x.shape,(2708,1433))
        self.assertEqual(len(edges),5278)
        self.assertEqual(len(set(train)&set(val)),0)
        self.assertEqual(len(set(train)&set(test)),0)
        self.assertEqual(len(set(val)&set(test)),0)
        self.assertEqual([len(train),len(val),len(test)],[140,500,1000])
        np.testing.assert_array_equal(np.bincount(y[train]),np.repeat(20,7))
        np.testing.assert_allclose(np.asarray(x.sum(1)).ravel(),1.)

if __name__=='__main__': unittest.main()
