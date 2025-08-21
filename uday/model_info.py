#!/usr/bin/env python3
"""
Model Information Tool
Analyzes Ben's neural network models to show parameters, architecture, etc.
"""

import sys
import os
import argparse
import warnings
warnings.filterwarnings('ignore')

# Set environment variables before importing TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
from tensorflow.keras.models import load_model

def analyze_model(model_path):
    """Analyze a Keras model and return information about it."""
    print(f"Analyzing model: {model_path}")
    print(f"TensorFlow version: {tf.__version__}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model
    print("Loading model...")
    model = load_model(model_path, compile=False)
    
    # Basic info
    print(f"\n{'='*60}")
    print(f"MODEL INFORMATION")
    print(f"{'='*60}")
    
    # Model summary
    print("\n--- Model Architecture ---")
    model.summary()
    
    # Count parameters
    total_params = model.count_params()
    trainable_params = sum([w.shape.num_elements() for w in model.trainable_weights])
    non_trainable_params = total_params - trainable_params
    
    print(f"\n--- Parameter Count ---")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Non-trainable parameters: {non_trainable_params:,}")
    
    # Model input/output shapes
    print(f"\n--- Input/Output Information ---")
    if hasattr(model, 'input_shape'):
        print(f"Input shape: {model.input_shape}")
    elif hasattr(model, 'inputs'):
        print(f"Input shapes: {[inp.shape for inp in model.inputs]}")
    
    if hasattr(model, 'output_shape'):
        print(f"Output shape: {model.output_shape}")
    elif hasattr(model, 'outputs'):
        print(f"Output shapes: {[out.shape for out in model.outputs]}")
    
    # Layer information
    print(f"\n--- Layer Details ---")
    for i, layer in enumerate(model.layers):
        layer_params = layer.count_params()
        print(f"Layer {i:2d}: {layer.__class__.__name__:15s} - {layer.name:20s} - {layer_params:8,} params")
        if hasattr(layer, 'units') and layer.units:
            print(f"          Units: {layer.units}")
        if hasattr(layer, 'activation') and layer.activation:
            print(f"          Activation: {layer.activation.__name__}")
    
    # Memory usage estimate
    print(f"\n--- Memory Estimates ---")
    
    # Calculate model size in MB
    model_size_mb = total_params * 4 / (1024 * 1024)  # Assuming float32
    print(f"Model size (float32): ~{model_size_mb:.1f} MB")
    
    # File size
    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"File size on disk: {file_size_mb:.1f} MB")
    
    return {
        'total_params': total_params,
        'trainable_params': trainable_params,
        'non_trainable_params': non_trainable_params,
        'model_size_mb': model_size_mb,
        'file_size_mb': file_size_mb,
        'num_layers': len(model.layers)
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze Ben neural network models')
    parser.add_argument('model', help='Path to model file (e.g., models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras)')
    parser.add_argument('--compare', help='Path to second model for comparison')
    
    args = parser.parse_args()
    
    try:
        info1 = analyze_model(args.model)
        
        if args.compare:
            print(f"\n{'='*60}")
            print(f"COMPARISON MODEL")
            print(f"{'='*60}")
            info2 = analyze_model(args.compare)
            
            print(f"\n{'='*60}")
            print(f"COMPARISON SUMMARY")
            print(f"{'='*60}")
            print(f"{'Parameter':<25} {'Model 1':<15} {'Model 2':<15} {'Difference':<15}")
            print(f"{'-'*70}")
            print(f"{'Total params':<25} {info1['total_params']:<15,} {info2['total_params']:<15,} {info2['total_params']-info1['total_params']:<15,}")
            print(f"{'Model size (MB)':<25} {info1['model_size_mb']:<15.1f} {info2['model_size_mb']:<15.1f} {info2['model_size_mb']-info1['model_size_mb']:<15.1f}")
            print(f"{'File size (MB)':<25} {info1['file_size_mb']:<15.1f} {info2['file_size_mb']:<15.1f} {info2['file_size_mb']-info1['file_size_mb']:<15.1f}")
            print(f"{'Number of layers':<25} {info1['num_layers']:<15} {info2['num_layers']:<15} {info2['num_layers']-info1['num_layers']:<15}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()