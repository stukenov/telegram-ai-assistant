import logging
import sys
import os
from flask import Flask, request, jsonify
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from IPython.display import Markdown, display, JSON

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

app = Flask(__name__)

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
Settings.llm = Ollama(model="newink/suzume", request_timeout=360.0)

# check if storage already exists
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    logger.debug("Storage directory does not exist. Creating new index.")
    # load the documents and create the index
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    logger.debug("Index created and persisted.")
else:
    logger.debug("Storage directory exists. Loading existing index.")
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
    logger.debug("Index loaded from storage.")

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    query = data.get('query')
    if not query:
        logger.error("Query parameter is missing")
        return jsonify({"error": "Query parameter is missing"}), 400

    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    logger.debug(f"Query received: {query}")
    # Convert to text response.response
    text = response.response
    return jsonify({"response": text}), 200

if __name__ == '__main__':
    logger.debug("Starting Flask app.")
    app.run(host='127.0.0.1', port=8181)
    logger.debug("Flask app running.")
