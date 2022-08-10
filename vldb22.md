---
title: Reproducibility instructions for Blueprint experiments in VLDB'22. 
author: jindal
layout: page
toc: true
---

# Setup
[See video here](https://www.loom.com/share/7150fb0e01ed4d25b98bda0daa693e43)

* Download and extract [all the scripts](https://drive.google.com/file/d/1XYru889eHSz9wOrNV5ScdlUGaLFSegPp/view?usp=sharing).
* Download [MIDV-2020 dataset](https://arxiv.org/abs/2107.00396) `templates.tar` in the `datasets/midv2020` folder 
* Rename all files in `datasets/midv2020/templates/images/` in following format
  * `images/alb_id/00.jpg` -> `images/alb_id_00.jpg`
* Create `datasets/midv2020/templates/hocr/` folder
* Run `ocrall.py` for one config glob at a time
  * This picks the appropriate Tesseract language settings and image channels to get the OCR output.

# Comparing hand-written program with synthesized program

### Performance, number of constraints
[See video here](https://www.loom.com/share/051e40caff884a0b95385144e9e751bd)

* Download [Blueprint](https://github.com/instabase/blueprint-oss/)
* Make sure that PYTHONPATH is set and requirements are installed
* Next, hand-written blueprint program `aze_passports.py` can be run using `runall.sh Section 1`.
	* Number of rules: `18`
* Similarly, synthesized blueprint program `aze_passport_model.json` can be run using `runall.sh Section 2`.
	* Number of rules: 
	  ```
jq 'recurse(.children[]) | .rules[].predicate' aze_passport_model.json | jq -s '. | length'
		```

### Accuracy calculations
[See video here](https://www.loom.com/share/8be3739b87054c29ba4be24b6e214a71)
* Add annotations in `annotations/` in `datasets/midv2020/templates/annotations/`
* Run `aze_analysis/preprocess.py`.  This will dump
  * ground.csv: Ground truth. Read from annotations provided in MIDV dataset.
  * hbp.csv. Handwritten blueprint program results
  * sbp.csv. Synthesized blueprint program results

* Run `aze_analysis/accuracy.py`. This will compare csv files such as hbp.csv
	with ground.csv and dump how many times out of 100, did each field match. It
	will also dump when the field(s) did not match. Non-match cases are
	considered as matching if they are basically OCR errors.

	This has to be run once with hbp.csv and once with sbp.csv.

# Comparing SBP with LayoutLM

### Running synthesized Blueprint program
[See video here](https://www.loom.com/share/1cd52910f90b4cf6bc124c39490d95ff)
* Synthesized blueprint program `all_model.json` can be run using `runall.sh Section 3`.
* Number of rules: 
	 ```
vimdiff <(jq '.' all_model.json) all_model_with_children.json
jq 'recurse(.children[]) | .rules[].predicate' all_model_with_children.json | jq -s '. | length'
	 ```

For accuracy calculation:
* Run `all_analysis/preprocess.py`. This will dump ground.csv and sbp.csv
* Run `all_analysis/accuracy.py`. This will compare the csv files to dump a report.
* Report is manually marked in `manual_report.txt`.
* Counts are generated using `gen_table.sh`

### Running LayoutLM model
[See video here](https://www.loom.com/share/dea468a7c0f84d179b8a9fe157eac9f4)
* LayoutLM model that was trained by us (`model.pth`) is provided.
* You can retrain the model using `training.py`, `evaluation.py`. See `layoutlm.md`
for details.
* Run `runall.sh Section 4` to run `model.pth` on all files.

For accuracy calculation:
* Run `lm_analysis/preprocess.py`. This will dump ground.csv and lm.csv
* Run `lm_analysis/accuracy.py`. This will compare the csv files to dump a report.
* Report is manually marked in `manual_report.txt`.
* Counts are generated using `gen_table.sh`
