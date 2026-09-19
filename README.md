# Machine Learning-Based Network Intrusion Detection System

A web-based Machine Learning Network Intrusion Detection System (NIDS) designed for real-time network traffic monitoring, anomaly detection, and security alert visualization.

The system combines **Python, Flask, Flask-SocketIO, Scapy, and Random Forest** to capture network traffic, extract features, classify traffic as normal or anomalous, and display high-confidence alerts through a web dashboard.

## 🔎 Overview

The system provides a real-time security monitoring workflow:

```text
Network Traffic
      ↓
Packet Capture (Scapy)
      ↓
Packet & Feature Extraction
      ↓
Feature Preprocessing
      ↓
Random Forest Classification
      ↓
Anomaly Probability
      ↓
Security Alert
      ↓
Web Dashboard
```

### 🚀 Key Features

- Real-time IPv4 packet capture using Scapy
- Network interface monitoring
- TCP, UDP, and ICMP traffic identification
- IP address and port extraction
- Network service identification
- Connection statistics and traffic tracking
- Feature preprocessing using one-hot encoding
- Feature normalization using StandardScaler
- Random Forest-based anomaly classification
- Anomaly probability calculation
- High-confidence alert generation
- Real-time dashboard updates using Flask-SocketIO
- Alert history and network statistics
- Dataset-based model training
- Model persistence using Pickle

---

### 🧠 Machine Learning

The system uses a Random Forest Classifier for binary network anomaly detection.

**Model Pipeline**

1. Load the training dataset
2. Encode categorical features
3. Separate features and target
4. Normalize numerical features
5. Split data into training and testing sets
6. Train the Random Forest classifier
7. Generate predictions
8. Produce a classification report and confusion matrix
9. Save the trained model

The model classifies traffic into:

- normal
- anomaly

The real-time monitoring component generates an alert when the model predicts an attack with a probability greater than 0.70.

--- 

### 🌐 Web Dashboard

The application provides a browser-based monitoring interface with real-time communication through Flask-SocketIO.

The dashboard receives:

- Network statistics
- Packet information
- Security alerts
- Model training status
- Monitoring status

| Endpoint            | Method | Purpose                     |
| ------------------- | ------ | --------------------------- |
| `/`                 | GET    | Web dashboard               |
| `/api/interfaces`   | GET    | Retrieve network interfaces |
| `/api/start`        | POST   | Start network monitoring    |
| `/api/stop`         | POST   | Stop network monitoring     |
| `/api/status`       | GET    | Check monitoring status     |
| `/api/alerts`       | GET    | Retrieve recent alerts      |
| `/api/load_dataset` | POST   | Load training dataset       |
| `/api/train_model`  | POST   | Start model training        |

--- 

### 🛠️ Technologies

- Python
- Flask
- Flask-SocketIO
- Scapy
- Pandas
- NumPy
- Scikit-learn
- Random Forest
- HTML
- CSS
- JavaScript

--- 

### ⚙️ Installation

1. Clone the repository:

git clone https://github.com/Ms-Nasir/ML-Network-Intrusion-Detection-System.git

2. Enter the project directory:

cd ML-Network-Intrusion-Detection-System

3. Install dependencies:

pip install -r requirements.txt

--- 

### 📊 Dataset

The original training dataset is not included in this repository because of its size.

The application expects the dataset at:

data/nids_data.csv

The dataset is used for model preprocessing, training, and evaluation.

--- 

### ▶️ Running the Application

After preparing the required dataset:

python server.py

The Flask application runs on port 5000 by default.

Open the dashboard in a browser:

http://127.0.0.1:5000

For network packet capture, appropriate permissions may be required depending on the operating system and network configuration.

--- 

### 📈 Model Evaluation

During training, the system generates:

- Classification report
- Confusion matrix

These outputs can be used to evaluate the Random Forest classifier's performance on the test data.

Actual accuracy, precision, recall, and F1-score values should be reported only from a recorded model-training run.

--- 

### 🔐 Cybersecurity Applications

This project demonstrates concepts relevant to:

- Network intrusion detection
- Security monitoring
- Network traffic analysis
- Anomaly detection
- SOC operations
- Incident investigation
- Detection engineering
- Security alerting
- Machine learning for cybersecurity

--- 

###⚠️ Limitations

The current real-time feature extraction uses several simplified or placeholder values because some dataset features require deeper connection-level or application-level analysis.

Therefore, the system should be considered an educational/research NIDS prototype, rather than a production-grade enterprise IDS.

Detection performance depends on the quality and compatibility of the training dataset and extracted real-time features.

--- 

### 🔮 Future Enhancements

- More comprehensive flow-based feature extraction
- Advanced attack classification
- Improved connection tracking
- PCAP export and replay
- Advanced alert severity classification
- Email/security-team notifications
- SIEM integration
- Improved detection rules
- More comprehensive network protocol analysis
- Production-grade deployment

--- 

### 🎓 Project Type

Final Year Project — Cybersecurity / Machine Learning

### ⚖️ Disclaimer

This project is intended for educational, research, and authorized cybersecurity testing purposes.

--- 

### 👩‍💻 Author

Ms. Nasir

Cybersecurity | SOC Operations | Network Security | Digital Forensics
