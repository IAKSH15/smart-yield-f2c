import urllib.request
import json

base_url = 'http://127.0.0.1:8000'

def run_tests():
    # 1. Health check
    res = urllib.request.urlopen(f'{base_url}/')
    data = json.loads(res.read().decode('utf-8'))
    print("1. Backend Health Check: OK - " + data['app'])

    # 2. Section 8 Pricing Engine exact worked example
    calc_payload = json.dumps({
        'crop_type': 'Tomatoes',
        'mandi_base_price': 22.0,
        'shelf_life_days': 2,
        'transport_distance_km': 25.0,
        'weather_risk': 'None'
    }).encode('utf-8')
    req = urllib.request.Request(f'{base_url}/api/pricing/calculate', data=calc_payload, headers={'Content-Type': 'application/json'})
    pricing = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    computed = pricing['computed_osp']
    assert computed == 24.0, f"Expected 24.0, got {computed}"
    print(f"2. Section 8 Pricing Formula: PASSED -> Computed OSP = Rs {computed:.2f}/kg (Mandi 22 + Shelf 3 - Transport 1 + Weather 0)")

    # 3. Listing retrieval
    res_list = urllib.request.urlopen(f'{base_url}/api/listings')
    listings = json.loads(res_list.read().decode('utf-8'))
    assert len(listings) >= 1
    sample_id = listings[0]['id']
    crop = listings[0]['crop_type']
    floor = listings[0]['computed_osp']
    print(f"3. Listings API: PASSED -> Found {len(listings)} active listing(s). Sample: {crop} @ Floor Rs {floor:.2f}/kg")

    # 4. Bid Evaluation - Section 8 Rejected Bid (Rs 19 < Rs 24 floor)
    reject_bid = json.dumps({'buyer_id': 2, 'bid_price': 19.0, 'quantity': 500.0}).encode('utf-8')
    req_rej = urllib.request.Request(f'{base_url}/api/listings/{sample_id}/bid', data=reject_bid, headers={'Content-Type': 'application/json'})
    res_rej = json.loads(urllib.request.urlopen(req_rej).read().decode('utf-8'))
    assert res_rej['accepted'] is False
    print("4. Section 8 Rejected Bid (Rs 19/kg): PASSED -> Rejected correctly below floor!")

    # 5. Bid Evaluation - Section 8 Accepted Bid (Rs 28 >= Rs 24 floor)
    accept_bid = json.dumps({'buyer_id': 2, 'bid_price': 28.0, 'quantity': 500.0}).encode('utf-8')
    req_acc = urllib.request.Request(f'{base_url}/api/listings/{sample_id}/bid', data=accept_bid, headers={'Content-Type': 'application/json'})
    res_acc = json.loads(urllib.request.urlopen(req_acc).read().decode('utf-8'))
    assert res_acc['accepted'] is True
    order_id = res_acc['order_id']
    total = res_acc['total_amount']
    print(f"5. Section 8 Accepted Bid (Rs 28/kg): PASSED -> Order #{order_id} created with Rs {total:.2f} locked in UPI Escrow (Held)")

    # 6. Delivery Geofence + OTP release (Shield 2)
    verify_payload = json.dumps({'otp': '7842'}).encode('utf-8')
    req_verify = urllib.request.Request(f'{base_url}/api/orders/{order_id}/verify-delivery', data=verify_payload, headers={'Content-Type': 'application/json'})
    res_verify = json.loads(urllib.request.urlopen(req_verify).read().decode('utf-8'))
    assert res_verify['success'] is True
    assert res_verify['escrow_status'] == 'Released'
    print("6. Escrow Shield 2 Settlement: PASSED -> OTP verified, funds Released instantly to farmer!")

    # 7. FPO Aggregation Check
    res_fpo = urllib.request.urlopen(f'{base_url}/api/fpo/lots')
    fpo_data = json.loads(res_fpo.read().decode('utf-8'))
    print("7. FPO Aggregation Module: PASSED -> " + fpo_data['hub_name'] + " (" + fpo_data['logistics_savings_percent'] + ")")

    print("\n===> ALL 7 BACKEND END-TO-END FLOW TESTS COMPLETED SUCCESSFULLY! <===")

if __name__ == '__main__':
    run_tests()
