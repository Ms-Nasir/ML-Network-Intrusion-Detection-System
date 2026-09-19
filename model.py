import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

class NIDSModel:
    def __init__(self, model_path='model/nids_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_columns = None
        
    def load_data(self, data_path):
        """Load the training data from a CSV file"""
        df = pd.read_csv(data_path)
        return df
        
    def preprocess_data(self, df):
        """Preprocess the data for training"""
        # Convert non-numeric columns to numeric using one-hot encoding
        categorical_cols = ['protocol_type', 'service', 'flag']
        df_encoded = pd.get_dummies(df, columns=categorical_cols)
        
        # Split into features and target
        X = df_encoded.drop('class', axis=1)
        y = df_encoded['class'].apply(lambda x: 1 if x == 'anomaly' else 0)
        
        # Store feature columns for later use
        self.feature_columns = X.columns
        
        # Normalize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
        
    def train_model(self, data_path, test_size=0.2, random_state=42):
        """Train the random forest model"""
        df = self.load_data(data_path)
        X, y = self.preprocess_data(df)
        
        # Split into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Train the model
        self.model = RandomForestClassifier(
            n_estimators=100, 
            random_state=random_state,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.model.predict(X_test)
        print("Model Evaluation:")
        print(classification_report(y_test, y_pred))
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }, f)
        
        print(f"Model saved to {self.model_path}")
        
    def load_model(self):
        """Load a previously trained model"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
            print(f"Model loaded from {self.model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_single_record(self, record):
        """Preprocess a single network record for prediction"""
        # Convert record to DataFrame
        if isinstance(record, dict):
            df = pd.DataFrame([record])
        else:
            df = record
            
        # One-hot encode categorical features
        categorical_cols = ['protocol_type', 'service', 'flag']
        df_encoded = pd.get_dummies(df, columns=categorical_cols)
        
        # Ensure all columns from training are present
        for col in self.feature_columns:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        
        # Select only the columns used during training
        df_encoded = df_encoded[self.feature_columns]
        
        # Scale the features
        X_scaled = self.scaler.transform(df_encoded)
        
        return X_scaled
        
    def predict(self, record):
        """Predict whether a network record is an attack or normal"""
        if self.model is None:
            if not self.load_model():
                raise Exception("Model not loaded. Train or load a model first.")
        
        X = self.preprocess_single_record(record)
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0][1]
        
        return {
            'is_attack': bool(prediction),
            'probability': float(probability),
            'prediction': 'anomaly' if prediction == 1 else 'normal'
        }

if __name__ == "__main__":
    # Train the model if this script is run directly
    model = NIDSModel()
    model.train_model("data/nids_data.csv")
    
    # Test the model with a sample record
    sample = {
        'duration': 0,
        'protocol_type': 'tcp',
        'service': 'private',
        'flag': 'S0',
        'src_bytes': 0,
        'dst_bytes': 0,
        'land': 0,
        'wrong_fragment': 0,
        'urgent': 0,
        'hot': 0,
        'num_failed_logins': 0,
        'logged_in': 0,
        'num_compromised': 0,
        'root_shell': 0,
        'su_attempted': 0,
        'num_root': 0,
        'num_file_creations': 0,
        'num_shells': 0,
        'num_access_files': 0,
        'num_outbound_cmds': 0,
        'is_host_login': 0,
        'is_guest_login': 0,
        'count': 123,
        'srv_count': 6,
        'serror_rate': 1,
        'srv_serror_rate': 1,
        'rerror_rate': 0,
        'srv_rerror_rate': 0,
        'same_srv_rate': 0.05,
        'diff_srv_rate': 0.07,
        'srv_diff_host_rate': 0,
        'dst_host_count': 255,
        'dst_host_srv_count': 26,
        'dst_host_same_srv_rate': 0.1,
        'dst_host_diff_srv_rate': 0.05,
        'dst_host_same_src_port_rate': 0,
        'dst_host_srv_diff_host_rate': 0,
        'dst_host_serror_rate': 1,
        'dst_host_srv_serror_rate': 1,
        'dst_host_rerror_rate': 0,
        'dst_host_srv_rerror_rate': 0
    }
    
    result = model.predict(sample)
    print(f"Prediction: {result}")