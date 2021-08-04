import pandas as pd
import re
import subprocess

filepath = "LORELEI_0152_2000_1208_Gold_3-13-21.csv"
filename = filepath[:-4]
output_filename = filename + "_semparse.txt"
with open(output_filename, "w") as output :
    with open(filepath, "r") as csv_file :
        df = pd.read_csv(csv_file)
        text = df["Sentence"]
        for sent in text :
            #Extract only the sentences (every third row)
            if type(sent) != str :
                continue

            new_sent = re.sub(" ", "%20", sent)
            new_sent = re.sub("[.!?\"\']", "", new_sent)

            curl = "curl localhost:8080/predict/semantics?utterance=" + new_sent +" | python -m json.tool"
            byte_result = subprocess.check_output(curl, shell=True)
            result = byte_result.decode('UTF-8')

            output.write("SENTENCE: " + sent + "\n")
            output.write(result)
            output.write("\n------------------------------------------------------\n")