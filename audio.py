from flask import Flask, request, jsonify
import logging
import sys
import os
from faster_whisper import WhisperModel

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

app = Flask(__name__)
model_size = "large-v3"

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
model = WhisperModel(model_size, device="cpu", compute_type="int8")

@app.route('/audio', methods=['POST'])
def audio():
    if 'file' not in request.files:
        logger.error("file parameter is missing")
        return jsonify({"error": "file parameter is missing"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join("audio", file.filename)
    file.save(file_path)

    segments, info = model.transcribe(file_path, beam_size=5)
    logger.info("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    all_segments = []
    for segment in segments:
        segment_text = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        all_segments.append(segment_text)

    return jsonify({"result": "\n".join(all_segments), "language": info.language}), 200

if __name__ == '__main__':
    logger.debug("Starting Flask app.")
    app.run(host='127.0.0.1', port=8183)
    logger.debug("Flask app running.")
