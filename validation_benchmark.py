import urllib.request
import urllib.error
import json
import time

def run_validation():
    print("=== AeroJoint Validation Benchmark ===")
    print("Material: T300/5208 Graphite/Epoxy")
    print("Layup: [0 / 45 / -45 / 90]_s")
    print("Test: Open-Hole Tension (Whitney-Nuismer Data)")
    
    # Experimental Data from Whitney & Nuismer (1974)
    exp_failure_load = 9829.8
    characteristic_distance_d0 = 1.016
    
    # We apply a nominal 1000 N far-field tension to the model
    # The solver will return lambda_f. Expected lambda_f = exp_failure_load / 1000 N
    nominal_load = 1000.0
    expected_lambda_f = exp_failure_load / nominal_load

    url = "http://127.0.0.1:8000/api/analysis/run"

    payload = {
        "width": 100.0,
        "height": 38.1,
        "delta_T": 0.0,
        "plies": [
            {"material_id": "T300_5208", "angle": 0.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": -45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 90.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 90.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": -45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 45.0, "thickness": 0.125},
            {"material_id": "T300_5208", "angle": 0.0, "thickness": 0.125}
        ],
        "holes": [
            {
                "x": 50.0, 
                "y": 19.05, 
                "diameter": 6.35,
                "load_magnitude": 0.0, # 0.0 triggers default OHT far-field nominal load (1000N)
                "load_angle": 0.0, 
                "torque": 0.0,
                "is_open": True 
            }
        ],
        "constraint_type": "fixed",
        "characteristic_distance": characteristic_distance_d0,
        "failure_criterion": "Hashin",
        "mesh_size_global": 4.0,
        "mesh_size_hole": 0.5,
        "enable_pdm": False
    }
    
    print(f"\nSending API Request for Open-Hole Tension Analysis...")
    print(f"Applied Nominal Far-field Load: {nominal_load} N")
    print(f"Applied Characteristic Distance (d0) for PSC: {characteristic_distance_d0} mm")
    
    start = time.time()
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"API Error: {e}")
        return
        
    calc_time = time.time() - start
    
    min_mos = result['min_mos']
    lambda_f = min_mos + 1.0
    predicted_failure_load = nominal_load * lambda_f
    error_percent = ((predicted_failure_load - exp_failure_load) / exp_failure_load) * 100

    
    print(f"\n=== AeroJoint Prediction Results ===")
    print(f"Computation Time: {result['computation_time_ms']:.0f} ms (API call took {calc_time*1000:.0f} ms)")
    print(f"Minimum Margin of Safety (MoS): {min_mos:.4f}")
    print(f"Critical Failure Lambda (Lambda_f): {lambda_f:.4f}")
    print(f"Critical Ply:                   #{result['critical_ply']} ({result['critical_angle']}°)")
    print(f"Critical Mode:                  {result['critical_mode']}")
    print(f"Governing Criterion:            {result['governing_criterion']}")
    print("-" * 40)
    print(f"Experimental Failure Load:      {exp_failure_load:.1f} N")
    print(f"AeroJoint Predicted Load:       {predicted_failure_load:.1f} N")
    print(f"Prediction Error:               {error_percent:+.2f}%")
    
    if abs(error_percent) <= 10.0:
        print("\n[PASS] Model prediction is within acceptable aerospace engineering tolerance (10%)!")
    else:
        print("\n[WARNING] Prediction differs significantly from experimental data. Mesh convergence or material tuning required.")

if __name__ == "__main__":
    run_validation()
