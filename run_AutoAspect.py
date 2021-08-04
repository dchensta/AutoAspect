from AutoAspect import AutoAspect

if __name__ == "__main__" :
    gold_path = "gold_files"
    semparse_path = "LORELEI_semparse"
    semparse_json_path = "LORELEI_semparse_json_cleaned"
    parser = AutoAspect(gold_path, semparse_path, semparse_json_path)
    parser.run_auto_aspect()