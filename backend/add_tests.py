import numpy as np
from app.core.clt import OrthotropicMaterial, Laminate, Ply, CLTEngine

path = r'C:\Users\maozk\.gemini\antigravity-cli\brain\dd0dc520-031d-4002-b31e-5d574c739362\scratch\math_validation.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

new_tests = '''
# ==========================================
# TEST 13: Transformation Round-Trip Test
# ==========================================
print("\\n" + "="*70)
print("TEST 13: Transformation Round-Trip Test")
print("="*70)
clt = CLTEngine()
theta = 35.0
sigma_local = np.array([100.0, -50.0, 25.0])
eps_local = np.array([0.01, -0.005, 0.002]) # engineering shear

# Transform local to global
T_sigma = clt.transform_stress_to_local(np.eye(3), theta) # T_sigma matrix is for global->local
# Wait, transform_stress_to_local takes global and gives local: local = T * global.
# To go local->global, we need T_inv.
T_inv = np.linalg.inv(T_sigma)
sigma_global = T_inv @ sigma_local

# Transform global back to local
sigma_recovered = clt.transform_stress_to_local(sigma_global, theta)
test("Stress Round-trip", np.allclose(sigma_local, sigma_recovered))

# ==========================================
# TEST 14: Pure Thermal Load on Isotropic Laminate
# ==========================================
print("\\n" + "="*70)
print("TEST 14: Pure Thermal Load on Isotropic Laminate")
print("="*70)
iso_mat = OrthotropicMaterial(
    name="Isotropic", E1=70000, E2=70000, G12=70000/(2*(1+0.3)), nu12=0.3,
    Xt=100, Xc=100, Yt=100, Yc=100, S12=50,
    alpha1=2.3e-5, alpha2=2.3e-5 # Aluminum CTE
)
iso_lam = Laminate([Ply(iso_mat, 0, 1.0), Ply(iso_mat, 45, 1.0), Ply(iso_mat, 90, 1.0)])
# Apply only thermal load (delta_T = 100)
iso_thermal = clt.compute_ply_stresses(iso_lam, np.zeros(3), np.zeros(3), delta_T=100.0)
# Isotropic material free expansion should yield ZERO thermal residual stresses
stress_0 = iso_thermal[0]['positions']['middle']['sigma_local']
stress_45 = iso_thermal[1]['positions']['middle']['sigma_local']
test("Isotropic thermal stress ~ 0", np.allclose(stress_0, 0, atol=1e-5) and np.allclose(stress_45, 0, atol=1e-5))
'''

code = code.replace('print("\\n" + "="*70)\nprint("SUMMARY:', new_tests + '\nprint("\\n" + "="*70)\nprint("SUMMARY:')

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
