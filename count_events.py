from pathlib import Path
import pandas as pd

for file in Path("gold_files").rglob("*.csv") :
    print(f'Processing {file.name}...')
    gold = pd.read_csv(file)
    col_list = ['Sentence', 'Gold Events', 'Gold Aspects', 'Events', 'Auto Aspect', "Step #"]
    col_dict = {key: None for key in col_list}

    #Get columns as arrays.
    events_col = gold["Event"]
    event_count = 0
    for event in events_col :
        if type(event) == str :
            event_count += 1
    print("Event count for this file: ", event_count)
