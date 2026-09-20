


def summarize_event(event_name : str) -> dict[str,str]:
    
    cleaned_event_name = event_name.strip(' ')
    if cleaned_event_name == '':
        raise ValueError("Invalid Event Name")
    
    return {
        "event_name" : cleaned_event_name,
        "status" : "received",
        "service" : "hookrelay"
    }
