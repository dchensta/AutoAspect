from pathlib import Path
import pandas as pd
import os

if __name__ == "__main__" :
    filepath = "LORELEI_semparse"
    json_filepath = "LORELEI_semparse_json" 

    for file in Path(filepath).glob("*.txt"):
        print(f'Processing {file.name}...')
        print(os.getcwd())
        print(os.path.isfile(file))
        with open(file) as semparse_file :
            text = semparse_file.read()
            sents = text.split("------------------------------------------------------")
            sents = sents[:-2]
        
            filename = file.name[:-13]
            new_path = os.path.join(json_filepath, filename)
            if not os.path.exists(new_path): os.mkdir(new_path)   
            os.chdir(new_path)
            sent_count = 1
            for sent in sents :
                sent_filename = filename + "_sent_" + str(sent_count) + ".json" 
                with open(sent_filename, "w") as output :
                    output.write(sent)
                sent_count += 1
            os.chdir("../..")