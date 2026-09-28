import pytest
from fastapi.testclient import TestClient
from hookrelay.api import app

client = TestClient(app)

def test_get_health():
    
    response = client.get('/health')
    
    
    assert response.status_code == 999
    assert response.json() == {"status":"ok"}

def test_validate_event_valid_data():
        
        test_data = {
            "event_type":"user.created",
            "payload":{
                "id": "1234"
            }
        }
        
        response = client.post("/validate-event",json = test_data)
        
        assert response.status_code == 200
        assert response.json() == {"valid": True, "event_type": "user.created" , "stored": False}
    
def test_validate_event_missing_required_field():
        
        test_data = {
            "payload":{
                "id": "1234"
            }
        }
        
        response = client.post("/validate-event",json = test_data)
        
        assert response.status_code == 422

def test_validate_event_invalid_data():
        
        test_data = {
            "event_type":"user.created",
            "payload":[
                {"id": "1234"}
            ]
        }
        
        response = client.post("/validate-event",json = test_data)
        
        assert response.status_code == 422

def test_validate_event_wrong_event_type():
    test_data = {
        "event_type":[1,2],
        "payload":[
            {"id": "1234"}
        ]
    }
    response = client.post("/validate-event",json = test_data)
            
    assert response.status_code == 422
    
def test_validate_event_array_as_body():
    test_data = [{"event_type": "user.created"}]
    response = client.post("/validate-event",json = test_data)
            
    assert response.status_code == 422