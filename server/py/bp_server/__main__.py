#!/usr/bin/env python3

import json
import os
import subprocess
import tempfile
import traceback

from pathlib import Path
from typing import Any, Callable, Dict, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore


app = Flask(__name__)
CORS(app)

STUDIO_PROJECTS_PATH: str = os.getenv('STUDIO_PROJECTS_PATH', 'UNDEFINED')
BP_PATH = f'{Path.cwd().absolute()}/../blueprint/py'
PYTHONPATH = f'{BP_PATH}'


def make_error_response(e: Exception) -> Tuple[str, int]:
  error = str(e)
  _traceback = traceback.format_exception(None, e, e.__traceback__)
  return jsonify({
    'error': error,
    'traceback': _traceback,
  }), 500


@app.route('/status')
def health_check() -> Tuple[str, int]:
  return jsonify({'status': 'alive'}), 200


@app.errorhandler(500)
def handle_bad_request(e: Exception) -> Tuple[str, int]:
  return jsonify({'error': str(e)}), 500


@app.route('/server_info')
def server_info() -> Any:
  return jsonify({
    'studioProjectsPath': STUDIO_PROJECTS_PATH,
  }), 200


@app.route('/run_bp_model', methods=['POST'])
def run_bp_model() -> Any:
  try:
    payload: Dict[str, Any] = request.get_json(force=True)

    doc = payload['doc']
    model_json = payload['model']

    # FIXME: Make timeout configurable in UI.
    TIMEOUT = 45
    NUM_SAMPLES = 20

    with tempfile.TemporaryDirectory() as tempdir:

      doc_path = f'{tempdir}/doc.json'
      model_path = f'{tempdir}/model.json'

      with Path(doc_path).open('w') as f:
        f.write(json.dumps(doc))
      with Path(model_path).open('w') as f:
        f.write(json.dumps(model_json))

      subprocess.call(
        f'python3 {BP_PATH}/bp/cli/cli_main.py run_model '
        f'-m {model_path} -o {tempdir} -d {doc_path} -t {TIMEOUT} '
        f'-n {NUM_SAMPLES}',
        shell=True, env={'PYTHONPATH': PYTHONPATH})

      return jsonify({
        'payload': {
          'results': json.load(Path(f'{doc_path}.json').open())
        }
      })

  except Exception as e:
    return make_error_response(e)


@app.route('/synthesis', methods=['POST'])
def synthesis() -> Any:
  try:
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

  except Exception as e:
    return make_error_response(e)


@app.route('/wiif', methods=['POST'])
def wiif() -> Any:
  try:
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

  except Exception as e:
    return make_error_response(e)


@app.route('/ls/<path:abs_path>')
def ls(abs_path: str) -> Any:
  try:
    return jsonify(os.listdir('/' + abs_path))
  except Exception as e:
    return make_error_response(e)


@app.route('/read_file/<path:abs_path>')
def read_file(abs_path: str) -> Any:
  try:
    with open('/' + abs_path) as f:
      return f.read()
  except Exception as e:
    return make_error_response(e)


@app.route('/write_file/<path:abs_path>', methods=['POST'])
def write_file(abs_path: str) -> Any:
  try:
    body = request.get_data()
    with open('/' + abs_path, 'wb') as f:
      f.write(body)
      return 'OK', 200
  except Exception as e:
    return make_error_response(e)


@app.route('/projects')
def projects() -> Any:
  try:
    return ls(STUDIO_PROJECTS_PATH)
  except Exception as e:
    return make_error_response(e)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
