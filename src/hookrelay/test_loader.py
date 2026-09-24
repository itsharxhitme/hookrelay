import pytest
import json
from pathlib import Path
from hookrelay.json_fixture import load_fixture

def test_load_fixture_no_crash(tmp_path: Path):
    
    dummy_file = tmp_path / 'sample.json'
    
    dummy_data = {
        "name": "test_user1",
        "age":21,
        "email":"abcd@gmail.com"
    }
    dummy_file.write_text(json.dumps(dummy_data))
    
    loaded_data = load_fixture(dummy_file, required_key='email')
    
    assert loaded_data == dummy_data
 
def test_load_fixture_empty_json_file(tmp_path: Path):
    
    dummy_file = tmp_path / 'sample.json'
    
    dummy_file.touch()
    
    with pytest.raises(json.JSONDecodeError):
        load_fixture(dummy_file, required_key="email")
     
def test_load_fixture_broken_json_syntax(tmp_path: Path):
    
    dummy_file = tmp_path / 'sample.json'
    
    dummy_file.write_text("{ 'invalid_json': ")
    
    with pytest.raises(json.JSONDecodeError):
        load_fixture(dummy_file, required_key="email")
   
           
def test_load_fixture_missing_required_key(tmp_path: Path):
    
    dummy_file = tmp_path / 'sample.json'
    
    dummy_data = {
        "name": "test_user1",
        "age":21,
    }
    dummy_file.write_text(json.dumps(dummy_data))
    with pytest.raises(ValueError) as excinfo:
        load_fixture(dummy_file, required_key="email")  
    
    assert f"Missing Required Field : email | file path : {dummy_file}" in str(excinfo.value)      
    
def test_load_fixture_top_level_list(tmp_path: Path):
    dummy_file = tmp_path / 'sample.json'
    dummy_file.write_text(json.dumps(["email", "user@example.com"]))
    
    with pytest.raises(TypeError) as excinfo:
        load_fixture(dummy_file, required_key="email")
        
    assert "Expected JSON object (dict), got list" in str(excinfo.value)