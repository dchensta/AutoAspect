import json 
import spacy
from pathlib import Path
import pandas as pd
import os

PTB_VERBS = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
nlp = spacy.load("en_core_web_lg")

def event_nominal_rule(events_hat, aspects_hat, step_nos, vn_nominals) :
    nominals = vn_nominals #[i] later on
    for nom in nominals :
        for span, sense in nom.items():
            print(f"span: {span}, sense: {sense}")
            events_hat.append(sense)
            aspects_hat.append("PROCESS")
            step_nos.append("Step 1")
    return events_hat, aspects_hat, step_nos

def extract_event_nominals(filepath, sent) :
    print("Analyzing sentence: ", sent)
    print("Current filepath: ", filepath)
    vn_nominals = []
    with open(filepath) as my_file :
        data = json.load(my_file)
        props = data["props"]
        for prop in props :
            #print(prop.keys()) #dict_keys(['sense', 'mainEvent', 'events', 'spans'])
            #events and spans are also dicts
            #print(prop["sense"])
            prop_dict = {}
            if type(prop["mainEvent"]) != dict :
                sense = prop["sense"]
                print(sense)
                span = ""
                for span_dict in prop["spans"] :
                    span += span_dict["text"] + " "
                span = span[:-1] #remove the last space
                print("span: ", span)
                print("len(span): ", len(span))
                doc = nlp(span)
                span_is_verb = False
                #Check span for verbs
                for token in doc :
                    if token.tag_ in PTB_VERBS: 
                        print(token.text)
                        span_is_verb = True
                if span_is_verb == False :
                    print("False span_is_verb")
                    prop_dict[span] = sense
                    vn_nominals.append(prop_dict)
    print("vn_nominals: ", vn_nominals)
    print("------------------------------------")
    return vn_nominals

def get_sentences(filepath) : #for one individual file
    with open(filepath, "r") as gold_file :
        df = pd.read_csv(gold_file)
        file_sents = []
        sentences = df["Sentence"]
        for sent in sentences :
            if type(sent) == str :
                file_sents.append(sent)
        file_sents.pop()
        print("file_sents: ", file_sents, '\n')
        return file_sents

def get_sent_from_idx(idx, semparse_path, file_sents) :
    #Doesn't accept 0 as an idx. Must start from 1.
    print("looking for idx: ", idx)
    idx_str = str(idx)
    if idx <= 9 :
        idx_str = "0" + idx_str
    semparse_split = semparse_path.split("/")
    semparse_filename = semparse_split[1]
    sent_path = semparse_path + "/" + semparse_filename + "_sent_" + idx_str + ".json"
    print("sent_path: ", sent_path)
    print("file_sents[idx]", file_sents[idx-1])
    event_nominals = extract_event_nominals(sent_path, file_sents[idx-1]) #append to master nominals list for that file
    events_hat, aspects_hat, step_nos = event_nominal_rule([],[],[],event_nominals)
    #print(f"events_hat: {events_hat}, aspects_hat: {aspects_hat}, step_nos: {step_nos}")
    return events_hat, aspects_hat, step_nos

def event_nominals(path_name) :
    EVENTS = []; ASPECTS = []; STEPS = []
    for path in Path("gold_files").rglob("*.csv") : #glob needs to be generated each time
        path_short = path.name[:-4]
        #Find yo file.
        print("path_short: ", path_short)
        print("path_name: ", path_name)
        if path_short == path_name:
            file_sents = get_sentences(path)
            semparse_path = "LORELEI_semparse_json_cleaned/" + path_short
            print("semparse_path: ", semparse_path)
            #Iterate through each sentence in the file.
            for idx in range(len(file_sents)) :
                idx = idx + 1
                if idx == len(file_sents) :
                    break
                events_hat, aspects_hat, step_nos = get_sent_from_idx(idx, semparse_path, file_sents)
                EVENTS.append(events_hat)
                ASPECTS.append(aspects_hat)
                STEPS.append(step_nos)

    print("EVENTS: ", EVENTS)
    print("ASPECTS: ", ASPECTS)
    print("STEPS: ", STEPS)
    print("\n")

if __name__ == "__main__" :
    # path_names = ["LORELEI_0147_2000_1023_Gold_3-13-21", 
    # "LORELEI_0152_2000_1208_Gold_3-13-21",
    # "LORELEI_0153_2000_1214_Gold_3-13-21",
    # "LORELEI_0155_2000_1228_Gold_3-13-21"
    # ]
    path_names = ["LORELEI_0147_2000_1023_Gold_3-13-21"]
    for path_name in path_names :
        event_nominals(path_name)