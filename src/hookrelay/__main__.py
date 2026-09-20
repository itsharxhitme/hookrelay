import argparse
import sys
import json
from hookrelay.events import summarize_event

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "event_name", 
        type=str,
        nargs="?",  
    )
    args = parser.parse_args(sys.argv[1:])
    try:
        if args.event_name is None:
            raise ValueError("Event Name is not provided")
        response = summarize_event(event_name=args.event_name)
        print(json.dumps(response))
    except ValueError as e:
        print(e)