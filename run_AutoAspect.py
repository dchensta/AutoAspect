from AutoAspect import AutoAspect

if __name__ == "__main__" :
    gold_path = "gold_files"
    semparse_path = "LORELEI_semparse"
    semparse_json_path = "LORELEI_semparse_json_cleaned"
    tac_path = "ta_labels.txt"
    parser = "spacy"
    model = AutoAspect(gold_path, semparse_path, semparse_json_path, tac_path, parser)
    model.run_auto_aspect()