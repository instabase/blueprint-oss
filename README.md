# Blueprint

Blueprint is a declarative extraction language for semi-structured documents.

# Setup

Start by cloning this repo to your machine.

## CLI

To run on a sample paystub:

- Add `path/to/blueprint-oss/blueprint/py` to your `PYTHONPATH`
- Run `pip3 install -r path/to/blueprint-oss/blueprint/requirements.txt`
- From the `blueprint/reference_extractions/paystubs` folder, run
`python3 paystubs.py run_model -v -g ocr/sample_paystub.jpg.json`

To generate your own OCR documents:
- Upload image here: https://cloud.google.com/vision/docs/drag-and-drop
- Navigate to the Text tab and click "Show JSON"
- Save a JSON file with the entire Response

## Server

TODO

## Studio

TODO
