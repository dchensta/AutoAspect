#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 8 23:53:24 2021

@author: Daniel Chen
@email: daniel.chen-1@colorado.edu
"""

import spacy
from pathlib import Path
import pandas as pd
import re
import json

#Global Variables
nlp = spacy.load("en_core_web_lg")
COPULA = ["is", "am", "are", "be", "been", "being", "were", "was"]
AUX  = ["has", "have", "will", "would", "can", "could", "shall", "should"]
VN_STATES= ["want-32.1", "long-32.2", "try-61.1", "intend-61.2", "wish-62",
         "allow-64.1", "let-64.2", "admit-64.3", "forbid-64.4", "tingle-40.8.2",
         "pain-40.8.1", "stimulus_subject-30.4", "keep-15.2", "support-15.3",
         "contain-15.4", "being_dressed-41.3.3", "simple_dressing-1.3.1",
         "function-105.2.1", "lodge-46", "exist-47.1", "bulge-47.5.3", "meander-47.7",
         "contiguous_location-47.8", "terminus-47.9", "put_spatial-9.2-1", "cling-22.5",
         "entity_specific_modes_being-47.2", "light_emission-43.1",
         "smell_emission-43.3", "sound_emission-43.2", "sound_existence-47.4",
         "substance_emission-43.4-1", "swarm-47.5.1-1", "animal_sounds-38",
         "carve-21.2-1", "modes_of_being_with_motion-47.3", "snooze-40.4",
         "body_internal_states-40.6", "spatial_configuration-47.6",
         "peer-30.3", "see-30.1"]
PTB_VERBS = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]

class AutoAspect :
    def __init__(self, filepath, semparse_filepath, semparse_json_filepath, tac_path, parser) :
        self.gold_files = Path(filepath).rglob("*.csv")
        self.semparse_path = semparse_filepath
        self.semparse_json_path = semparse_json_filepath
        self.tac_dict = self.extract_tac(tac_path)
        print(self.tac_dict.keys())
        self.parser = parser

    def dump(self, obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

    def verb_loop(self, sent, vn_senses, filename) :
        events_hat = []
        aspects_hat = []
        step_nos = []
        root_vf = ""
        vn_idx = -1 #Start at -1, first vn_idx will be 0 at beginning of token loop
        tac_verbs = self.tac_dict[filename]
        '''Step 1: Distinguishing verbs, nonverbal predication, and event nominals.'''
        doc = nlp(sent)
        verbs = []
        prev_vn_senses= []
        for i, token in enumerate(doc) :
            print("token: ", token.text)
            print("pos: ", token.pos_)
            #Variables for Step 3a and Step 4
            prev_token = "" #"being" as prev_token marks a VERB entering Step 4 as ACTIVITY
            next_verb = False
            if i > 0 :
                prev_token = doc[i-1].text
            if i != len(doc) - 1:
                if doc[i+1].tag_ == "VERB" :
                    next_verb = True

            #dump(token) #Uncomment to see all spaCy attributes
            #VERBS + NONVERBAL PREDICATION: predicate nominals/adjectives/locationals (with copula)
            #print(f"POS of {token.text}= {token.pos_}")
            if token.tag_ in PTB_VERBS :
                vn_idx += 1
                verb = token.text
                print("Verb: ", verb)
                verbs.append(verb)

                #Get TAC info.
                ann = ""; vf_tac = ""; t = ""; a = ""
                for v in tac_verbs :
                    if v[0] == verb :
                        ann = v[1]
                        vf_tac = ann[0]; t = ann[1]; a = ann[2]

                if vn_idx < len(vn_senses) :
                    vn_sense = vn_senses[vn_idx]

                tag = str(token.tag_)
                vf = self.get_vf(tag)

                if "complete-55.2" in vn_senses or "stop-55.4-1" in vn_senses:
                    prev_vn_senses = vn_senses

                '''Step 2a: Nonverbal predication and ability modals
                Verbs which occur in the Simple Present cxn and the Past Habitual cxn are annotated
                as HABITUAL.
                '''
                if verb in COPULA and (next_verb == False or token.dep_ == "ROOT"): #buggy on 8/4/21: helping verbs are getting this ann.
                    events_hat.append(verb)
                    aspects_hat.append("State")
                    step_nos.append("Step 2a")
                    print("Step 2a applied.")
                    root_vf = self.get_vf(tag)
                    continue

                if len(vn_senses) == 0 :
                    print("Empty vn_senses")
                if verb in AUX or len(vn_senses) == 0 :#6/11/21 - took out "if verb in copula"
                    continue

                print("Verb in Rules: ", verb)

                '''Step 2b: Categorize verbs based on VerbNet class: either STATE or PROCESS'''
                # print("class_id: ", class_id)
                events_hat.append(verb)

                #if class_id[0] in VN_STATES :
                #print("vn_sense in VN_STATES: ", vn_sense in VN_STATES)
                print("vn_senses: ", vn_senses)
                print("vn_sense: ", vn_sense)
                spacy_step_3 = vf == "3_sing_pres" or vf == "12_sing_pres" or (verb.lower() == token.lemma_ and root_vf == "simple_past")
                tac_step_3 = vf_tac == "v" and t == "n" and a == "-" 
                step_3_bool = None
                if self.parser == "tac" and len(ann) > 0:
                    step_3_bool = tac_step_3
                else :
                    step_3_bool = spacy_step_3

                if any(re.search(vn, vn_sense) != None for vn in VN_STATES):
                    aspects_hat.append("State")
                    step_nos.append("Step 2b")
                    print("Step 2b applied.")
                elif step_3_bool :
                    aspects_hat.append("Habitual")
                    step_nos.append("Step 3")
                    print("Step 3 applied.")
                else : #PROCESS verb -> move on to Step 4
                    '''Step 4: Activity Annotation
                    Verbs that occur in the present progressive, present perfect progressive and past progressive
                    are annotated as ACTIVITY. Verbs which occur with inceptive (VN class begin-55.1
                    and continuative (VN class continue-55.3, sustain-55.6) aspectual auxiliaries are
                    also annotated as ACTIVITY.'''
                    spacy_step_4 = vf == "ppl" or "begin-55.1" == vn_sense \
                        or "continue-55.3" == vn_sense or "sustain-55.6" == vn_sense \
                        or prev_token == "being"
                    tac_step_4 = vf_tac == "v" and (t == "p" or t == "n") and (a == "p" or a == "b")
                    step_4_bool = None
                    if self.parser == "tac" and len(ann) > 0:
                        step_4_bool = tac_step_4
                    else :
                        step_4_bool = spacy_step_4
                            
                    if step_4_bool:
                        aspects_hat.append("Activity")
                        step_nos.append("Step 4")
                        print("Step 4 applied.")
                        continue

                    '''Step 5: Terminative and Completive Auxilaries
                    Verbs which occur with completive aspectual auxilaries are annotated as PERFORMANCE.
                    Verbs which occur with terminative aspectual auxiliaries are annotated as ENDEAVOR'''
                    if len(prev_vn_senses) != 0 :
                        if "complete-55.2" in prev_vn_senses :
                            aspects_hat.append("Performance")
                        elif "stop-55.4" in prev_vn_senses :
                            aspects_hat.append("Endeavor")
                        step_nos.append("Step 5")
                        print("Step 5 applied.")
                        continue

                    '''Step 6: Adverbials'''
                    prep_6 = self.prep_search_6(doc)
                    if prep_6 == "in" :
                        aspects_hat.append("Performance")
                        step_nos.append("Step 6")
                        print("Step 6 applied.")
                        continue
                    elif prep_6 == "for" :
                        aspects_hat.append("Endeavor")
                        step_nos.append("Step 6")
                        print("Step 6 applied.")
                        continue

                    prep_7 = self.prep_search_7(doc)
                    if prep_7 == "around" or prep_7 == "along" or prep_7 == "past" :
                        aspects_hat.append("Endeavor")
                        step_nos.append("Step 7")
                        print("Step 7 applied.")
                        continue

                    '''Step 8: Everything else is annotated as PERFORMANCE.'''
                    aspects_hat.append("Performance")
                    step_nos.append("Step 8")
                    print("Step 8 applied.")

        return events_hat, aspects_hat, step_nos

    def event_nominal_rule(self, events_hat, aspects_hat, step_nos, vn_nominals) :
        print("vn_nominals: ", vn_nominals)
        for nom in vn_nominals :
            for span, sense in nom.items():
                print(f"span: {span}, sense: {sense}")
                events_hat.append((span, sense))
                aspects_hat.append("Process")
                step_nos.append("Step 1")
        return events_hat, aspects_hat, step_nos

    def extract_event_nominals(self, filepath, sent) :
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

    def get_sentences(self, filepath) : #for one individual file
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

    def get_sent_from_idx(self, idx, semparse_path, file_sents) :
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
        event_nominals = self.extract_event_nominals(sent_path, file_sents[idx-1]) #append to master nominals list for that file
        events_hat, aspects_hat, step_nos = self.event_nominal_rule([],[],[],event_nominals)
        #print(f"events_hat: {events_hat}, aspects_hat: {aspects_hat}, step_nos: {step_nos}")
        return events_hat, aspects_hat, step_nos

    def get_event_nominals_from_file(self, path_name) :
        events = []; aspects = []; steps = []
        for path in Path("gold_files").rglob("*.csv") : #glob needs to be generated each time
            path_short = path.name[:-4]
            #Find yo file.
            print("path_short: ", path_short)
            print("path_name: ", path_name)
            if path_short == path_name:
                file_sents = self.get_sentences(path)
                semparse_path = "LORELEI_semparse_json_cleaned/" + path_short
                print("semparse_path: ", semparse_path)
                #Iterate through each sentence in the file.
                print("Length of file_sents: ", len(file_sents))
                for idx in range(len(file_sents) + 1) :
                    idx = idx + 1
                    if idx > len(file_sents) :
                        break
                    events_hat, aspects_hat, step_nos = self.get_sent_from_idx(idx, semparse_path, file_sents)
                    events.append(events_hat)
                    aspects.append(aspects_hat)
                    steps.append(step_nos)

        print("EVENTS: ", events)
        print("ASPECTS: ", aspects)
        print("STEPS: ", steps)
        print("\n")
        return (events, aspects, steps) #tuple
        
    def apply_rules(self, sent, sent_idx, events, aspects, vn_senses, sent_vn_nominals_tuple, filename) :
        #events and aspects are the gold data. I'm creating events_hat and aspects_hat
        assert (len(events) == len(aspects)), "Unequal number of events and aspects!"
        print("sent_idx: ", sent_idx)
        print("length of event nominals: ", len(sent_vn_nominals_tuple[0]))
        events_hat = []
        aspects_hat = []
        step_nos = []

        events_hat, aspects_hat, step_nos = self.verb_loop(sent, vn_senses, filename)
        (event_nominals_hat, aspect_nominals_hat, step_nos_nominals) = sent_vn_nominals_tuple

        #Python 3.5> List Concatenation: https://stackoverflow.com/questions/1720421/how-do-i-concatenate-two-lists-in-python
        events_hat = [*events_hat, *event_nominals_hat[sent_idx]]
        aspects_hat = [*aspects_hat, *aspect_nominals_hat[sent_idx]]
        step_nos = [*step_nos, *step_nos_nominals[sent_idx]]
        print("events_hat: ", events_hat)
        print("aspects_hat: ", aspects_hat)

        return {'Sentence':sent, 'Gold Events':events, 'Gold Aspects':aspects, 'Events':events_hat, 'Auto Aspect':aspects_hat, 'Step #': step_nos}

    def prep_search_6(self, doc):
        '''
        Returns the preposition "in" or "for", if they are part of 
        a container or  durative adverbial clause, respectively.

        Otherwise, returns None.
        Source: https://stackoverflow.com/questions/49292321/how-can-i-get-children-of-an-ancestor-using-spacy-dependency-tree-in-python
        '''
        #deplacy.render(doc)

        for token in doc:
            if token.dep_ == "prep": 
                for a in token.ancestors:
                    print("a: ", a.text)
                    print("a.dep: ", a.dep_)
                    if a.dep_ == "ROOT" :
                        return token.text.lower()
        return None

    def prep_search_7(self, doc):
        '''
        Returns prepositions that occur immediately after their verb (i.e. there is no result path).
        '''
        #deplacy.render(doc)

        prev_verb = None
        tokens_in_btwn = 0
        for token in doc:
            tokens_in_btwn += 1
            if token.pos_ == "VERB" :
                prev_verb = token.text
                tokens_in_btwn = 0
            if token.dep_ == "prep": 
                print("tokens_in_btwn: ", tokens_in_btwn)
                if prev_verb != None and tokens_in_btwn == 1: #must be the immediate next token
                    return token.text.lower()
        return None

    def get_vf(self, tag) :
        #Extract appropriate tense from Penn Treebank Tag
        vf = ""
        if tag == "VB" :
            vf = "base"
        elif tag == "VBD" :
            vf = "simple_past"
        elif tag == "VBG" or tag == "VBN" :
            vf = "ppl"
        elif tag == "VBP" :
            vf = "12_sing_pres"
        elif tag == "VBZ" :
            vf = "3_sing_pres" #SIMPLE PRESENT

        return vf
    
    def read_semparse_files(self, filename) :
        vn_semparse = []
        for file in Path(self.semparse_path).rglob("*.txt"):
            print("filename: ", filename)
            print("file.name[:-9]: ", file.name[:-13])
            print(filename == file.name[:-13])
            if file.name[:-13] == filename :
                print(f'Processing {file.name}...')
                with open(file) as semparse_file :
                    text = semparse_file.read()
                    sents = text.split("------------------------------------------------------")
                    sents = sents[:-2] #ignore "END_FILE" sentence
                    for s in sents :
                        sent = re.findall("(?<=SENTENCE: )(.*)(?=\n{\n    \"tokens\":)", s)[0]
                        print("Analyzing sentence: ", sent)
                        doc = nlp(sent)
                        vn_senses = re.findall("(?<=\"sense\": \")(.*)(?=\",)", s)
                        vn_semparse.append(vn_senses)
                break
        return vn_semparse
    
    def extract_tac(self, filepath) :
        '''
        outputs a dictionary
        '''
        tac_dict = {}
        with open(filepath) as tac_file :
            lines = tac_file.readlines()
            filename = ""
            file_values = []
            for line in lines :
                if line[:7] == "LORELEI" :
                    line = re.sub("NW_PRI_ENG_", "", line)
                    filename = re.sub(".tsv", "_Gold_3-13-21", line)
                    filename = re.sub("\n", "", filename)
                else :
                    if re.search("---", line) != None :
                        tac_dict[filename] = file_values
                        filename = ""
                        file_values = []
                    else:
                        temp = line.split()
                        tac_tuple = (temp[0], temp[1])
                        file_values += tac_tuple
        return tac_dict

    def run_auto_aspect(self) :
        for file in self.gold_files:

            print(f'Processing {file.name}...')
            gold = pd.read_csv(file)
            col_list = ['Sentence', 'Gold Events', 'Gold Aspects', 'Events', 'Auto Aspect', "Step #"]
            col_dict = {key: None for key in col_list}
            rows_list = []

            #Get columns as arrays.
            sents_col = gold["Sentence"]
            events_col = gold["Event"]
            aspect_col = gold["Aspect"]
            assert(len(sents_col) == len(events_col)), "Unequal column lengths"
            assert(len(events_col) == len(aspect_col)), "Unequal column lengths"

            filename = file.name[:-4]
            vn_semparse = self.read_semparse_files(filename)
            #vn_nominals = self.read_semparse_jsons(filename)
            vn_nominals = self.get_event_nominals_from_file(filename)
            print("vn_nominals: ", vn_nominals)

            theSent = ""
            i = 0
            vn_idx = 0
            sent_idx = -1
            while i < len(sents_col) :
                print("Current index: ", i)
                sent = sents_col[i]
        
                #BREAK WHILE LOOP
                if sent == "END_FILE" :
                    break
        
                if type(sent) == str :
                    print("theSent: ",sent)
                    theSent = sent
                    i += 1
                    sent_idx += 1
                    sent = sents_col[i]

                events = []
                aspects = []
        
                #All Event and Aspect information is stored while (new) sent == NaN
                while type(sent) != str:
                    events.append(events_col[i])
                    aspects.append(aspect_col[i])
                    i += 1
                    sent = sents_col[i]

                print("events: ", events)
                print("aspects:", aspects)

                #MAIN CODE (running tests)
                vn_senses = vn_semparse[vn_idx]
                vn_idx += 1
                sent_dict = self.apply_rules(theSent, sent_idx, events, aspects, vn_senses, vn_nominals, filename)
                print(sent_dict)
                rows_list.append(sent_dict)
                print("--------------------------------------------------------------------")
            output_df = pd.DataFrame(rows_list)
            output_df = output_df.reindex(columns=col_list)
            output_df.to_excel(file.name[:-4] + ".xlsx")