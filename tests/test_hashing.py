import pytest
from hookrelay.hashing import sha256_hex, hash_json_obj

def test_comare_hash_same_input():
    
    test_data = b'hello'
    assert sha256_hex(test_data) == sha256_hex(test_data)
    

def test_comare_hash_different_input():
    
    test_data1 = b'hello'
    test_data2 = b'world'
    assert sha256_hex(test_data1) != sha256_hex(test_data2)

def test_hash_value():
    test_data = b''
    assert sha256_hex(test_data) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    
def test_compare_hash_same_object_different_order():
    test_data1 = {
        "name": "abc",
        "age": 21
    }
    test_data2 = {
        "age": 21,
        "name": "abc"
    }
    assert hash_json_obj(test_data1) == hash_json_obj(test_data2)

def test_compare_hash_different_object():
    test_data1 = {
        "name": "abc",
        "age": 21
    }
    test_data2 = {
        "age": 22,
        "name": "abc"
    }
    assert hash_json_obj(test_data1) != hash_json_obj(test_data2)

def test_hash_non_finite_value():
    test_data = {
        "name": "abc",
        "age": float('nan')
    }
    
    with pytest.raises(ValueError, match="invalid JSON value"):
        hash_json_obj(test_data)