"""Run: python -m unittest discover -s tests -p 'test_*.py'"""
import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
from positions_npz_to_json import convert

class TestConverter(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'sample.npz'
        body=np.zeros((3,6,3));body[:,0]=[.305,1.54,0];body[:,1]=[.4,1.1,0];body[:,2]=[.4,.85,0]
        body[:,3]=[-.305,1.54,0];body[:,4]=[-.4,1.1,0];body[:,5]=[-.4,.85,0]
        hands=np.zeros((3,2,21,3));hands[:,0,:,:]=body[:,2,None,:];hands[:,1,:,:]=body[:,5,None,:]
        np.savez(self.path,body_points=body,hand_points=hands)
    def tearDown(self):self.tmp.cleanup()
    def test_good(self):
        d=convert(self.path,'SYNTHETIC',30)
        self.assertEqual(len(d['frames']),3)
        self.assertEqual(d['frames'][2]['time_ms'],67)
    def test_wrong_shape(self):
        np.savez(self.path,body_points=np.zeros((3,55,3)),hand_points=np.zeros((3,2,21,3)))
        with self.assertRaisesRegex(ValueError,'shape'):convert(self.path,'SYNTHETIC',30)
    def test_wrist_discontinuity(self):
        with np.load(self.path) as f:body=f['body_points'];hands=f['hand_points']
        hands[0,0,0]=[3,3,3]
        np.savez(self.path,body_points=body,hand_points=hands)
        with self.assertRaisesRegex(ValueError,'wrist'):convert(self.path,'SYNTHETIC',30)

if __name__=='__main__':unittest.main()
