import pytest
import json
from hookrelay.canonical import canonical_json_bytes, parse_json_bytes

def test_key_order_equivalence():
    
    test_obj1 = {
        "name": "abc",
        "age":21
    }
    
    test_obj2 = {
        "age":21,
        "name": "abc"
    }

    assert canonical_json_bytes(test_obj1) == canonical_json_bytes(test_obj2)

def test_value_diff():
        test_obj1 = {
            "name": "abcd",
            "age":21
        }
        
        test_obj2 = {
            "age":21,
            "name": "abc"
        }
    
        assert canonical_json_bytes(test_obj1) != canonical_json_bytes(test_obj2)
        
def test_whitespace_not_matter_after_parsing():
    
    test_json_str1 = b'{"a": 1, "b": 2}'
    test_json_str2 = b'{"a":1,"b":2}'
    
    parsed1 = json.loads(test_json_str1)
    parsed2 = json.loads(test_json_str2)
    
    assert canonical_json_bytes(parsed1) == canonical_json_bytes(parsed2)
    
def test_array_order_matters():
    
    test_obj1 = {'a': [1,2,3]}
            
    test_obj2 = {'a': [2,3,1]}
    assert canonical_json_bytes(test_obj1) != canonical_json_bytes(test_obj2)

def test_reject_nan():
    test_obj = {"a": float('nan')}
    
    with pytest.raises(ValueError) as excinfo:
        canonical_json_bytes(test_obj)

    assert 'invalid JSON value' in str(excinfo)

def test_reject_inf():
    test_obj = {"a": float('inf')}
        
    with pytest.raises(ValueError,  match=r"invalid JSON value") as excinfo:
        canonical_json_bytes(test_obj)
    

def test_encoder_returns_utf8_bytes():
    
    test_obj = {"a":"é"}
    
    canonalized_bytes = canonical_json_bytes(test_obj)
    
    decoded = canonalized_bytes.decode('utf-8')
    
    assert decoded == '{"a":"é"}'
    
def test_reject_duplicate_keys():
    
    raw = b'{"name": "abc", "name": "abcd"}'
    with pytest.raises(ValueError, match=r"duplicate keys in JSON object"):
        parse_json_bytes(raw)


def test_accept_valid_json():
    test_obj = {
        "name":"abc",
        "age":21
    }
    
    raw_bytes = canonical_json_bytes(test_obj)
        
    parsed_obj = parse_json_bytes(raw_bytes)
    
    assert test_obj == parsed_obj
    
def test_complete_check():
    test_obj = {
        "name":"abc",
        "age":21
    }
    
    canonalized_bytes = canonical_json_bytes(test_obj)   
        
    parsed_obj = parse_json_bytes(canonalized_bytes)
    
    re_canonalized_bytes = canonical_json_bytes(parsed_obj)   
        
    assert re_canonalized_bytes == canonalized_bytes