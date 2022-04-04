import requests
import json
import pandas as pd

test_sample = json.dumps({'data': [[0,1,8,1,0,0,1,0,0,0,0,0,0,0,12,1,0,0,0.5,0.3,0.610327781,7,1,-1,0,-1,1,1,1,2,1,65,1,0.316227766,0.669556409,0.352136337,3.464101615,0.1,0.8,0.6,1,1,6,3,6,2,9,1,1,1,12,0,1,1,0,0,1],[4,2,5,1,0,0,0,0,1,0,0,0,0,0,5,1,0,0,0.9,0.5,0.771362431,4,1,-1,0,0,11,1,1,0,1,103,1,0.316227766,0.60632002,0.358329457,2.828427125,0.4,0.5,0.4,3,3,8,4,10,2,7,2,0,3,10,0,0,1,1,0,1]]})
test_sample = str(test_sample)

def test_ml_service(scoreurl, scorekey):
    assert scoreurl != None

    if scorekey is None:
        headers = {'Content-Type':'application/json'}
    else:
        headers = {'Content-Type':'application/json', 'Authorization':('Bearer ' + scorekey)}

    resp = requests.post(scoreurl, test_sample, headers=headers)
    assert resp.status_code == requests.codes.ok
    assert resp.text != None
    assert resp.headers.get('content-type') == 'application/json'
    assert int(resp.headers.get('Content-Length')) > 0

# test_data = [FALSE,FALSE,TRUE,	0,	197,	0,	56,	51,	0,	0.434448987,	0.08145,	0.024253,	0,	49,	46,	53,	41,	FALSE,	FALSE,	FALSE,	0,	1,	0,	FALSE,	1500,	0], [FALSE,FALSE,TRUE,	0,	197,	0,	56,	51,	0,	0.434567988,	0.087761998,	-0.020750999,	0,	49,	46,	52,	41,	FALSE,	FALSE,	FALSE,	0,	1,	0,	FALSE,	1500,	0]
# df = pd.DataFrame(test_data)
# sample_df = prepare_data(df)


