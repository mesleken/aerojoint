"""
CLT Modülü Doğrulama Testleri
Referans: Daniel & Ishai, "Engineering Mechanics of Composite Materials"
          NASA/TM-2011-217125
"""
import numpy as np
import pytest
from app.core.clt import OrthotropicMaterial, Ply, Laminate, CLTEngine

T300_5208 = OrthotropicMaterial(
    name="T300/5208", E1=181_000, E2=10_300, G12=7_170, nu12=0.28,
    Xt=1500, Xc=1500, Yt=40, Yc=246, S12=68
)

def test_Q_matrix_diagonal():
    Q = CLTEngine.compute_Q(T300_5208)
    assert Q[0,0] > Q[1,1], "E1 > E2 ise Q11 > Q22 olmalı"
    assert Q[2,2] == T300_5208.G12

def test_Qbar_at_zero_degrees():
    Q = CLTEngine.compute_Q(T300_5208)
    Qbar = CLTEngine.compute_Qbar(Q, 0.0)
    np.testing.assert_array_almost_equal(Q, Qbar)

def test_Qbar_at_90_degrees():
    Q = CLTEngine.compute_Q(T300_5208)
    Qbar = CLTEngine.compute_Qbar(Q, 90.0)
    assert np.isclose(Qbar[0,0], Q[1,1], rtol=1e-6)
    assert np.isclose(Qbar[1,1], Q[0,0], rtol=1e-6)

def test_symmetric_laminate_B_zero():
    plies = [Ply(T300_5208, a, 0.125) for a in [0, 45, -45, 90, 90, -45, 45, 0]]
    laminate = Laminate(plies)
    A, B, D = CLTEngine.compute_ABD(laminate)
    assert np.allclose(B, 0, atol=1e-6)

def test_quasi_isotropic_A11_eq_A22():
    plies = [Ply(T300_5208, a, 0.125) for a in [0, 45, -45, 90, 90, -45, 45, 0]]
    laminate = Laminate(plies)
    A, B, D = CLTEngine.compute_ABD(laminate)
    assert np.isclose(A[0,0], A[1,1], rtol=0.01)

def test_single_ply_stress_recovery():
    plies = [Ply(T300_5208, 0, 0.125)]
    laminate = Laminate(plies)
    N = np.array([100.0, 0.0, 0.0])
    M = np.array([0.0, 0.0, 0.0])
    results = CLTEngine.compute_ply_stresses(laminate, N, M)
    sigma1 = results[0]['positions']['middle']['sigma_local'][0]
    assert np.isclose(sigma1, 100.0/0.125, rtol=0.01)
