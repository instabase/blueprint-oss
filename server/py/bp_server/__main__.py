#!/usr/bin/env python3

import json
import os
import subprocess
import tempfile
import traceback

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore

from bp.config import Config
from bp.document import (
  dump_to_json as dump_doc_to_json,
  load_doc_from_json,
)
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


def make_error_response(e: Exception) -> Tuple[str, int]:
  error = str(e)
  _traceback = traceback.format_exception(None, e, e.__traceback__)
  return jsonify({
    'error': error,
    'traceback': _traceback,
  }), 500


@app.errorhandler(500)
def handle_bad_request(e: Exception) -> Tuple[str, int]:
  return jsonify({'error': str(e)}), 500


@app.route('/gen_bp_doc', methods=['POST'])
def gen_bp_doc() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True)
    google_ocr_json = payload['google_ocr']
    doc = generate_doc_from_google_ocr_json(
            google_ocr_json, 'random_document_name')
    return jsonify({'doc': asdict(doc)})

    """
    with tempfile.TemporaryDirectory() as tempdir:

      print(f'running gen_bp_doc, with tempdir={tempdir}')

      google_ocr_path = f'{tempdir}/google_ocr.json'
      output_doc_path = f'{tempdir}/doc.json'

      with Path(google_ocr_path).open('w') as f:
        f.write(json.dumps(google_ocr_json))

      subprocess.call(
        f'python3 -m bp gen_bp_doc '
        f'-g {google_ocr_path} -o {output_doc_path}',
        shell=True, env={'PYTHONPATH': PYTHONPATH})

      return jsonify({
        'payload': {
          'results': json.load(Path(f'{output_doc_path}').open())
        }
      })
    """

  except Exception as e:
    return make_error_response(e)


@app.route('/run_bp_model', methods=['POST'])
def run_bp_model() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True)
    doc = load_doc_from_json(payload['doc'])
    model = load_model_from_json(payload['model'])
    # FIXME: Make timeout configurable in UI.
    TIMEOUT = 45
    NUM_SAMPLES = 20
    config = Config(NUM_SAMPLES, TIMEOUT)
    results = run_model(doc, model, config)
    return jsonify({'doc': asdict(results)})

    """
    payload: Dict[str, Any] = request.get_json(force=True)

    doc = payload['doc']
    model_json = payload['model']

    with tempfile.TemporaryDirectory() as tempdir:

      fake_doc_name = 'doc.json'

      doc_path = f'{tempdir}/{fake_doc_name}'
      model_path = f'{tempdir}/model.json'
      output_dir = f'{tempdir}/output'

      # Pretty janky.json.json
      output_file = f'{output_dir}/{fake_doc_name}.json'

      with Path(doc_path).open('w') as f:
        f.write(json.dumps(doc))
      with Path(model_path).open('w') as f:
        f.write(json.dumps(model_json))

      subprocess.call(
        f'python3 {BP_PATH}/bp/cli/cli_main.py run_model '
        f'-m {model_path} -o {output_dir} -d {doc_path} -t {TIMEOUT} '
        f'-n {NUM_SAMPLES}',
        shell=True, env={'PYTHONPATH': PYTHONPATH})

      return jsonify({
        'payload': {
          'results': json.load(Path(f'{output_file}').open())
        }
      })
    """

  except Exception as e:
    return make_error_response(e)


@app.route('/synthesis', methods=['POST'])
def synthesis() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True)
    doc = load_doc_from_json(payload['doc'])
    target_extraction = load_extraction_from_json(payload['target_extraction'])
    schema = load_schema_from_json(payload['schema'])
    node = synthesize_pattern_node(target_extraction, schema, doc)
    return jsonify({'node': asdict(node)})

    """
    payload: Dict[str, Any] = request.get_json(force=True)

    doc = payload['doc']
    target_extraction = payload['target_extraction']
    schema = payload['schema']

    with tempfile.TemporaryDirectory() as tempdir:

      target_extraction_path = f'{tempdir}/target_extraction.json'
      schema_path = f'{tempdir}/schema.json'
      doc_path = f'{tempdir}/doc.json'
      output_path = f'{tempdir}/out.json'

      with Path(target_extraction_path).open('w') as f:
        f.write(json.dumps(target_extraction))
      with Path(schema_path).open('w') as f:
        f.write(json.dumps(schema))
      with Path(doc_path).open('w') as f:
        f.write(json.dumps(doc))

      subprocess.call(
        f'python3 {BP_PATH}/bp/cli/cli_main.py synthesis '
        f'-e {target_extraction_path} -o {output_path} -d {doc_path} '
        f'-s {schema_path}',
        shell=True, env={'PYTHONPATH': PYTHONPATH})
      results = json.load(Path(output_path).open())

      return jsonify({
        'payload': {
          'node': json.load(Path(f'{output_path}').open())
        }
      })
    """

  except Exception as e:
    return make_error_response(e)


@app.route('/wiif', methods=['POST'])
def wiif() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True)
    doc = load_doc_from_json(payload['doc'])
    node = load_model_from_json(payload['node'])
    target_extraction = load_extraction_from_json(payload['target_extraction'])
    wiif_node = why_is_it_failing(target_extraction, node, doc)
    return jsonify({'wiif_node': asdict(wiif_node)})

    """
    payload: Dict[str, Any] = request.get_json(force=True)

    doc = payload['doc']
    node = payload['node']
    target_extraction = payload['target_extraction']

    with tempfile.TemporaryDirectory() as tempdir:

      doc_path = f'{tempdir}/doc.json'
      target_extraction_path = f'{tempdir}/target_extraction.json'
      node_path = f'{tempdir}/node.json'
      output_path = f'{tempdir}/out.json'

      with Path(doc_path).open('w') as f:
        f.write(json.dumps(doc))
      with Path(target_extraction_path).open('w') as f:
        f.write(json.dumps(target_extraction))
      with Path(node_path).open('w') as f:
        f.write(json.dumps(node))

      subprocess.call(
        f'python3 {BP_PATH}/bp/cli/cli_main.py wiif '
        f'-n {node_path} -o {output_path} -d {doc_path} '
        f'-e {target_extraction_path} ',
        shell=True, env={'PYTHONPATH': PYTHONPATH})

      return jsonify({
        'payload': {
          'wiif_node': json.load(Path(f'{output_path}').open())
        }
      })
    """

  except Exception as e:
    return make_error_response(e)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
