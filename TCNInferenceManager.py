# TCNInferenceManager.py

import bisect
import tensorflow as tf
import numpy as np
import pandas as pd
import os
from typing import List, Tuple, Dict 

class TCNInferenceManager:
    """
    Manages the loading and inference of a TensorFlow Lite TCN model
    for sensor data.
    """
    def __init__(self, model_path: str, input_window_size: int = 250, input_features: int = 3, class_names: list = None):
        """
        Initializes the TCN inference manager.

        Args:
            model_path (str): Path to the TensorFlow Lite model file.
            input_window_size (int): Number of samples in the input window for the model. 
                                     Default is 250 (2.5 seconds * 100Hz).
            input_features (int): Number of features (e.g., acc_x, acc_y, acc_z) per sample. 
                                  Default is 3.
            class_names (list): List of behavior class names corresponding to model output indices.
        """
        self.model_path = model_path
        self.interpreter = None
        self.input_window_size = input_window_size
        self.input_features = input_features
        self.class_names = class_names if class_names is not None else ["Unknown"] 
        self._load_model()
        
        # List to store inference results as tuples: 
        # [(start_timestamp_ms, end_timestamp_ms, predicted_behavior_name_with_global_counter), ...]
        self._predictions: List[Tuple[int, int, str]] = [] 
        
        # Global counter for all inferences
        self._inference_counter: int = 0

    def _load_model(self):
        """
        Loads the TensorFlow Lite model.
        Sets self.interpreter to None if loading fails.
        """
        if not os.path.exists(self.model_path):
            print(f"Error: TCN model file not found at: {self.model_path}")
            self.interpreter = None 
            return
        
        try:
            self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            print(f"TCN Model loaded successfully from: {self.model_path}")
            print(f"  Input shape: {self.input_details[0]['shape']}")
            print(f"  Output shape: {self.output_details[0]['shape']}")
        except Exception as e:
            print(f"Error loading TCN model: {e}")
            self.interpreter = None 

    def perform_inference_on_data(self, sensor_df: pd.DataFrame):
        """
        Performs TCN inference on the entire sensor DataFrame using a sliding window approach
        and stores the results internally as a list of (start_time, end_time, behavior_with_counter) tuples.

        This function assumes:
        1. 'timestamp' column in sensor_df is in milliseconds.
        2. Required raw features are 'acc_x', 'acc_y', 'acc_z'.
        3. An additional 'magnitude' feature is calculated from these three.
        4. Data is scaled using pre-defined mean and standard deviation values.
        5. Includes a defense mechanism to discard windows with significant timestamp gaps.
        6. Each valid prediction gets a unique, sequential counter.

        Args:
            sensor_df (pd.DataFrame): DataFrame containing sensor data. Expected columns:
                                      'timestamp', 'acc_x', 'acc_y', 'acc_z'.
        """
        self._predictions = [] # Reset previous prediction results
        self._inference_counter = 0 # Reset the global counter for new data

        if self.interpreter is None:
            print("TCN model is not loaded. Cannot perform prediction.")
            return

        # Define the raw feature columns
        raw_feature_columns = ['acc_x', 'acc_y', 'acc_z'] 
        
        # Check if all required raw feature columns exist in the DataFrame
        if not all(col in sensor_df.columns for col in raw_feature_columns):
            print(f"Error: Missing one or more required raw feature columns. Expected: {raw_feature_columns}. Found: {sensor_df.columns.tolist()}")
            return

        # 1. Extract raw acceleration data
        accel_data = sensor_df[raw_feature_columns].values 

        # 2. Calculate magnitude 
        magnitude = np.sqrt(np.sum(np.square(accel_data), axis=1, keepdims=True))

        # 3. Combine raw features and magnitude
        feature_data = np.hstack((accel_data, magnitude)) 

        # Ensure input_features matches the prepared feature count (4)
        if self.input_features != 4:
            print(f"Warning: TCNInferenceManager initialized with input_features={self.input_features}, but 4 features are being prepared (acc_x, acc_y, acc_z, magnitude). "
                  "Ensure your TCN model expects 4 features. Temporarily setting input_features to 4 for this inference run.")
            self.input_features = 4 

        timestamps = sensor_df['timestamp'].values 
        num_samples = len(sensor_df)
        
        # Calculate the expected duration of one window in milliseconds
        # Assuming 100Hz sampling rate implies 100 samples per second, so each sample represents 10ms.
        sample_interval_ms = 1000 / 100 
        expected_window_duration_ms = int(self.input_window_size * sample_interval_ms) 
        
        # Define the maximum allowed gap for a valid window (e.g., 3 seconds)
        MAX_ALLOWED_WINDOW_DURATION_MS = 3000 # 3 seconds in milliseconds (adjust as needed)

        # Retrieve input tensor details to check expected shape and data type
        input_details = self.interpreter.get_input_details()[0]
        input_shape = input_details['shape']
        input_dtype = input_details['dtype']

        # Ensure the expected input shape from the model matches our manager's settings
        if len(input_shape) != 3 or input_shape[1] != self.input_window_size or input_shape[2] != self.input_features:
            print(f"Error: TCN model's expected input shape {input_shape} does not match prepared features (batch, {self.input_window_size}, {self.input_features}).")
            print("Please verify 'input_window_size' and 'input_features' during TCNInferenceManager initialization and ensure they match your model.")
            return

        # Define mean and standard deviation for scaling
        mean = np.array([[[-0.17672844, -0.08874533, -4.21656531, 10.17833267]]], dtype=np.float32)
        std = np.array([[[4.58728252, 6.29407456, 5.87849594, 3.07169755]]], dtype=np.float32)

        # Ensure std values are not zero to prevent division by zero
        if np.any(std == 0):
            print("Warning: Standard deviation contains zero values. Replacing with small epsilon to avoid division by zero.")
            std = np.where(std == 0, 1e-8, std) 

        def _scale_data(data_array, mean_arr, std_arr):
            """Applies Z-score scaling to a numpy array."""
            return (data_array - mean_arr) / std_arr

        # Perform inference using a non-overlapping sliding window
        for i in range(0, num_samples - self.input_window_size + 1, self.input_window_size):
            window_data = feature_data[i : i + self.input_window_size]
            
            # --- Defense Code for Timestamp Gaps ---
            start_timestamp_ms = timestamps[i] 
            end_timestamp_ms = timestamps[i + self.input_window_size - 1] # Timestamp of the last sample in the window
            
            actual_window_duration = end_timestamp_ms - start_timestamp_ms
            
            # If the actual duration is significantly different from the expected duration
            if actual_window_duration > MAX_ALLOWED_WINDOW_DURATION_MS:
                print(f"Skipping prediction for window starting at {start_timestamp_ms}ms due to large timestamp gap. "
                      f"Actual duration: {actual_window_duration}ms, Expected ~{expected_window_duration_ms}ms, Max allowed: {MAX_ALLOWED_WINDOW_DURATION_MS}ms.")
                continue # Skip this window and move to the next
            # --- End Defense Code ---

            scaled_window_data = _scale_data(window_data, mean, std)
            
            # Reshape data to match model's expected input shape: (1, input_window_size, input_features)
            input_data = np.array(scaled_window_data, dtype=input_dtype).reshape(1, self.input_window_size, self.input_features)

            self.interpreter.set_tensor(input_details['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            predicted_class_idx = np.argmax(output_data[0])
            predicted_behavior = "Unknown"
            if self.class_names and predicted_class_idx < len(self.class_names):
                predicted_behavior = self.class_names[predicted_class_idx]
            
            # Increment the global counter for each valid prediction
            self._inference_counter += 1
            behavior_with_counter = f"{predicted_behavior}-{self._inference_counter}"
            
            self._predictions.append((start_timestamp_ms, end_timestamp_ms, behavior_with_counter))
            
        print(f"TCN inference completed. Generated {len(self._predictions)} predictions for {num_samples} samples.")

    def get_predicted_behavior_at_timestamp(self, timestamp_ms: int) -> str:
        """
        Retrieves the predicted behavior for a given timestamp (in milliseconds) using binary search.
        It efficiently finds the prediction window that contains the given timestamp.
        Returns the behavior in "TCN::BEHAVIOR_NAME-COUNT::" format.

        Args:
            timestamp_ms (int): The timestamp in milliseconds to query.

        Returns:
            str: The predicted behavior string in "TCN::BEHAVIOR_NAME-COUNT::" format,
                 or "N/A (No TCN predictions loaded)" if no predictions are available,
                 or "N/A (No TCN prediction for this time)" if the timestamp falls outside any predicted window.
        """
        if not self._predictions:
            return "N/A (No TCN predictions loaded)" 

        start_timestamps = [pred[0] for pred in self._predictions]
        idx = bisect.bisect_right(start_timestamps, timestamp_ms)

        if idx == 0:
            return "N/A (No TCN prediction for this time)"
        
        candidate_idx = idx - 1 
        start_ts, end_ts, behavior_with_counter = self._predictions[candidate_idx]

        if start_ts <= timestamp_ms < end_ts:
            # Return the behavior with the global counter, formatted as "TCN::BEHAVIOR_NAME-COUNT::"
            return f"TCN::{behavior_with_counter}::" 
        
        return "N/A (No TCN prediction for this time)"