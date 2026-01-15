"""API handlers for the realtime512b serve command."""

import os
import json
import yaml
from flask import jsonify, request, Response, send_from_directory


def get_config_handler():
    """Returns the experiment configuration."""
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    if not os.path.exists(config_path):
        return jsonify({"error": "Configuration file not found"}), 404
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    return jsonify(config)


def get_epochs_handler():
    """Returns list of available epochs."""
    raw_dir = os.path.join(os.getcwd(), "raw")
    computed_dir = os.path.join(os.getcwd(), "computed")
    
    if not os.path.exists(raw_dir):
        return jsonify({"error": "raw/ directory not found"}), 404
    
    epochs_info = []
    for item in sorted(os.listdir(raw_dir)):
        item_path = os.path.join(raw_dir, item)
        if os.path.isdir(item_path):
            # Get number of segments in this epoch
            segment_files = [f for f in os.listdir(item_path) if f.endswith(".bin")]
            num_segments = len(segment_files)
            
            # Check for epoch spike sorting
            epoch_sorting_dir = os.path.join(computed_dir, "epoch_spike_sorting", item)
            has_epoch_sorting = (
                os.path.exists(os.path.join(epoch_sorting_dir, "templates.npy")) and
                os.path.exists(os.path.join(epoch_sorting_dir, "spike_times.npy")) and
                os.path.exists(os.path.join(epoch_sorting_dir, "spike_labels.npy")) and
                os.path.exists(os.path.join(epoch_sorting_dir, "spike_amplitudes.npy"))
            )
            
            # Check for epoch preview
            epoch_preview_dir = os.path.join(computed_dir, "epoch_preview", item, "epoch.figpack")
            has_epoch_preview = os.path.exists(epoch_preview_dir) and os.path.isdir(epoch_preview_dir)
            
            # Count how many segments have spike sorting completed
            spike_sorting_dir = os.path.join(computed_dir, "spike_sorting", item)
            num_segments_sorted = 0
            if os.path.exists(spike_sorting_dir):
                for segment_file in segment_files:
                    segment_sorting_path = os.path.join(spike_sorting_dir, segment_file)
                    if (os.path.exists(os.path.join(segment_sorting_path, "templates.npy")) and
                        os.path.exists(os.path.join(segment_sorting_path, "spike_times.npy")) and
                        os.path.exists(os.path.join(segment_sorting_path, "spike_labels.npy")) and
                        os.path.exists(os.path.join(segment_sorting_path, "spike_amplitudes.npy"))):
                        num_segments_sorted += 1
            
            epochs_info.append({
                "name": item,
                "num_segments": num_segments,
                "num_segments_sorted": num_segments_sorted,
                "has_epoch_sorting": has_epoch_sorting,
                "has_epoch_preview": has_epoch_preview
            })
    
    return jsonify({"epochs": sorted(epochs_info, key=lambda x: x["name"])})


def get_segments_handler(epoch_id):
    """Returns list of available segments for an epoch."""
    raw_dir = os.path.join(os.getcwd(), "raw", epoch_id)
    computed_dir = os.path.join(os.getcwd(), "computed")
    
    if not os.path.exists(raw_dir):
        return jsonify({"error": f"Epoch {epoch_id} not found"}), 404
    
    bin_files = [fname for fname in os.listdir(raw_dir) if fname.endswith(".bin")]
    
    segments_info = []
    for fname in sorted(bin_files):
        segment_info = {
            "filename": fname,
            "has_filt": os.path.exists(os.path.join(computed_dir, "filt", epoch_id, fname + ".filt")),
            "has_shifted": os.path.exists(os.path.join(computed_dir, "shifted", epoch_id, fname + ".filt.shifted")),
            "has_high_activity": os.path.exists(os.path.join(computed_dir, "high_activity", epoch_id, fname + ".high_activity.json")),
            "has_stats": os.path.exists(os.path.join(computed_dir, "stats", epoch_id, fname + ".stats.json")),
            "has_preview": os.path.exists(os.path.join(computed_dir, "preview", epoch_id, fname + ".figpack")),
        }
        
        # Check for reference sorting
        reference_sorting_dir = os.path.join(computed_dir, "reference_sorting", epoch_id, fname)
        has_reference_sorting = (
            os.path.exists(os.path.join(reference_sorting_dir, "templates.npy")) and
            os.path.exists(os.path.join(reference_sorting_dir, "spike_times.npy")) and
            os.path.exists(os.path.join(reference_sorting_dir, "spike_labels.npy")) and
            os.path.exists(os.path.join(reference_sorting_dir, "spike_amplitudes.npy"))
        )
        segment_info["has_reference_sorting"] = has_reference_sorting
        
        # Check for spike sorting
        spike_sorting_dir = os.path.join(computed_dir, "spike_sorting", epoch_id, fname)
        has_spike_sorting = (
            os.path.exists(os.path.join(spike_sorting_dir, "templates.npy")) and
            os.path.exists(os.path.join(spike_sorting_dir, "spike_times.npy")) and
            os.path.exists(os.path.join(spike_sorting_dir, "spike_labels.npy")) and
            os.path.exists(os.path.join(spike_sorting_dir, "spike_amplitudes.npy"))
        )
        segment_info["has_spike_sorting"] = has_spike_sorting
        
        # Get file size and duration
        raw_path = os.path.join(raw_dir, fname)
        if os.path.exists(raw_path):
            file_size = os.path.getsize(raw_path)
            segment_info["size_bytes"] = file_size
            
            # Load config to get n_channels and sampling_frequency
            config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                n_channels = config.get("n_channels", 512)
                sampling_frequency = config.get("sampling_frequency", 20000)
                
                num_frames = file_size // (2 * n_channels)
                duration_sec = num_frames / sampling_frequency
                segment_info["num_frames"] = num_frames
                segment_info["duration_sec"] = duration_sec
        
        segments_info.append(segment_info)
    
    return jsonify({"epoch": epoch_id, "segments": segments_info})


def get_shift_coefficients_handler():
    """Returns shift coefficients."""
    computed_dir = os.path.join(os.getcwd(), "computed")
    shift_coeffs_path = os.path.join(computed_dir, "shift_coeffs.yaml")
    
    if not os.path.exists(shift_coeffs_path):
        return jsonify({"error": "Shift coefficients not found"}), 404
    
    with open(shift_coeffs_path, "r") as f:
        shift_coeffs = yaml.safe_load(f)
    
    return jsonify(shift_coeffs)


def get_binary_data_handler(data_type, epoch_id, filename):
    """Returns binary data (raw, filt, or shifted) for a time range."""
    # Load configuration
    config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
    if not os.path.exists(config_path):
        return jsonify({"error": "Configuration file not found"}), 404
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    n_channels = config.get("n_channels", 512)
    sampling_frequency = config.get("sampling_frequency", 20000)
    
    # Determine file path based on data type
    if data_type == "raw":
        data_path = os.path.join(os.getcwd(), "raw", epoch_id, filename)
    elif data_type == "filt":
        data_path = os.path.join(os.getcwd(), "computed", "filt", epoch_id, filename + ".filt")
    elif data_type == "shifted":
        data_path = os.path.join(os.getcwd(), "computed", "shifted", epoch_id, filename + ".filt.shifted")
    else:
        return jsonify({"error": "Invalid data type"}), 400
    
    if not os.path.exists(data_path):
        return jsonify({"error": f"{data_type} file not found"}), 404
    
    # Get file size and calculate total duration
    file_size = os.path.getsize(data_path)
    total_frames = file_size // (2 * n_channels)
    total_duration_sec = total_frames / sampling_frequency
    
    # Get time range parameters
    start_sec = request.args.get("start_sec", type=float)
    end_sec = request.args.get("end_sec", type=float)
    
    # If no time range specified, return entire file
    if start_sec is None and end_sec is None:
        with open(data_path, "rb") as f:
            data_bytes = f.read()
        return Response(
            data_bytes,
            mimetype="application/octet-stream",
            headers={
                "X-Num-Frames": str(total_frames),
                "X-Num-Channels": str(n_channels),
                "X-Sampling-Frequency": str(sampling_frequency)
            }
        )
    
    # Validate time range
    if start_sec is None:
        start_sec = 0.0
    if end_sec is None:
        end_sec = total_duration_sec
    
    if start_sec < 0 or end_sec > total_duration_sec or start_sec >= end_sec:
        return jsonify({
            "error": "Invalid time range",
            "start_sec": start_sec,
            "end_sec": end_sec,
            "total_duration_sec": total_duration_sec
        }), 400
    
    # Calculate frame range
    start_frame = int(start_sec * sampling_frequency)
    end_frame = int(end_sec * sampling_frequency)
    num_frames = end_frame - start_frame
    
    # Calculate byte offset and size
    bytes_per_frame = 2 * n_channels
    byte_offset = start_frame * bytes_per_frame
    num_bytes = num_frames * bytes_per_frame
    
    # Read the data segment
    with open(data_path, "rb") as f:
        f.seek(byte_offset)
        data_bytes = f.read(num_bytes)
    
    # Return as binary response
    return Response(
        data_bytes,
        mimetype="application/octet-stream",
        headers={
            "X-Start-Sec": str(start_sec),
            "X-End-Sec": str(end_sec),
            "X-Num-Frames": str(num_frames),
            "X-Num-Channels": str(n_channels),
            "X-Sampling-Frequency": str(sampling_frequency)
        }
    )


def get_high_activity_handler(epoch_id, filename):
    """Returns high activity intervals JSON."""
    computed_dir = os.path.join(os.getcwd(), "computed")
    high_activity_path = os.path.join(computed_dir, "high_activity", epoch_id, filename + ".high_activity.json")
    
    if not os.path.exists(high_activity_path):
        return jsonify({"error": "High activity file not found"}), 404
    
    with open(high_activity_path, "r") as f:
        data = json.load(f)
    
    return jsonify(data)


def get_stats_handler(epoch_id, filename):
    """Returns spike statistics JSON."""
    computed_dir = os.path.join(os.getcwd(), "computed")
    stats_path = os.path.join(computed_dir, "stats", epoch_id, filename + ".stats.json")
    
    if not os.path.exists(stats_path):
        return jsonify({"error": "Stats file not found"}), 404
    
    with open(stats_path, "r") as f:
        data = json.load(f)
    
    return jsonify(data)


def get_preview_file_handler(epoch_id, filename, filepath):
    """Serves static files from preview directories with range request support."""
    computed_dir = os.path.join(os.getcwd(), "computed")
    preview_dir = os.path.join(computed_dir, "preview", epoch_id, filename + ".figpack")
    
    if not os.path.exists(preview_dir):
        return jsonify({"error": "Preview directory not found"}), 404
    
    # Serve the file with range request support
    return send_from_directory(
        preview_dir,
        filepath,
        conditional=True  # Enables range request support
    )


def get_epoch_detail_handler(epoch_id):
    """Returns detailed information about an epoch including epoch sorting data."""
    raw_dir = os.path.join(os.getcwd(), "raw", epoch_id)
    computed_dir = os.path.join(os.getcwd(), "computed")
    
    if not os.path.exists(raw_dir):
        return jsonify({"error": f"Epoch {epoch_id} not found"}), 404
    
    # Get segment list
    segment_files = sorted([f for f in os.listdir(raw_dir) if f.endswith(".bin")])
    num_segments = len(segment_files)
    
    # Check epoch spike sorting status
    epoch_sorting_dir = os.path.join(computed_dir, "epoch_spike_sorting", epoch_id)
    has_epoch_sorting = (
        os.path.exists(os.path.join(epoch_sorting_dir, "templates.npy")) and
        os.path.exists(os.path.join(epoch_sorting_dir, "spike_times.npy")) and
        os.path.exists(os.path.join(epoch_sorting_dir, "spike_labels.npy")) and
        os.path.exists(os.path.join(epoch_sorting_dir, "spike_amplitudes.npy"))
    )
    
    # Check epoch preview status
    epoch_preview_dir = os.path.join(computed_dir, "epoch_preview", epoch_id, "epoch.figpack")
    has_epoch_preview = os.path.exists(epoch_preview_dir) and os.path.isdir(epoch_preview_dir)
    
    # Get epoch sorting statistics if available
    epoch_sorting_stats = None
    if has_epoch_sorting:
        import numpy as np
        spike_times = np.load(os.path.join(epoch_sorting_dir, "spike_times.npy"))
        spike_labels = np.load(os.path.join(epoch_sorting_dir, "spike_labels.npy"))
        templates = np.load(os.path.join(epoch_sorting_dir, "templates.npy"))
        
        # Load config to get segment duration
        config_path = os.path.join(os.getcwd(), "realtime512b.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            segment_duration_sec = config.get("raw_segment_duration_sec", 30)
            epoch_duration_sec = num_segments * segment_duration_sec
        else:
            epoch_duration_sec = None
        
        unique_labels = np.unique(spike_labels)
        epoch_sorting_stats = {
            "num_spikes": len(spike_times),
            "num_units": len(unique_labels),
            "num_templates": len(templates),
            "duration_sec": epoch_duration_sec,
            "min_time_sec": float(np.min(spike_times)) if len(spike_times) > 0 else None,
            "max_time_sec": float(np.max(spike_times)) if len(spike_times) > 0 else None
        }
    
    # Count segments with spike sorting
    spike_sorting_dir = os.path.join(computed_dir, "spike_sorting", epoch_id)
    num_segments_sorted = 0
    if os.path.exists(spike_sorting_dir):
        for segment_file in segment_files:
            segment_sorting_path = os.path.join(spike_sorting_dir, segment_file)
            if (os.path.exists(os.path.join(segment_sorting_path, "templates.npy")) and
                os.path.exists(os.path.join(segment_sorting_path, "spike_times.npy")) and
                os.path.exists(os.path.join(segment_sorting_path, "spike_labels.npy")) and
                os.path.exists(os.path.join(segment_sorting_path, "spike_amplitudes.npy"))):
                num_segments_sorted += 1
    
    return jsonify({
        "epoch": epoch_id,
        "num_segments": num_segments,
        "num_segments_sorted": num_segments_sorted,
        "has_epoch_sorting": has_epoch_sorting,
        "has_epoch_preview": has_epoch_preview,
        "epoch_sorting_stats": epoch_sorting_stats,
        "segments": segment_files
    })


def get_epoch_preview_file_handler(epoch_id, filepath):
    """Serves static files from epoch preview directories with range request support."""
    computed_dir = os.path.join(os.getcwd(), "computed")
    epoch_preview_dir = os.path.join(computed_dir, "epoch_preview", epoch_id, "epoch.figpack")
    
    if not os.path.exists(epoch_preview_dir):
        return jsonify({"error": "Epoch preview directory not found"}), 404
    
    # Serve the file with range request support
    return send_from_directory(
        epoch_preview_dir,
        filepath,
        conditional=True  # Enables range request support
    )
