import urllib.request
import json

def test_full_system():
    # 1. Check index.html
    res = urllib.request.urlopen('http://127.0.0.1:8000/')
    html = res.read().decode('utf-8')
    assert 'subtab-expected-waste' in html, 'Missing subtab-expected-waste in HTML'
    assert 'subtab-after-prediction' in html, 'Missing subtab-after-prediction in HTML'
    assert 'res-risk-badge' in html, 'Missing res-risk-badge in HTML'
    assert 'res-risk-meter-fill' in html, 'Missing res-risk-meter-fill in HTML'
    assert 'slider-ap-speed' in html, 'Missing slider-ap-speed in HTML'
    print('[PASS] 1. HTML structure and subtab elements validated.')

    # 2. Check /api/predict-expected
    data = {
        'batch_id': 'TEST-EXP-01',
        'machine_id': 'M03',
        'fabric_type': 'Cotton',
        'shift': 'Morning',
        'operator': 'Priya S.',
        'total_production': 1000,
        'waste_quantity': None,
        'production_speed': 920,
        'machine_age': 5.0,
        'last_maintenance_date': '2026-05-01',
        'humidity': 55.0,
        'temperature': 26.0
    }
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/predict-expected',
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    res_json = json.loads(res.read().decode('utf-8'))
    assert 'expected_waste_percentage' in res_json
    assert 'risk_level' in res_json
    assert 'risk_score' in res_json
    print(f'[PASS] 2. /api/predict-expected: Expected Waste={res_json["expected_waste_percentage"]}%, Risk={res_json["risk_level"]}, RiskScore={res_json["risk_score"]}')

    # 3. Check /api/predict for After-Prediction initial batch
    data_ap = {
        'batch_id': 'TEST-AP-01',
        'machine_id': 'M02',
        'fabric_type': 'Silk',
        'shift': 'Night',
        'operator': 'Rajesh K.',
        'total_production': 1000,
        'waste_quantity': 85.0,
        'production_speed': 940,
        'machine_age': 6.2,
        'last_maintenance_date': '2026-05-15',
        'humidity': 42.0,
        'temperature': 31.0
    }
    req2 = urllib.request.Request(
        'http://127.0.0.1:8000/api/predict',
        data=json.dumps(data_ap).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res2 = urllib.request.urlopen(req2)
    res2_json = json.loads(res2.read().decode('utf-8'))
    assert 'waste_percentage' in res2_json
    assert 'risk_level' in res2_json
    assert 'root_cause_analysis' in res2_json
    print(f'[PASS] 3. /api/predict: Waste={res2_json["waste_percentage"]}%, Risk={res2_json["risk_level"]}, Primary Cause={res2_json["root_cause_analysis"]["primary_cause"]["title"]}')

    # 4. Check /api/root-cause/simulate for After-Prediction simulator
    sim_req_data = {
        'batch': data_ap,
        'modified_params': {
            'production_speed': 680,
            'humidity': 58.0,
            'maintenance_age_days': 10,
            'temperature': 24.0
        }
    }
    req3 = urllib.request.Request(
        'http://127.0.0.1:8000/api/root-cause/simulate',
        data=json.dumps(sim_req_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res3 = urllib.request.urlopen(req3)
    res3_json = json.loads(res3.read().decode('utf-8'))
    assert 'simulated_waste_percentage' in res3_json or 'simulated_waste_pct' in res3_json
    assert 'simulated_risk_level' in res3_json
    assert 'estimated_kg_saved' in res3_json or 'estimated_waste_saved_kg' in res3_json
    sim_waste = res3_json.get('simulated_waste_percentage', res3_json.get('simulated_waste_pct'))
    saved_kg = res3_json.get('estimated_kg_saved', res3_json.get('estimated_waste_saved_kg'))
    print(f'[PASS] 4. /api/root-cause/simulate: Simulated Waste={sim_waste}%, Simulated Risk={res3_json["simulated_risk_level"]}, Saved Kg={saved_kg} kg')

    print('\nALL FRONTEND AND BACKEND INTEGRATION CONTRACTS VERIFIED!')

if __name__ == '__main__':
    test_full_system()
