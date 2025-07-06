import os
from PyQt5.QtWidgets import QMessageBox
from TCNInferenceManager import TCNInferenceManager

class AppInitializer:
    """
    Initializes application-wide components, such as the TCNInferenceManager.
    This class centralizes the setup logic for core services.
    """
    def __init__(self):
        self.tcn_inference_manager = None
        self._initialize_tcn_manager()

    def _initialize_tcn_manager(self):
        """
        Initializes the TCNInferenceManager.
        The model path and class names can be hardcoded here or loaded from 
        a configuration file (e.g., config.py).
        """
        current_dir = os.path.dirname(__file__)
        TCN_MODEL_PATH = os.path.join(current_dir, "tcn_model.tflite")
        #BEHAVIOR_CLASS_NAMES = ["Walking", "Running", "Eating", "Lying", "Standing", "Barking", "Other"] 
        BEHAVIOR_CLASS_NAMES = ["standing", "lying", "running", "walking", "sniffing", "shaking", "eating", "drinking", "barking"] 

        print(f"Attempting to load TCN model from: {TCN_MODEL_PATH}")

        try:
            self.tcn_inference_manager = TCNInferenceManager(
                model_path=TCN_MODEL_PATH,
                input_window_size=250, 
                input_features=4, 
                class_names=BEHAVIOR_CLASS_NAMES
            )
        except FileNotFoundError as e:
            QMessageBox.critical(None, "TCN Model Load Error", f"TCN model file not found: {e}\n"
                                                                f"Please check the path: {TCN_MODEL_PATH}")
            self.tcn_inference_manager = None # Set to None on error to prevent further inference attempts
        except Exception as e:
            QMessageBox.critical(None, "TCN Model Load Error", f"An error occurred while loading the TCN model: {e}")
            self.tcn_inference_manager = None

    def get_tcn_inference_manager(self) -> TCNInferenceManager:
        """
        Returns the initialized TCNInferenceManager instance.
        """
        return self.tcn_inference_manager