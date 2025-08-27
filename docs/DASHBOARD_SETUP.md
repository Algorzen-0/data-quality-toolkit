# 🚀 **Algorzen Data Quality Toolkit - Dashboard Setup**

## 🎯 **Overview**

The Algorzen Data Quality Toolkit now uses a **React frontend** with a **FastAPI backend** instead of the old Python dashboard. This provides a modern, professional user experience with all the same functionality.

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI       │    │   Data Quality  │
│   (Port 3000)   │◄──►│   Server        │◄──►│   Engine        │
│                 │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **Quick Start**

### **Option 1: Automated Startup (Recommended)**
```bash
# Make the script executable (first time only)
chmod +x start_dashboard.sh

# Start both API server and React dashboard
./start_dashboard.sh
```

### **Option 2: Manual Startup**
```bash
# Terminal 1: Start API server
algorzen-dqt api-server --host 127.0.0.1 --port 8000

# Terminal 2: Start React dashboard
cd frontend/algorzen-dashboard
npm start
```

## 🌐 **Access URLs**

- **React Dashboard**: http://localhost:3000
- **API Server**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## 🎨 **React Dashboard Features**

### **✅ Fully Working**
- **Modern UI**: Professional glassmorphism design
- **Quality Checks**: Interactive quality analysis
- **Team Workspaces**: Collaboration and project management
- **Task Scheduler**: Automated task scheduling
- **Business Rules**: Custom validation rules
- **Real-time Monitoring**: System health and metrics
- **Data Persistence**: localStorage-based state management

### **🔧 Technical Stack**
- **React 18** with TypeScript
- **Framer Motion** for animations
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons

## 🐍 **API Server Features**

### **✅ Available Endpoints**
- **Business Rules**: `/api/business-rules/`
- **Scheduler**: `/api/scheduler/`
- **Monitoring**: `/api/monitoring/`
- **Workspaces**: `/api/workspaces/`
- **Projects**: `/api/projects/`

### **🔧 Technical Stack**
- **FastAPI** for high-performance API
- **CORS** enabled for React frontend
- **Pydantic** for data validation
- **Uvicorn** ASGI server

## 🧪 **Testing the Setup**

### **1. Test API Server**
```bash
# Start API server
algorzen-dqt api-server --port 8000

# Test endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/business-rules/
```

### **2. Test React Dashboard**
```bash
# Start React app
cd frontend/algorzen-dashboard
npm start

# Open browser to http://localhost:3000
```

### **3. Test Full Integration**
```bash
# Use the startup script
./start_dashboard.sh
```

## 🗑️ **What Was Removed**

- ❌ **Python Dashboard**: `launch_dashboard.py`
- ❌ **Dashboard API**: `algorzen_dqt/api/dashboard.py`
- ❌ **Dashboard CLI Command**: `algorzen-dqt dashboard`

## 🔄 **Migration Notes**

### **Old Way (Removed)**
```bash
algorzen-dqt dashboard --host 127.0.0.1 --port 8000
```

### **New Way**
```bash
# Start API server
algorzen-dqt api-server --host 127.0.0.1 --port 8000

# Start React dashboard
cd frontend/algorzen-dashboard && npm start
```

## 🚨 **Troubleshooting**

### **Port Already in Use**
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process or use different ports
algorzen-dqt api-server --port 8001
```

### **React Dependencies Missing**
```bash
cd frontend/algorzen-dashboard
npm install
```

### **API Server Won't Start**
```bash
# Check if all Python dependencies are installed
pip install -e .

# Check for import errors
python -c "from algorzen_dqt.api.server import app"
```

## 📚 **Additional Resources**

- **React Dashboard Guide**: `frontend/README.md`
- **API Documentation**: http://127.0.0.1:8000/docs
- **Project Analysis**: `PROJECT_ANALYSIS.md`
- **Implementation Status**: `IMPLEMENTATION_STATUS.md`

## 🎉 **Benefits of New Setup**

1. **Better Performance**: React is faster than server-rendered HTML
2. **Modern UX**: Professional animations and interactions
3. **Easier Development**: Separate frontend/backend concerns
4. **Better Testing**: Can test frontend and backend independently
5. **Scalability**: React can be deployed separately from API
6. **Maintainability**: Clear separation of concerns

---

**Ready to use the modern React dashboard!** 🚀
