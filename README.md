# 🚀 **Algorzen Data Quality Toolkit**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![React](https://img.shields.io/badge/React-18.0.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-green.svg)](https://fastapi.tiangolo.com/)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/algorzen)

> **Enterprise-grade data quality toolkit with modern React dashboard, comprehensive validation rules, and real-time monitoring capabilities.**

---

## ✨ **What Makes This Special**

<div align="center">

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Preview-blue?style=for-the-badge&logo=react)

**Professional React Dashboard • FastAPI Backend • Real-time Monitoring • ML-Powered Quality Scoring**

</div>

---

## 🎯 **Key Features**

### 🎨 **Modern User Experience**
- **React 18 Dashboard** with glassmorphism design
- **Framer Motion** animations and smooth transitions
- **Responsive Design** for all devices
- **Professional UI/UX** inspired by Scale AI

### 🔍 **Comprehensive Data Quality**
- **Statistical Analysis** (outliers, distributions, correlations)
- **Pattern Recognition** (regex, format validation, business rules)
- **Cross-Column Validation** (relationships, conditional logic)
- **ML-Powered Scoring** (Isolation Forest, DBSCAN, K-means)

### 🚀 **Enterprise Architecture**
- **FastAPI Backend** with async support
- **Modular Design** for easy extension
- **Real-time Monitoring** with Prometheus + Grafana
- **Multi-format Support** (CSV, JSON, Excel, Parquet, databases)

### 🛠️ **Developer Experience**
- **Rich CLI** with animations and colors
- **Comprehensive API** with auto-generated docs
- **Docker Support** for easy deployment
- **Extensive Testing** framework

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI       │    │   Data Quality  │
│   (Port 3000)   │◄──►│   API Server    │◄──►│   Engine        │
│   Modern UI     │    │   (Port 8000)   │    │   Core Logic    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Glassmorphism UI      RESTful Endpoints      ML Algorithms
   Framer Motion         CORS Enabled          Statistical Analysis
   Responsive Design     Auto-docs             Quality Scoring
```

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10+
- Node.js 16+
- Docker (for monitoring stack)

### **1. Clone & Install**
```bash
git clone https://github.com/algorzen/data-quality-toolkit.git
cd data-quality-toolkit

# Install Python dependencies
pip install -e .

# Install React dependencies
cd frontend/algorzen-dashboard
npm install
cd ../..
```

### **2. Start Everything (Recommended)**
```bash
# Make script executable
chmod +x start_dashboard.sh

# Start both API server and React dashboard
./start_dashboard.sh
```

### **3. Manual Startup**
```bash
# Terminal 1: Start API server
algorzen-dqt api-server --port 8000

# Terminal 2: Start React dashboard
cd frontend/algorzen-dashboard
npm start
```

### **4. Access Your Dashboard**
- 🌐 **React Dashboard**: http://localhost:3000
- 📊 **API Server**: http://127.0.0.1:8000
- 📚 **API Docs**: http://127.0.0.1:8000/docs

---

## 🎨 **Dashboard Features**

### **📊 Real-time Analytics**
- Live quality score tracking
- Interactive charts and visualizations
- Performance metrics and system health
- Trend analysis and benchmarking

### **🔧 Quality Management**
- Interactive quality check execution
- Custom business rule configuration
- Automated task scheduling
- Comprehensive result reporting

### **👥 Team Collaboration**
- Multi-workspace management
- Team member roles and permissions
- Project tracking and progress
- Resource sharing capabilities

### **📈 Monitoring & Alerting**
- System health monitoring
- Quality metrics tracking
- Proactive issue detection
- Grafana integration

---

## 🐍 **CLI Commands**

<img width="1463" height="426" alt="Screenshot 2025-08-27 at 22 17 41" src="https://github.com/user-attachments/assets/ed7c2d84-b01e-4245-abe3-573f1a4a841a" />

```bash
# Quality Checks
algorzen-dqt check data.csv                    # Run quality checks
algorzen-dqt profile data.csv                  # Generate data profile
algorzen-dqt validate                          # Validate system

# Dashboard & API
algorzen-dqt api-server                        # Start API server
algorzen-dqt monitoring                        # Launch monitoring stack

# Monitoring
algorzen-dqt grafana                           # Start Grafana
algorzen-dqt prometheus                        # Start Prometheus
algorzen-dqt status                            # Check service status

# Help & Info
algorzen-dqt --help                            # Show all commands
algorzen-dqt version                           # Version information
```

---

## 🔌 **API Endpoints**

### **Core Endpoints**
- `GET /api/business-rules/` - Manage validation rules
- `GET /api/scheduler/` - Task scheduling
- `GET /api/monitoring/system-health` - System metrics
- `GET /api/workspaces/` - Team collaboration
- `GET /api/projects/` - Project management

### **Quality Checks**
- `POST /api/quality-checks/run` - Execute quality checks
- `GET /api/quality-checks/results` - Get check results
- `POST /api/quality-checks/reports` - Generate reports

---

## 📊 **Data Quality Capabilities**

### **Statistical Analysis**
- **Outlier Detection**: Z-score, IQR, percentile-based
- **Distribution Analysis**: Skewness, kurtosis, normality tests
- **Correlation Analysis**: Cross-column relationships
- **Data Profiling**: Comprehensive statistical summaries

### **Pattern Recognition**
- **Regex Validation**: Custom pattern matching
- **Format Validation**: Email, phone, credit card, SSN
- **Business Rules**: Visual rule builder
- **Sequence Validation**: Chronological order, ID sequences

### **Machine Learning**
- **Anomaly Detection**: Isolation Forest, DBSCAN
- **Quality Scoring**: Random Forest-based prediction
- **Feature Engineering**: Automated selection and preprocessing
- **Performance Optimization**: Parallel processing, caching

---

## 🚀 **Performance & Scalability**

- **Big Data Support**: Apache Spark, Dask integration
- **Real-time Processing**: Stream processing capabilities
- **Cloud Integration**: AWS, Azure, Google Cloud
- **Containerization**: Docker, Kubernetes support
- **Auto-scaling**: Cloud platform optimization

---

## 🛡️ **Security & Compliance**

- **JWT Authentication**: Secure API access
- **Role-based Access**: Granular permissions
- **Data Encryption**: In transit and at rest
- **Audit Logging**: Comprehensive activity tracking
- **GDPR Compliance**: Privacy protection features

---

## 📚 **Documentation**

- **[Dashboard Setup](DASHBOARD_SETUP.md)** - Complete setup guide
- **[API Reference](http://127.0.0.1:8000/docs)** - Interactive API docs
- **[Project Analysis](PROJECT_ANALYSIS.md)** - Technical deep-dive
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Feature completion

---

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black algorzen_dqt/
flake8 algorzen_dqt/
```

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 **Authors**

**Rishi R Carloni & the Algorzen team**

- 🌐 **Website**: [algorzen.com](https://algorzen.com)
- 📧 **Email**: rishi@algorzen.com
- 🐦 **Twitter**: [@algorzen](https://twitter.com/algorzen)
- 💼 **LinkedIn**: [Algorzen](https://linkedin.com/company/algorzen)

---

## 🙏 **Acknowledgments**

- **React Team** for the amazing frontend framework
- **FastAPI Team** for the high-performance API framework
- **Python Community** for the rich ecosystem
- **Open Source Contributors** who made this possible

---

<div align="center">

### **🌟 Star this repository if you find it helpful! 🌟**

[![GitHub stars](https://img.shields.io/github/stars/algorzen/data-quality-toolkit?style=social)](https://github.com/algorzen/data-quality-toolkit)
[![GitHub forks](https://img.shields.io/github/forks/algorzen/data-quality-toolkit?style=social)](https://github.com/algorzen/data-quality-toolkit)
[![GitHub issues](https://img.shields.io/github/issues/algorzen/data-quality-toolkit)](https://github.com/algorzen/data-quality-toolkit/issues)

**Made with ❤️ by the Algorzen Team**

</div>
