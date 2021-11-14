#!/usr/bin/env python3

import traceback

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Tuple

from flask import Flask, Response, jsonify, request
from flask_cors import CORS # type: ignore

from bp.config import Config
from bp.document import load_doc_from_json
from bp.extraction import load_extraction_from_json
from bp.google_ocr_file import generate_doc_from_google_ocr_json
from bp.model import load_model_from_json
from bp.run import run_model
from bp.synthesis.synthesize import synthesize_pattern_node
from bp.synthesis.wiif import why_is_it_failing
from bp.targets import load_schema_from_json, load_targets_from_json


app = Flask(__name__)
CORS(app)

BP_PATH = f'{Path.cwd().absolute()}/../blueprint/py'
PYTHONPATH = f'{BP_PATH}'


def make_error_response(e: Exception) -> Tuple[Response, int]:
  error = str(e)
  _traceback = traceback.format_exception(None, e, e.__traceback__)
  return jsonify({
    'error': error,
    'traceback': _traceback,
  }), 500


@app.errorhandler(500) # type: ignore
def handle_bad_request(e: Exception) -> Tuple[Response, int]:
  return jsonify({'error': str(e)}), 500


@app.route('/gen_bp_doc', methods=['POST'])
def gen_bp_doc() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True) # type: ignore
    google_ocr_json = payload['google_ocr']
    doc = generate_doc_from_google_ocr_json(
            google_ocr_json, 'random_document_name')
    return jsonify({'doc': asdict(doc)})

  except Exception as e:
    return make_error_response(e)


@app.route('/run_bp_model', methods=['POST'])
def run_bp_model() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True) # type: ignore
    doc = load_doc_from_json(payload['doc'])
    model = load_model_from_json(payload['model'])
    # FIXME: Make these configurable from the GUI.
    TIMEOUT = -1 # signal (used for timeouts) only work from the main thread
    NUM_SAMPLES = 20
    config = Config(NUM_SAMPLES, TIMEOUT)
    results = run_model(doc, model, config)
    return jsonify({'results': asdict(results)})

  except Exception as e:
    return make_error_response(e)


@app.route('/synthesis', methods=['POST'])
def synthesis() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True) # type: ignore
    doc = load_doc_from_json(payload['doc'])
    target_extraction = load_extraction_from_json(payload['target_extraction'])
    schema = load_schema_from_json(payload['schema'])
    node = synthesize_pattern_node(target_extraction, schema, doc)
    return jsonify({'node': asdict(node)})

  except Exception as e:
    return make_error_response(e)


@app.route('/wiif', methods=['POST'])
def wiif() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True) # type: ignore
    doc = load_doc_from_json(payload['doc'])
    node = load_model_from_json(payload['node'])
    target_extraction = load_extraction_from_json(payload['target_extraction'])
    wiif_node = why_is_it_failing(target_extraction, node, doc)
    return jsonify({'wiif_node': asdict(wiif_node)})

  except Exception as e:
    return make_error_response(e)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
