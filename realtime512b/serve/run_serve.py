"""Main entry point for realtime512b serve command."""

import os
from flask import Flask
from flask_cors import CORS

from .api_handlers import (
    get_config_handler,
    get_epochs_handler,
    get_segments_handler,
    get_shift_coefficients_handler,
    get_binary_data_handler,
    get_high_activity_handler,
    get_stats_handler,
    get_preview_file_handler,
    get_epoch_detail_handler,
    get_epoch_preview_file_handler,
)


def run_serve(host="0.0.0.0", port=5000):
    """Main entry point for realtime512b serve."""
    # Check if we're in an experiment directory
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    if not os.path.exists(config_path):
        print("Error: No realtime512b.yaml configuration file found in current directory.")
        print("Please run this command from an experiment directory.")
        return
    
    raw_dir = os.path.join(os.getcwd(), "raw")
    if not os.path.exists(raw_dir):
        print("Error: No raw/ directory found in current directory.")
        print("Please run this command from an experiment directory.")
        return
    
    print(f"Starting realtime512b server...")
    print(f"Serving data from: {os.getcwd()}")
    print(f"Server will listen on http://{host}:{port}")
    print(f"CORS enabled for: http://localhost:5173")
    print("")
    print("API Endpoints:")
    print("  GET /api/config - Configuration")
    print("  GET /api/epochs - Available epochs")
    print("  GET /api/epochs/<epoch_id> - Epoch details and epoch sorting stats")
    print("  GET /api/epochs/<epoch_id>/segments - Segments in an epoch")
    print("  GET /api/shift_coefficients - Shift coefficients")
    print("  GET /api/raw/<epoch_id>/<filename>?start_sec=X&end_sec=Y - Raw data")
    print("  GET /api/filt/<epoch_id>/<filename>?start_sec=X&end_sec=Y - Filtered data")
    print("  GET /api/shifted/<epoch_id>/<filename>?start_sec=X&end_sec=Y - Shifted data")
    print("  GET /api/high_activity/<epoch_id>/<filename> - High activity intervals")
    print("  GET /api/stats/<epoch_id>/<filename> - Spike statistics")
    print("  GET /api/preview/<epoch_id>/<filename>/<filepath> - Preview files (with range support)")
    print("  GET /api/epoch_preview/<epoch_id>/<filepath> - Epoch preview files (with range support)")
    print("")
    
    # Create Flask app
    app = Flask(__name__)

    # Enable CORS for localhost:5173 and expose custom headers
    CORS(app, origins=["http://localhost:5173"], expose_headers=[
        "X-Start-Sec",
        "X-End-Sec", 
        "X-Num-Frames",
        "X-Num-Channels",
        "X-Sampling-Frequency"
    ])
    
    # Register routes
    @app.route("/api/config", methods=["GET"])
    def get_config():
        return get_config_handler()
    
    @app.route("/api/epochs", methods=["GET"])
    def get_epochs():
        return get_epochs_handler()
    
    @app.route("/api/epochs/<epoch_id>", methods=["GET"])
    def get_epoch_detail(epoch_id):
        return get_epoch_detail_handler(epoch_id)
    
    @app.route("/api/epochs/<epoch_id>/segments", methods=["GET"])
    def get_segments(epoch_id):
        return get_segments_handler(epoch_id)
    
    @app.route("/api/shift_coefficients", methods=["GET"])
    def get_shift_coefficients():
        return get_shift_coefficients_handler()
    
    @app.route("/api/raw/<epoch_id>/<filename>", methods=["GET"])
    def get_raw(epoch_id, filename):
        return get_binary_data_handler("raw", epoch_id, filename)
    
    @app.route("/api/filt/<epoch_id>/<filename>", methods=["GET"])
    def get_filt(epoch_id, filename):
        return get_binary_data_handler("filt", epoch_id, filename)
    
    @app.route("/api/shifted/<epoch_id>/<filename>", methods=["GET"])
    def get_shifted(epoch_id, filename):
        return get_binary_data_handler("shifted", epoch_id, filename)
    
    @app.route("/api/high_activity/<epoch_id>/<filename>", methods=["GET"])
    def get_high_activity(epoch_id, filename):
        return get_high_activity_handler(epoch_id, filename)
    
    @app.route("/api/stats/<epoch_id>/<filename>", methods=["GET"])
    def get_stats(epoch_id, filename):
        return get_stats_handler(epoch_id, filename)
    
    @app.route("/api/preview/<epoch_id>/<filename>/<path:filepath>", methods=["GET"])
    def get_preview_file(epoch_id, filename, filepath):
        return get_preview_file_handler(epoch_id, filename, filepath)
    
    @app.route("/api/epoch_preview/<epoch_id>/<path:filepath>", methods=["GET"])
    def get_epoch_preview_file(epoch_id, filepath):
        return get_epoch_preview_file_handler(epoch_id, filepath)
    
    # Run the server
    app.run(host=host, port=port, debug=False)
