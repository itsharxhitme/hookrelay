Ques -> What does a Python type hint guarantee at runtime, and what does it not guarantee?
Ans -> Python type hints does not affect the execution at runtime, these are useful for IDE's for provind recommendations and for tools to compute and specify errors in the code during data flow
runtime validation should be done explicitly to avoid any errors or crash


What I built: I built a running python program with a running function named summarize_event which takes an event, validates it and summarize it 
What I broke: I try to ran the program from a repo without installing the project or running it in editable mode, tested the error handling of the function summarize_event
What proved it works: i ran the commands and the returns i got are great and as expected
What I still cannot explain: i can explain all of it 