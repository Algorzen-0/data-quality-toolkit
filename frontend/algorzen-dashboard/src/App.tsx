import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, 
  Upload, 
  Settings, 
  Users, 
  Clock, 
  Shield, 
  Database, 
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  TrendingUp,
  FileText,
  Zap,
  Globe,
  Cloud,
  Sparkles,
  Brain
} from 'lucide-react';

// Types
interface QualityCheckResult {
  id: string;
  filename: string;
  timestamp: string;
  overall_score: number;
  status: 'passed' | 'failed' | 'warning';
  execution_time: number;
  checks: {
    name: string;
    status: 'passed' | 'failed' | 'warning';
    score: number;
    details: {
      metric: string;
      value: string | number;
      threshold: string | number;
      status: 'passed' | 'failed' | 'warning';
    }[];
  }[];
}

interface DashboardStats {
  total_workspaces: number;
  total_tasks: number;
  total_rules: number;
  active_tasks: number;
  system_health: string;
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [qualityResults, setQualityResults] = useState<QualityCheckResult[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    total_workspaces: 12,
    total_tasks: 45,
    total_rules: 28,
    active_tasks: 8,
    system_health: 'healthy'
  });

  // Quality Check Modal States
  const [showQualityModal, setShowQualityModal] = useState(false);
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [checkTypes, setCheckTypes] = useState<string[]>([]);
  const [isRunningCheck, setIsRunningCheck] = useState(false);

  // Quality Rules Configuration
  const [qualityRules, setQualityRules] = useState({
    missingValuesThreshold: 5,
    duplicateTolerance: 2,
    outlierDetectionMethod: 'IQR',
    dataTypeValidation: true,
    rangeValidation: true,
    emailValidation: true,
    phoneValidation: true,
    dateValidation: true
  });

  // Workspace States
  const [workspaces, setWorkspaces] = useState([
    { id: '1', name: 'Data Science Lab', team: 'Data Science', members: 8, projects: 12, description: 'Advanced analytics and ML research workspace' },
    { id: '2', name: 'Engineering Hub', team: 'Engineering', members: 15, projects: 24, description: 'Software development and infrastructure workspace' },
    { id: '3', name: 'Analytics Center', team: 'Analytics', members: 6, projects: 8, description: 'Business intelligence and reporting workspace' }
  ]);
  const [showCreateWorkspaceModal, setShowCreateWorkspaceModal] = useState(false);
  const [showEditWorkspaceModal, setShowEditWorkspaceModal] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [showManageProjectsModal, setShowManageProjectsModal] = useState(false);
  const [newWorkspace, setNewWorkspace] = useState({ name: '', team: '', description: '' });
  const [editingWorkspace, setEditingWorkspace] = useState<any>(null);
  const [selectedWorkspace, setSelectedWorkspace] = useState<any>(null);
  const [newMember, setNewMember] = useState({ email: '', role: 'member' });
  const [newProject, setNewProject] = useState({ name: '', description: '', project_type: 'data_quality', priority: 'medium' });

  // Projects state
  const [projects, setProjects] = useState([
    { id: '1', name: 'Customer Data Quality Pipeline', description: 'Automated quality checks for customer data', workspace_id: '1', project_type: 'data_quality', priority: 'high', status: 'in_progress', progress: 75 },
    { id: '2', name: 'Sales Analytics Dashboard', description: 'Real-time sales performance monitoring', workspace_id: '3', project_type: 'analytics', priority: 'medium', status: 'completed', progress: 100 },
    { id: '3', name: 'ML Model Training Pipeline', description: 'Automated machine learning model training', workspace_id: '1', project_type: 'ml_pipeline', priority: 'critical', status: 'planning', progress: 15 }
  ]);

  // Scheduler state
  const [scheduledTasks, setScheduledTasks] = useState([
    { 
      id: '1', 
      name: 'Daily Quality Check', 
      description: 'Automated daily data quality validation',
      frequency: 'daily', 
      time: '09:00', 
      day: 'monday',
      status: 'active',
      lastRun: '2024-01-15 09:00',
      nextRun: '2024-01-16 09:00',
      workspace: 'Data Science Lab',
      project: 'Customer Data Quality Pipeline'
    },
    { 
      id: '2', 
      name: 'Weekly Report Generation', 
      description: 'Generate weekly data quality reports',
      frequency: 'weekly', 
      time: '08:00', 
      day: 'monday',
      status: 'active',
      lastRun: '2024-01-15 08:00',
      nextRun: '2024-01-22 08:00',
      workspace: 'Analytics Center',
      project: 'Sales Analytics Dashboard'
    },
    { 
      id: '3', 
      name: 'Monthly Data Cleanup', 
      description: 'Monthly data archiving and cleanup',
      frequency: 'monthly', 
      time: '06:00', 
      day: '1st',
      status: 'paused',
      lastRun: '2024-01-01 06:00',
      nextRun: '2024-02-01 06:00',
      workspace: 'Engineering Hub',
      project: 'ML Model Training Pipeline'
    }
  ]);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [showEditTaskModal, setShowEditTaskModal] = useState(false);
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    frequency: 'daily',
    time: '09:00',
    day: 'monday',
    workspace: '',
    project: ''
  });
  const [editingTask, setEditingTask] = useState<any>(null);

  // Business Rules state
  const [businessRules, setBusinessRules] = useState([
    {
      id: '1',
      name: 'Email Format Validation',
      type: 'data_validation',
      description: 'Ensures email addresses follow proper format',
      status: 'active',
      conditions: {
        field: 'email',
        operator: 'regex',
        value: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
        severity: 'error'
      },
      created_at: '2024-01-15',
      updated_at: '2024-01-15',
      applied_count: 1247
    },
    {
      id: '2',
      name: 'Age Range Check',
      type: 'business_logic',
      description: 'Age must be between 18 and 100',
      status: 'active',
      conditions: {
        field: 'age',
        operator: 'range',
        min_value: 18,
        max_value: 100,
        severity: 'warning'
      },
      created_at: '2024-01-14',
      updated_at: '2024-01-14',
      applied_count: 892
    },
    {
      id: '3',
      name: 'Data Completeness',
      type: 'quality_threshold',
      description: 'Required fields must be 95% complete',
      status: 'active',
      conditions: {
        field: 'required_fields',
        operator: 'completeness',
        threshold: 0.95,
        severity: 'error'
      },
      created_at: '2024-01-13',
      updated_at: '2024-01-13',
      applied_count: 2156
    },
    {
      id: '4',
      name: 'Phone Number Format',
      type: 'data_validation',
      description: 'Phone numbers must be in international format',
      status: 'paused',
      conditions: {
        field: 'phone',
        operator: 'regex',
        value: '^\\+[1-9]\\d{1,14}$',
        severity: 'warning'
      },
      created_at: '2024-01-12',
      updated_at: '2024-01-12',
      applied_count: 567
    }
  ]);
  const [showCreateRuleModal, setShowCreateRuleModal] = useState(false);
  const [showEditRuleModal, setShowEditRuleModal] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    type: 'data_validation',
    description: '',
    field: '',
    operator: 'regex',
    value: '',
    min_value: '',
    max_value: '',
    threshold: '',
    severity: 'error'
  });
  const [editingRule, setEditingRule] = useState<any>(null);

  // Monitoring state
  const [monitoringData, setMonitoringData] = useState({
    systemHealth: {
      status: 'healthy',
      uptime: '99.8%',
      lastCheck: new Date().toISOString(),
      cpu: 23,
      memory: 45,
      disk: 12,
      network: 67
    },
    qualityMetrics: {
      totalChecks: 1247,
      passedChecks: 1189,
      failedChecks: 58,
      successRate: 95.3,
      avgResponseTime: 2.3,
      lastHourChecks: 23
    },
    alerts: [
      {
        id: '1',
        type: 'warning',
        message: 'Data quality score dropped below threshold',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        severity: 'medium',
        acknowledged: false
      },
      {
        id: '2',
        type: 'error',
        message: 'Database connection timeout',
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        severity: 'high',
        acknowledged: false
      },
      {
        id: '3',
        type: 'info',
        message: 'Scheduled task completed successfully',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        severity: 'low',
        acknowledged: true
      }
    ],
    integrations: {
      grafana: { status: 'connected', url: 'http://localhost:3000', lastSync: new Date().toISOString() },
      prometheus: { status: 'connected', url: 'http://localhost:9090', lastSync: new Date().toISOString() },
      elasticsearch: { status: 'disconnected', url: 'http://localhost:9200', lastSync: null },
      datadog: { status: 'connected', url: 'https://app.datadoghq.com', lastSync: new Date().toISOString() }
    }
  });

  // Load data from localStorage on component mount
  useEffect(() => {
    const savedQualityResults = localStorage.getItem('qualityResults');
    const savedQualityRules = localStorage.getItem('qualityRules');
    const savedWorkspaces = localStorage.getItem('workspaces');
    const savedProjects = localStorage.getItem('projects');
    
    if (savedQualityResults) {
      setQualityResults(JSON.parse(savedQualityResults));
    }
    if (savedQualityRules) {
      setQualityRules(JSON.parse(savedQualityRules));
    }
    if (savedWorkspaces) {
      setWorkspaces(JSON.parse(savedWorkspaces));
    }
    if (savedProjects) {
      setProjects(JSON.parse(savedProjects));
    }
    
    const savedScheduledTasks = localStorage.getItem('scheduledTasks');
    if (savedScheduledTasks) {
      setScheduledTasks(JSON.parse(savedScheduledTasks));
    }
    
    const savedBusinessRules = localStorage.getItem('businessRules');
    if (savedBusinessRules) {
      setBusinessRules(JSON.parse(savedBusinessRules));
    }
  }, []);

  // Save data to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('qualityResults', JSON.stringify(qualityResults));
  }, [qualityResults]);

  useEffect(() => {
    localStorage.setItem('qualityRules', JSON.stringify(qualityRules));
  }, [qualityRules]);

  useEffect(() => {
    localStorage.setItem('workspaces', JSON.stringify(workspaces));
  }, [workspaces]);

  useEffect(() => {
    localStorage.setItem('projects', JSON.stringify(projects));
  }, [projects]);

  useEffect(() => {
    localStorage.setItem('scheduledTasks', JSON.stringify(scheduledTasks));
  }, [scheduledTasks]);

  useEffect(() => {
    localStorage.setItem('businessRules', JSON.stringify(businessRules));
  }, [businessRules]);

  // Simulate file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          // Simulate quality check results
          setTimeout(() => {
            setQualityResults([
              {
                id: '1',
                filename: 'user_data.csv',
                timestamp: '2024-08-27T10:00:00Z',
                overall_score: 95.2,
                status: 'passed',
                execution_time: 2.3,
                checks: [
                  {
                    name: 'Missing Values Analysis',
                    status: 'passed',
                    score: 0.95,
                    details: [
                      { metric: 'Missing Values (%)', value: '2%', threshold: '5%', status: 'passed' },
                      { metric: 'Missing Values (count)', value: 20, threshold: 50, status: 'passed' }
                    ]
                  },
                  {
                    name: 'Duplicate Detection',
                    status: 'warning',
                    score: 0.87,
                    details: [
                      { metric: 'Duplicate Rows (%)', value: '0.1%', threshold: '2%', status: 'passed' },
                      { metric: 'Duplicate Rows (count)', value: 1, threshold: 10, status: 'passed' }
                    ]
                  },
                  {
                    name: 'Outlier Detection',
                    status: 'passed',
                    score: 0.92,
                    details: [
                      { metric: 'Outliers (%)', value: '3%', threshold: '5%', status: 'passed' },
                      { metric: 'Outliers (count)', value: 30, threshold: 50, status: 'passed' }
                    ]
                  }
                ]
              },
              {
                id: '2',
                filename: 'sales_data.xlsx',
                timestamp: '2024-08-26T11:00:00Z',
                overall_score: 87.8,
                status: 'warning',
                execution_time: 1.8,
                checks: [
                  {
                    name: 'Missing Values Analysis',
                    status: 'failed',
                    score: 0.7,
                    details: [
                      { metric: 'Missing Values (%)', value: '8%', threshold: '5%', status: 'failed' },
                      { metric: 'Missing Values (count)', value: 160, threshold: 100, status: 'failed' }
                    ]
                  },
                  {
                    name: 'Duplicate Detection',
                    status: 'warning',
                    score: 0.9,
                    details: [
                      { metric: 'Duplicate Rows (%)', value: '2%', threshold: '2%', status: 'passed' },
                      { metric: 'Duplicate Rows (count)', value: 40, threshold: 50, status: 'passed' }
                    ]
                  },
                  {
                    name: 'Outlier Detection',
                    status: 'warning',
                    score: 0.8,
                    details: [
                      { metric: 'Outliers (%)', value: '12%', threshold: '5%', status: 'warning' },
                      { metric: 'Outliers (count)', value: 240, threshold: 200, status: 'warning' }
                    ]
                  }
                ]
              },
              {
                id: '3',
                filename: 'inventory.json',
                timestamp: '2024-08-25T12:00:00Z',
                overall_score: 92.1,
                status: 'passed',
                execution_time: 3.1,
                checks: [
                  {
                    name: 'Missing Values Analysis',
                    status: 'passed',
                    score: 0.98,
                    details: [
                      { metric: 'Missing Values (%)', value: '1%', threshold: '5%', status: 'passed' },
                      { metric: 'Missing Values (count)', value: 10, threshold: 50, status: 'passed' }
                    ]
                  },
                  {
                    name: 'Duplicate Detection',
                    status: 'passed',
                    score: 0.95,
                    details: [
                      { metric: 'Duplicate Rows (%)', value: '0.5%', threshold: '2%', status: 'passed' },
                      { metric: 'Duplicate Rows (count)', value: 5, threshold: 10, status: 'passed' }
                    ]
                  },
                  {
                    name: 'Outlier Detection',
                    status: 'passed',
                    score: 0.9,
                    details: [
                      { metric: 'Outliers (%)', value: '2%', threshold: '5%', status: 'passed' },
                      { metric: 'Outliers (count)', value: 20, threshold: 50, status: 'passed' }
                    ]
                  }
                ]
              },
              {
                id: '4',
                filename: 'customer_data.csv',
                timestamp: '2024-08-24T13:00:00Z',
                overall_score: 78.5,
                status: 'failed',
                execution_time: 1.5,
                checks: [
                  {
                    name: 'Missing Values Analysis',
                    status: 'failed',
                    score: 0.6,
                    details: [
                      { metric: 'Missing Values (%)', value: '15%', threshold: '5%', status: 'failed' },
                      { metric: 'Missing Values (count)', value: 75, threshold: 100, status: 'failed' }
                    ]
                  },
                  {
                    name: 'Duplicate Detection',
                    status: 'warning',
                    score: 0.7,
                    details: [
                      { metric: 'Duplicate Rows (%)', value: '8%', threshold: '2%', status: 'warning' },
                      { metric: 'Duplicate Rows (count)', value: 40, threshold: 50, status: 'warning' }
                    ]
                  },
                  {
                    name: 'Outlier Detection',
                    status: 'warning',
                    score: 0.5,
                    details: [
                      { metric: 'Outliers (%)', value: '25%', threshold: '5%', status: 'warning' },
                      { metric: 'Outliers (count)', value: 125, threshold: 200, status: 'warning' }
                    ]
                  }
                ]
              }
            ]);
          }, 1000);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  // Quality Check Functions
  const handleRunQualityCheck = () => {
    setShowQualityModal(true);
  };

  const handleConfigureRules = () => {
    setShowRulesModal(true);
  };

  const handleViewHistory = () => {
    setShowHistoryModal(true);
  };

  // Workspace Functions
  const handleCreateWorkspace = () => {
    if (newWorkspace.name && newWorkspace.team) {
      const workspace = {
        id: Date.now().toString(),
        name: newWorkspace.name,
        team: newWorkspace.team,
        description: newWorkspace.description,
        members: 1,
        projects: 0
      };
      setWorkspaces(prev => [...prev, workspace]);
      setNewWorkspace({ name: '', team: '', description: '' });
      setShowCreateWorkspaceModal(false);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Workspace "${workspace.name}" created successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleEditWorkspace = (workspace: any) => {
    setEditingWorkspace(workspace);
    setShowEditWorkspaceModal(true);
  };

  const handleUpdateWorkspace = () => {
    if (editingWorkspace && editingWorkspace.name && editingWorkspace.team) {
      setWorkspaces((prev: any[]) => prev.map(w => 
        w.id === editingWorkspace.id ? editingWorkspace : w
      ));
      setShowEditWorkspaceModal(false);
      setEditingWorkspace(null);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Workspace "${editingWorkspace.name}" updated successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleAddMember = (workspace: any) => {
    setSelectedWorkspace(workspace);
    setShowAddMemberModal(true);
  };

  const handleAddMemberSubmit = () => {
    if (newMember.email && selectedWorkspace) {
      setWorkspaces((prev: any[]) => prev.map(w => 
        w.id === selectedWorkspace.id 
          ? { ...w, members: w.members + 1 }
          : w
      ));
      setNewMember({ email: '', role: 'member' });
      setShowAddMemberModal(false);
      setSelectedWorkspace(null);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Member ${newMember.email} added to ${selectedWorkspace.name}!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleManageProjects = (workspace: any) => {
    setSelectedWorkspace(workspace);
    setShowManageProjectsModal(true);
  };

  const handleCreateProject = () => {
    if (newProject.name && selectedWorkspace) {
      const project = {
        id: Date.now().toString(),
        name: newProject.name,
        description: newProject.description,
        workspace_id: selectedWorkspace.id,
        project_type: newProject.project_type,
        priority: newProject.priority,
        status: 'planning',
        progress: 0
      };
      setProjects((prev: any[]) => [...prev, project]);
      
      // Update workspace project count
      setWorkspaces((prev: any[]) => prev.map(w => 
        w.id === selectedWorkspace.id 
          ? { ...w, projects: w.projects + 1 }
          : w
      ));
      
      setNewProject({ name: '', description: '', project_type: 'data_quality', priority: 'medium' });
      setShowManageProjectsModal(false);
      setSelectedWorkspace(null);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Project "${project.name}" created successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleDeleteWorkspace = (workspaceId: string) => {
    setWorkspaces(prev => prev.filter(w => w.id !== workspaceId));
  };

  // Scheduler Functions
  const handleCreateTask = () => {
    if (newTask.name && newTask.workspace) {
      const task = {
        id: Date.now().toString(),
        name: newTask.name,
        description: newTask.description,
        frequency: newTask.frequency,
        time: newTask.time,
        day: newTask.day,
        status: 'active',
        lastRun: 'Never',
        nextRun: calculateNextRun(newTask.frequency, newTask.time, newTask.day),
        workspace: newTask.workspace,
        project: newTask.project
      };
      
      setScheduledTasks(prev => [...prev, task]);
      setNewTask({
        name: '',
        description: '',
        frequency: 'daily',
        time: '09:00',
        day: 'monday',
        workspace: '',
        project: ''
      });
      setShowCreateTaskModal(false);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Task "${task.name}" scheduled successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleEditTask = (task: any) => {
    setEditingTask(task);
    setShowEditTaskModal(true);
  };

  const handleUpdateTask = () => {
    if (editingTask && editingTask.name && editingTask.workspace) {
      setScheduledTasks(prev => prev.map(t => 
        t.id === editingTask.id ? editingTask : t
      ));
      setShowEditTaskModal(false);
      setEditingTask(null);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Task "${editingTask.name}" updated successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleDeleteTask = (taskId: string) => {
    setScheduledTasks(prev => prev.filter(t => t.id !== taskId));
  };

  const handleToggleTaskStatus = (taskId: string) => {
    setScheduledTasks(prev => prev.map(t => 
      t.id === taskId 
        ? { ...t, status: t.status === 'active' ? 'paused' : 'active' }
        : t
    ));
  };

  const handleRunTaskNow = (taskId: string) => {
    // Simulate running the task
    setScheduledTasks(prev => prev.map(t => 
      t.id === taskId 
        ? { 
            ...t, 
            lastRun: new Date().toLocaleString(),
            nextRun: calculateNextRun(t.frequency, t.time, t.day)
          }
        : t
    ));
    
    // Show success notification
    const task = scheduledTasks.find(t => t.id === taskId);
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.innerHTML = `
      <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <span>Task "${task?.name}" executed successfully!</span>
      </div>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  };

  const calculateNextRun = (frequency: string, time: string, day: string) => {
    const now = new Date();
    const [hours, minutes] = time.split(':').map(Number);
    
    switch (frequency) {
      case 'daily':
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(hours, minutes, 0, 0);
        return tomorrow.toLocaleString();
      case 'weekly':
        const nextWeek = new Date(now);
        const daysUntilNext = (7 + getDayNumber(day) - now.getDay()) % 7;
        nextWeek.setDate(now.getDate() + daysUntilNext);
        nextWeek.setHours(hours, minutes, 0, 0);
        return nextWeek.toLocaleString();
      case 'monthly':
        const nextMonth = new Date(now);
        nextMonth.setMonth(nextMonth.getMonth() + 1);
        nextMonth.setDate(parseInt(day));
        nextMonth.setHours(hours, minutes, 0, 0);
        return nextMonth.toLocaleString();
      default:
        return 'Unknown';
    }
  };

  const getDayNumber = (day: string) => {
    const days = { 'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6 };
    return days[day.toLowerCase() as keyof typeof days] || 0;
  };

  // Business Rules Functions
  const handleCreateRule = () => {
    if (newRule.name && newRule.field) {
      const rule = {
        id: Date.now().toString(),
        name: newRule.name,
        type: newRule.type,
        description: newRule.description,
        status: 'active',
        conditions: {
          field: newRule.field,
          operator: newRule.operator,
          value: newRule.value,
          min_value: newRule.min_value ? parseFloat(newRule.min_value) : undefined,
          max_value: newRule.max_value ? parseFloat(newRule.max_value) : undefined,
          threshold: newRule.threshold ? parseFloat(newRule.threshold) : undefined,
          severity: newRule.severity
        },
        created_at: new Date().toISOString().split('T')[0],
        updated_at: new Date().toISOString().split('T')[0],
        applied_count: 0
      };
      
      setBusinessRules((prev: any[]) => [...prev, rule]);
      setNewRule({
        name: '',
        type: 'data_validation',
        description: '',
        field: '',
        operator: 'regex',
        value: '',
        min_value: '',
        max_value: '',
        threshold: '',
        severity: 'error'
      });
      setShowCreateRuleModal(false);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Business rule "${rule.name}" created successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleEditRule = (rule: any) => {
    setEditingRule(rule);
    setShowEditRuleModal(true);
  };

  const handleUpdateRule = () => {
    if (editingRule && editingRule.name && editingRule.field) {
      setBusinessRules((prev: any[]) => prev.map(r => 
        r.id === editingRule.id ? editingRule : r
      ));
      setShowEditRuleModal(false);
      setEditingRule(null);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Business rule "${editingRule.name}" updated successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }
  };

  const handleDeleteRule = (ruleId: string) => {
    setBusinessRules((prev: any[]) => prev.filter(r => r.id !== ruleId));
  };

  const handleToggleRuleStatus = (ruleId: string) => {
    setBusinessRules((prev: any[]) => prev.map(r => 
      r.id === ruleId 
        ? { ...r, status: r.status === 'active' ? 'paused' : 'active' }
        : r
    ));
  };

  const handleTestRule = (rule: any) => {
    // Simulate testing the rule
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.innerHTML = `
      <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
        </svg>
        <span>Testing rule "${rule.name}" with sample data...</span>
      </div>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
      
      // Show test results
      const resultNotification = document.createElement('div');
      resultNotification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Rule "${rule.name}" passed all test cases!</span>
        </div>
      `;
      document.body.appendChild(resultNotification);
      
      setTimeout(() => {
        if (resultNotification.parentNode) {
          resultNotification.parentNode.removeChild(resultNotification);
        }
      }, 3000);
    }, 2000);
  };

  // Monitoring Functions
  const handleAcknowledgeAlert = (alertId: string) => {
    setMonitoringData(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    }));
  };

  const handleRefreshMetrics = () => {
    // Simulate refreshing metrics
    setMonitoringData(prev => ({
      ...prev,
      systemHealth: {
        ...prev.systemHealth,
        lastCheck: new Date().toISOString(),
        cpu: Math.floor(Math.random() * 30) + 15,
        memory: Math.floor(Math.random() * 30) + 30,
        disk: Math.floor(Math.random() * 20) + 5,
        network: Math.floor(Math.random() * 40) + 40
      },
      qualityMetrics: {
        ...prev.qualityMetrics,
        lastHourChecks: Math.floor(Math.random() * 50) + 10
      }
    }));
  };

  const handleTestIntegration = (integrationName: string) => {
    const integration = monitoringData.integrations[integrationName as keyof typeof monitoringData.integrations];
    if (integration.status === 'connected') {
      // Simulate testing connection
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Testing ${integrationName} connection...</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
        
        // Show success
        const successNotification = document.createElement('div');
        successNotification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        successNotification.innerHTML = `
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>${integrationName} connection successful!</span>
        </div>
      `;
        document.body.appendChild(successNotification);
        
        setTimeout(() => {
          if (successNotification.parentNode) {
            successNotification.parentNode.removeChild(successNotification);
          }
        }, 3000);
      }, 1500);
    }
  };

  const runQualityCheck = async () => {
    if (!selectedFile || checkTypes.length === 0) {
      alert('Please select a file and at least one check type');
      return;
    }

    setIsRunningCheck(true);
    setShowQualityModal(false);

    // Simulate quality check processing
    setTimeout(() => {
      // Generate realistic quality check results based on configured rules
      const checks: {
        name: string;
        status: 'passed' | 'failed' | 'warning';
        score: number;
        details: {
          metric: string;
          value: string | number;
          threshold: string | number;
          status: 'passed' | 'failed' | 'warning';
        }[];
      }[] = checkTypes.map(checkType => {
        let checkResult: {
          name: string;
          status: 'passed' | 'failed' | 'warning';
          score: number;
          details: {
            metric: string;
            value: string | number;
            threshold: string | number;
            status: 'passed' | 'failed' | 'warning';
          }[];
        };
        
        switch (checkType) {
          case 'Missing Values':
            const missingPercent = Math.random() * 10; // 0-10%
            const missingStatus: 'passed' | 'failed' = missingPercent <= qualityRules.missingValuesThreshold ? 'passed' : 'failed';
            checkResult = {
              name: 'Missing Values Analysis',
              status: missingStatus,
              score: Math.max(0, 1 - (missingPercent / 100)),
              details: [
                { 
                  metric: 'Missing Values (%)', 
                  value: `${missingPercent.toFixed(1)}%`, 
                  threshold: `${qualityRules.missingValuesThreshold}%`, 
                  status: missingStatus 
                },
                { 
                  metric: 'Missing Values (count)', 
                  value: Math.round(missingPercent * 10), 
                  threshold: Math.round(qualityRules.missingValuesThreshold * 10), 
                  status: missingStatus 
                },
                                 { 
                   metric: 'Columns with Missing Data', 
                   value: Math.round(Math.random() * 3) + 1, 
                   threshold: 2, 
                   status: missingPercent <= qualityRules.missingValuesThreshold ? 'passed' : 'failed'
                 }
              ]
            };
            break;
            
          case 'Duplicates':
            const duplicatePercent = Math.random() * 5; // 0-5%
            const duplicateStatus: 'passed' | 'warning' = duplicatePercent <= qualityRules.duplicateTolerance ? 'passed' : 'warning';
            checkResult = {
              name: 'Duplicate Detection',
              status: duplicateStatus,
              score: Math.max(0, 1 - (duplicatePercent / 100)),
              details: [
                { 
                  metric: 'Duplicate Rows (%)', 
                  value: `${duplicatePercent.toFixed(1)}%`, 
                  threshold: `${qualityRules.duplicateTolerance}%`, 
                  status: duplicateStatus 
                },
                { 
                  metric: 'Duplicate Rows (count)', 
                  value: Math.round(duplicatePercent * 20), 
                  threshold: Math.round(qualityRules.duplicateTolerance * 20), 
                  status: duplicateStatus 
                },
                { 
                  metric: 'Potential Duplicate Keys', 
                  value: Math.round(Math.random() * 5), 
                  threshold: 3, 
                  status: duplicatePercent <= qualityRules.duplicateTolerance ? 'passed' : 'warning'
                }
              ]
            };
            break;
            
          case 'Outliers':
            const outlierPercent = Math.random() * 15; // 0-15%
            const outlierStatus: 'passed' | 'warning' | 'failed' = outlierPercent <= 5 ? 'passed' : outlierPercent <= 10 ? 'warning' : 'failed';
            checkResult = {
              name: 'Outlier Detection',
              status: outlierStatus,
              score: Math.max(0, 1 - (outlierPercent / 100)),
              details: [
                { 
                  metric: 'Outliers (%)', 
                  value: `${outlierPercent.toFixed(1)}%`, 
                  threshold: '5%', 
                  status: outlierPercent <= 5 ? 'passed' : 'warning'
                },
                { 
                  metric: 'Outliers (count)', 
                  value: Math.round(outlierPercent * 20), 
                  threshold: 100, 
                  status: outlierPercent <= 5 ? 'passed' : 'warning'
                },
                { 
                  metric: 'Detection Method', 
                  value: qualityRules.outlierDetectionMethod, 
                  threshold: 'IQR', 
                  status: 'passed'
                },
                { 
                  metric: 'High-Value Outliers', 
                  value: Math.round(Math.random() * 10), 
                  threshold: 5, 
                  status: outlierPercent <= 10 ? 'passed' : 'warning'
                }
              ]
            };
            break;
            
          case 'Data Types':
            const dataTypeScore = 0.85 + Math.random() * 0.15; // 85-100%
            const dataTypeStatus: 'passed' | 'warning' = dataTypeScore >= 0.9 ? 'passed' : 'warning';
            checkResult = {
              name: 'Data Type Validation',
              status: dataTypeStatus,
              score: dataTypeScore,
              details: [
                { 
                  metric: 'Correct Data Types (%)', 
                  value: `${(dataTypeScore * 100).toFixed(1)}%`, 
                  threshold: '90%', 
                  status: dataTypeStatus 
                },
                { 
                  metric: 'Type Mismatches', 
                  value: Math.round((1 - dataTypeScore) * 20), 
                  threshold: 2, 
                  status: dataTypeScore >= 0.9 ? 'passed' : 'warning'
                },
                { 
                  metric: 'Date Format Issues', 
                  value: qualityRules.dateValidation ? Math.round(Math.random() * 3) : 0, 
                  threshold: 2, 
                  status: qualityRules.dateValidation ? 'passed' : 'failed'
                },
                { 
                  metric: 'Numeric Format Issues', 
                  value: Math.round(Math.random() * 2), 
                  threshold: 1, 
                  status: 'passed'
                }
              ]
            };
            break;
            
          case 'Range Validation':
            const rangeScore = 0.8 + Math.random() * 0.2; // 80-100%
            const rangeStatus: 'passed' | 'warning' = rangeScore >= 0.85 ? 'passed' : 'warning';
            checkResult = {
              name: 'Range Validation',
              status: rangeStatus,
              score: rangeScore,
              details: [
                { 
                  metric: 'Values in Range (%)', 
                  value: `${(rangeScore * 100).toFixed(1)}%`, 
                  threshold: '85%', 
                  status: rangeStatus 
                },
                { 
                  metric: 'Out of Range Values', 
                  value: Math.round((1 - rangeScore) * 50), 
                  threshold: 10, 
                  status: rangeScore >= 0.85 ? 'passed' : 'warning'
                },
                { 
                  metric: 'Age Range Violations', 
                  value: Math.round(Math.random() * 8), 
                  threshold: 5, 
                  status: rangeScore >= 0.85 ? 'passed' : 'warning'
                },
                { 
                  metric: 'Salary Range Violations', 
                  value: Math.round(Math.random() * 5), 
                  threshold: 3, 
                  status: rangeScore >= 0.85 ? 'passed' : 'passed'
                }
              ]
            };
            break;
            
          default:
            checkResult = {
              name: `${checkType} Analysis`,
              status: 'passed',
              score: 0.9 + Math.random() * 0.1,
              details: [
                { metric: 'General Score', value: `${(0.9 + Math.random() * 0.1) * 100}%`, threshold: '85%', status: 'passed' },
                { metric: 'Issues Found', value: Math.round(Math.random() * 3), threshold: 2, status: 'passed' }
              ]
            };
        }
        
        return checkResult;
      });

      // Calculate overall score based on individual check scores
      const overallScore = checks.reduce((sum, check) => sum + check.score, 0) / checks.length * 100;
      const overallStatus: 'passed' | 'warning' | 'failed' = overallScore >= 90 ? 'passed' : overallScore >= 75 ? 'warning' : 'failed';

      const newResults: QualityCheckResult[] = [
        {
          id: Date.now().toString(),
          filename: selectedFile.name,
          timestamp: new Date().toISOString(),
          overall_score: Math.round(overallScore * 10) / 10,
          status: overallStatus,
          execution_time: 1.8 + Math.random() * 1,
          checks: checks
        }
      ];
      
      setQualityResults(prev => [...newResults, ...prev]);
      setIsRunningCheck(false);
      setSelectedFile(null);
      setCheckTypes([]);
      
      // Show success notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      notification.innerHTML = `
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
          </svg>
          <span>Quality check completed successfully!</span>
        </div>
      `;
      document.body.appendChild(notification);
      
      // Remove notification after 3 seconds
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 3000);
    }, 3000);
  };

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
    { id: 'quality', name: 'Quality Checks', icon: CheckCircle },
    { id: 'workspaces', name: 'Workspaces', icon: Users },
    { id: 'scheduler', name: 'Scheduler', icon: Clock },
    { id: 'rules', name: 'Business Rules', icon: Shield },
    { id: 'monitoring', name: 'Monitoring', icon: Activity },
    { id: 'analytics', name: 'Analytics', icon: TrendingUp },
    { id: 'connectors', name: 'Connectors', icon: Database },
    { id: 'settings', name: 'Settings', icon: Settings }
  ];

  const features = [
    {
      title: 'Advanced Quality Checks',
      description: 'Statistical analysis, pattern recognition, and ML-based scoring',
      icon: CheckCircle,
      color: 'from-green-500 to-emerald-500'
    },
    {
      title: 'Multi-Format Support',
      description: 'CSV, JSON, Excel, Parquet, and database connectors',
      icon: FileText,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: 'Big Data Processing',
      description: 'Spark and Dask integration for massive datasets',
      icon: Zap,
      color: 'from-purple-500 to-pink-500'
    },
    {
      title: 'Real-time Monitoring',
      description: 'Live quality metrics and performance tracking',
      icon: Activity,
      color: 'from-orange-500 to-red-500'
    },
    {
      title: 'Team Collaboration',
      description: 'Shared workspaces and resource management',
      icon: Users,
      color: 'from-indigo-500 to-purple-500'
    },
    {
      title: 'Cloud Integration',
      description: 'AWS S3, Azure Blob, and Google Cloud Storage',
      icon: Cloud,
      color: 'from-teal-500 to-blue-500'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-blue-800">
      {/* Header */}
      <motion.header 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-card m-4 p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center"
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold gradient-text">Algorzen DQT</h1>
              <p className="text-blue-200">Enterprise Data Quality Toolkit</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-green-400">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>System Healthy</span>
            </div>
            <button className="btn-secondary">
              <Users className="w-5 h-5 mr-2" />
              Admin
            </button>
          </div>
        </div>
      </motion.header>

      <div className="flex gap-4 mx-4 mb-4">
        {/* Sidebar */}
        <motion.aside 
          initial={{ x: -200, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="w-64 space-y-2"
        >
          {tabs.map((tab, index) => (
            <motion.button
              key={tab.id}
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 p-4 rounded-lg transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg'
                  : 'glass-card text-blue-200 hover:bg-white/10'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span className="font-medium">{tab.name}</span>
            </motion.button>
          ))}
        </motion.aside>

        {/* Main Content */}
        <motion.main 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 space-y-6"
        >
          {activeTab === 'dashboard' && (
            <DashboardContent 
              stats={stats}
              features={features}
              qualityResults={qualityResults}
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
            />
          )}
          
          {activeTab === 'quality' && (
            <QualityChecksContent 
              qualityResults={qualityResults}
              onRunCheck={handleRunQualityCheck}
              onConfigureRules={handleConfigureRules}
              onViewHistory={handleViewHistory}
              isRunningCheck={isRunningCheck}
            />
          )}
          
          {activeTab === 'workspaces' && (
            <WorkspacesContent 
              workspaces={workspaces}
              onCreateWorkspace={() => setShowCreateWorkspaceModal(true)}
              onDeleteWorkspace={handleDeleteWorkspace}
              onEditWorkspace={handleEditWorkspace}
              onAddMember={handleAddMember}
              onManageProjects={handleManageProjects}
            />
          )}
          
          {activeTab === 'scheduler' && (
            <SchedulerContent 
              scheduledTasks={scheduledTasks}
              onCreateTask={() => setShowCreateTaskModal(true)}
              onEditTask={handleEditTask}
              onDeleteTask={handleDeleteTask}
              onToggleStatus={handleToggleTaskStatus}
              onRunNow={handleRunTaskNow}
            />
          )}
          
          {activeTab === 'rules' && (
            <BusinessRulesContent 
              businessRules={businessRules}
              onCreateRule={() => setShowCreateRuleModal(true)}
              onEditRule={handleEditRule}
              onDeleteRule={handleDeleteRule}
              onToggleStatus={handleToggleRuleStatus}
              onTestRule={handleTestRule}
            />
          )}
          
          {activeTab === 'monitoring' && (
            <MonitoringContent 
              monitoringData={monitoringData}
              onAcknowledgeAlert={handleAcknowledgeAlert}
              onRefreshMetrics={handleRefreshMetrics}
              onTestIntegration={handleTestIntegration}
            />
          )}
          
          {activeTab === 'analytics' && (
            <AnalyticsContent />
          )}
          
          {activeTab === 'connectors' && (
            <ConnectorsContent />
          )}
          
          {activeTab === 'settings' && (
            <SettingsContent />
          )}
        </motion.main>
      </div>

      {/* Quality Check Modal */}
      <AnimatePresence>
        {showQualityModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowQualityModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Run Quality Check</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Select File</label>
                  <input
                    type="file"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    accept=".csv,.json,.xlsx,.xls"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Check Types</label>
                  <div className="space-y-2">
                    {['Missing Values', 'Duplicates', 'Outliers', 'Data Types', 'Range Validation'].map((type) => (
                      <label key={type} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={checkTypes.includes(type)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCheckTypes([...checkTypes, type]);
                            } else {
                              setCheckTypes(checkTypes.filter(t => t !== type));
                            }
                          }}
                          className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                        />
                        <span className="text-blue-200">{type}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowQualityModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={runQualityCheck}
                  disabled={!selectedFile || checkTypes.length === 0}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Run Check
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rules Configuration Modal */}
      <AnimatePresence>
        {showRulesModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowRulesModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Configure Quality Rules</h3>
              
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Missing Values Threshold (%)</label>
                    <input
                      type="number"
                      value={qualityRules.missingValuesThreshold}
                      onChange={(e) => setQualityRules(prev => ({
                        ...prev,
                        missingValuesThreshold: parseInt(e.target.value) || 5
                      }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Duplicate Tolerance (%)</label>
                    <input
                      type="number"
                      value={qualityRules.duplicateTolerance}
                      onChange={(e) => setQualityRules(prev => ({
                        ...prev,
                        duplicateTolerance: parseInt(e.target.value) || 2
                      }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Outlier Detection Method</label>
                  <select 
                    value={qualityRules.outlierDetectionMethod}
                    onChange={(e) => setQualityRules(prev => ({
                      ...prev,
                      outlierDetectionMethod: e.target.value
                    }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="IQR">IQR Method</option>
                    <option value="Z-Score">Z-Score</option>
                    <option value="Isolation Forest">Isolation Forest</option>
                  </select>
                </div>

                <div>
                  <h4 className="text-lg font-bold text-white mb-3">Validation Rules</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={qualityRules.dataTypeValidation}
                        onChange={(e) => setQualityRules(prev => ({
                          ...prev,
                          dataTypeValidation: e.target.checked
                        }))}
                        className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-blue-200">Data Type Validation</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={qualityRules.rangeValidation}
                        onChange={(e) => setQualityRules(prev => ({
                          ...prev,
                          rangeValidation: e.target.checked
                        }))}
                        className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-blue-200">Range Validation</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={qualityRules.emailValidation}
                        onChange={(e) => setQualityRules(prev => ({
                          ...prev,
                          emailValidation: e.target.checked
                        }))}
                        className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-blue-200">Email Validation</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={qualityRules.phoneValidation}
                        onChange={(e) => setQualityRules(prev => ({
                          ...prev,
                          phoneValidation: e.target.checked
                        }))}
                        className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-blue-200">Phone Validation</span>
                    </label>
                    <label className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={qualityRules.dateValidation}
                        onChange={(e) => setQualityRules(prev => ({
                          ...prev,
                          dateValidation: e.target.checked
                        }))}
                        className="rounded border-white/20 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-blue-200">Date Validation</span>
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowRulesModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Rules are already saved in state, just close modal
                    setShowRulesModal(false);
                    // Show success notification
                    const notification = document.createElement('div');
                    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
                    notification.innerHTML = `
                      <div class="flex items-center space-x-2">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                        <span>Quality rules updated successfully!</span>
                      </div>
                    `;
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {
                      if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                      }
                    }, 3000);
                  }}
                  className="btn-primary flex-1"
                >
                  Save Rules
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Workspace Modal */}
      <AnimatePresence>
        {showCreateWorkspaceModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCreateWorkspaceModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Create New Workspace</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Workspace Name</label>
                  <input
                    type="text"
                    value={newWorkspace.name}
                    onChange={(e) => setNewWorkspace(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter workspace name"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Team</label>
                  <select
                    value={newWorkspace.team}
                    onChange={(e) => setNewWorkspace(prev => ({ ...prev, team: e.target.value }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Team</option>
                    <option value="Data Science">Data Science</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Analytics">Analytics</option>
                    <option value="Product">Product</option>
                    <option value="Marketing">Marketing</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={newWorkspace.description}
                    onChange={(e) => setNewWorkspace(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the workspace purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateWorkspaceModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateWorkspace}
                  disabled={!newWorkspace.name || !newWorkspace.team}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Workspace
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Workspace Modal */}
      <AnimatePresence>
        {showEditWorkspaceModal && editingWorkspace && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowEditWorkspaceModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Edit Workspace</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Workspace Name</label>
                  <input
                    type="text"
                    value={editingWorkspace.name}
                    onChange={(e) => setEditingWorkspace((prev: any) => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter workspace name"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Team</label>
                  <select
                    value={editingWorkspace.team}
                    onChange={(e) => setEditingWorkspace((prev: any) => ({ ...prev, team: e.target.value }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Data Science">Data Science</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Analytics">Analytics</option>
                    <option value="Product">Product</option>
                    <option value="Marketing">Marketing</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={editingWorkspace.description || ''}
                    onChange={(e) => setEditingWorkspace((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the workspace purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowEditWorkspaceModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateWorkspace}
                  disabled={!editingWorkspace.name || !editingWorkspace.team}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Workspace
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Member Modal */}
      <AnimatePresence>
        {showAddMemberModal && selectedWorkspace && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowAddMemberModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Add Member to {selectedWorkspace.name}</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Email Address</label>
                  <input
                    type="email"
                    value={newMember.email}
                    onChange={(e) => setNewMember((prev: any) => ({ ...prev, email: e.target.value }))}
                    placeholder="Enter member email"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Role</label>
                  <select
                    value={newMember.role}
                    onChange={(e) => setNewMember((prev: any) => ({ ...prev, role: e.target.value }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowAddMemberModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddMemberSubmit}
                  disabled={!newMember.email}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add Member
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Manage Projects Modal */}
      <AnimatePresence>
        {showManageProjectsModal && selectedWorkspace && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowManageProjectsModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Manage Projects - {selectedWorkspace.name}</h3>
              
              {/* Create New Project */}
              <div className="bg-white/5 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-bold text-white mb-4">Create New Project</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <input
                    type="text"
                    value={newProject.name}
                    onChange={(e) => setNewProject((prev: any) => ({ ...prev, name: e.target.value }))}
                    placeholder="Project name"
                    className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <select
                    value={newProject.project_type}
                    onChange={(e) => setNewProject((prev: any) => ({ ...prev, project_type: e.target.value }))}
                    className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="data_quality">Data Quality</option>
                    <option value="ml_pipeline">ML Pipeline</option>
                    <option value="analytics">Analytics</option>
                    <option value="etl">ETL</option>
                    <option value="reporting">Reporting</option>
                  </select>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <select
                    value={newProject.priority}
                    onChange={(e) => setNewProject((prev: any) => ({ ...prev, priority: e.target.value }))}
                    className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                  <textarea
                    value={newProject.description}
                    onChange={(e) => setNewProject((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Project description"
                    rows={2}
                    className="bg-white/10 border border-white/10 border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={handleCreateProject}
                  disabled={!newProject.name}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Project
                </button>
              </div>

              {/* Existing Projects */}
              <div>
                <h4 className="text-lg font-bold text-white mb-4">Existing Projects</h4>
                <div className="space-y-3">
                  {projects.filter(p => p.workspace_id === selectedWorkspace.id).map((project, index) => (
                    <motion.div
                      key={project.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center justify-between p-4 bg-white/5 rounded-lg"
                    >
                      <div>
                        <h5 className="text-white font-medium">{project.name}</h5>
                        <p className="text-blue-200 text-sm">{project.description}</p>
                        <div className="flex space-x-4 mt-2 text-sm">
                          <span className="text-blue-300">Type: {project.project_type}</span>
                          <span className="text-blue-300">Priority: {project.priority}</span>
                          <span className="text-blue-300">Status: {project.status}</span>
                          <span className="text-blue-300">Progress: {project.progress}%</span>
                        </div>
                      </div>
                      <div className="w-24 bg-white/10 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${project.progress}%` }}
                        ></div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
              
              <div className="mt-6 text-center">
                <button
                  onClick={() => setShowManageProjectsModal(false)}
                  className="btn-secondary"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Task Modal */}
      <AnimatePresence>
        {showCreateTaskModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCreateTaskModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Schedule New Task</h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Task Name</label>
                    <input
                      type="text"
                      value={newTask.name}
                      onChange={(e) => setNewTask((prev: any) => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter task name"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Frequency</label>
                    <select
                      value={newTask.frequency}
                      onChange={(e) => setNewTask((prev: any) => ({ ...prev, frequency: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Time</label>
                    <input
                      type="time"
                      value={newTask.time}
                      onChange={(e) => setNewTask((prev: any) => ({ ...prev, time: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Day</label>
                    {newTask.frequency === 'daily' ? (
                      <input
                        type="text"
                        value={newTask.day}
                        onChange={(e) => setNewTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        placeholder="Every day"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled
                      />
                    ) : newTask.frequency === 'weekly' ? (
                      <select
                        value={newTask.day}
                        onChange={(e) => setNewTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="monday">Monday</option>
                        <option value="tuesday">Tuesday</option>
                        <option value="wednesday">Wednesday</option>
                        <option value="thursday">Thursday</option>
                        <option value="friday">Friday</option>
                        <option value="saturday">Saturday</option>
                        <option value="sunday">Sunday</option>
                      </select>
                    ) : (
                      <select
                        value={newTask.day}
                        onChange={(e) => setNewTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="1st">1st</option>
                        <option value="2nd">2nd</option>
                        <option value="3rd">3rd</option>
                        <option value="4th">4th</option>
                        <option value="5th">5th</option>
                        <option value="6th">6th</option>
                        <option value="7th">7th</option>
                        <option value="8th">8th</option>
                        <option value="9th">9th</option>
                        <option value="10th">10th</option>
                        <option value="15th">15th</option>
                        <option value="20th">20th</option>
                        <option value="25th">25th</option>
                        <option value="30th">30th</option>
                      </select>
                    )}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Workspace</label>
                    <select
                      value={newTask.workspace}
                      onChange={(e) => setNewTask((prev: any) => ({ ...prev, workspace: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Workspace</option>
                      {workspaces.map(workspace => (
                        <option key={workspace.id} value={workspace.name}>{workspace.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Project</label>
                    <select
                      value={newTask.project}
                      onChange={(e) => setNewTask((prev: any) => ({ ...prev, project: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Project</option>
                      {projects.map(project => (
                        <option key={project.id} value={project.name}>{project.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the task purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateTaskModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTask}
                  disabled={!newTask.name || !newTask.workspace}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Schedule Task
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Task Modal */}
      <AnimatePresence>
        {showEditTaskModal && editingTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowEditTaskModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Edit Task</h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Task Name</label>
                    <input
                      type="text"
                      value={editingTask.name}
                      onChange={(e) => setEditingTask((prev: any) => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter task name"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Frequency</label>
                    <select
                      value={editingTask.frequency}
                      onChange={(e) => setEditingTask((prev: any) => ({ ...prev, frequency: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Time</label>
                    <input
                      type="time"
                      value={editingTask.time}
                      onChange={(e) => setEditingTask((prev: any) => ({ ...prev, time: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Day</label>
                    {editingTask.frequency === 'daily' ? (
                      <input
                        type="text"
                        value={editingTask.day}
                        onChange={(e) => setEditingTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        placeholder="Every day"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled
                      />
                    ) : editingTask.frequency === 'weekly' ? (
                      <select
                        value={editingTask.day}
                        onChange={(e) => setEditingTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="monday">Monday</option>
                        <option value="tuesday">Tuesday</option>
                        <option value="wednesday">Wednesday</option>
                        <option value="thursday">Thursday</option>
                        <option value="friday">Friday</option>
                        <option value="saturday">Saturday</option>
                        <option value="sunday">Sunday</option>
                      </select>
                    ) : (
                      <select
                        value={editingTask.day}
                        onChange={(e) => setEditingTask((prev: any) => ({ ...prev, day: e.target.value }))}
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="1st">1st</option>
                        <option value="2nd">2nd</option>
                        <option value="3rd">3rd</option>
                        <option value="4th">4th</option>
                        <option value="5th">5th</option>
                        <option value="6th">6th</option>
                        <option value="7th">7th</option>
                        <option value="8th">8th</option>
                        <option value="9th">9th</option>
                        <option value="10th">10th</option>
                        <option value="15th">15th</option>
                        <option value="20th">20th</option>
                        <option value="25th">25th</option>
                        <option value="30th">30th</option>
                      </select>
                    )}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Workspace</label>
                    <select
                      value={editingTask.workspace}
                      onChange={(e) => setEditingTask((prev: any) => ({ ...prev, workspace: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Workspace</option>
                      {workspaces.map(workspace => (
                        <option key={workspace.id} value={workspace.name}>{workspace.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Project</label>
                    <select
                      value={editingTask.project}
                      onChange={(e) => setEditingTask((prev: any) => ({ ...prev, project: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Project</option>
                      {projects.map(project => (
                        <option key={project.id} value={project.name}>{project.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={editingTask.description}
                    onChange={(e) => setEditingTask((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the task purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowEditTaskModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateTask}
                  disabled={!editingTask.name || !editingTask.workspace}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Task
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Business Rule Modal */}
      <AnimatePresence>
        {showCreateRuleModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCreateRuleModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Create New Business Rule</h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Rule Name</label>
                    <input
                      type="text"
                      value={newRule.name}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter rule name"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Rule Type</label>
                    <select
                      value={newRule.type}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, type: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="data_validation">Data Validation</option>
                      <option value="business_logic">Business Logic</option>
                      <option value="quality_threshold">Quality Threshold</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={newRule.description}
                    onChange={(e) => setNewRule((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the rule purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Field Name</label>
                    <input
                      type="text"
                      value={newRule.field}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, field: e.target.value }))}
                      placeholder="e.g., email, age, phone"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Operator</label>
                    <select
                      value={newRule.operator}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, operator: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="regex">Regular Expression</option>
                      <option value="range">Range Check</option>
                      <option value="completeness">Completeness</option>
                      <option value="equals">Equals</option>
                      <option value="not_equals">Not Equals</option>
                      <option value="contains">Contains</option>
                      <option value="not_contains">Not Contains</option>
                    </select>
                  </div>
                </div>
                
                {newRule.operator === 'regex' && (
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Regular Expression</label>
                    <input
                      type="text"
                      value={newRule.value}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, value: e.target.value }))}
                      placeholder="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
                
                {newRule.operator === 'range' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Minimum Value</label>
                      <input
                        type="number"
                        value={newRule.min_value}
                        onChange={(e) => setNewRule((prev: any) => ({ ...prev, min_value: e.target.value }))}
                        placeholder="0"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Maximum Value</label>
                      <input
                        type="number"
                        value={newRule.max_value}
                        onChange={(e) => setNewRule((prev: any) => ({ ...prev, max_value: e.target.value }))}
                        placeholder="100"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}
                
                {newRule.operator === 'completeness' && (
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Threshold (%)</label>
                    <input
                      type="number"
                      value={newRule.threshold}
                      onChange={(e) => setNewRule((prev: any) => ({ ...prev, threshold: e.target.value }))}
                      placeholder="95"
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Severity</label>
                  <select
                    value={newRule.severity}
                    onChange={(e) => setNewRule((prev: any) => ({ ...prev, severity: e.target.value }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="error">Error</option>
                    <option value="warning">Warning</option>
                    <option value="info">Info</option>
                  </select>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateRuleModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateRule}
                  disabled={!newRule.name || !newRule.field}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Rule
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Business Rule Modal */}
      <AnimatePresence>
        {showEditRuleModal && editingRule && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowEditRuleModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Edit Business Rule</h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Rule Name</label>
                    <input
                      type="text"
                      value={editingRule.name}
                      onChange={(e) => setEditingRule((prev: any) => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter rule name"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Rule Type</label>
                    <select
                      value={editingRule.type}
                      onChange={(e) => setEditingRule((prev: any) => ({ ...prev, type: e.target.value }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="data_validation">Data Validation</option>
                      <option value="business_logic">Business Logic</option>
                      <option value="quality_threshold">Quality Threshold</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={editingRule.description}
                    onChange={(e) => setEditingRule((prev: any) => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the rule purpose"
                    rows={3}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Field Name</label>
                    <input
                      type="text"
                      value={editingRule.conditions.field}
                      onChange={(e) => setEditingRule((prev: any) => ({ 
                        ...prev, 
                        conditions: { ...prev.conditions, field: e.target.value }
                      }))}
                      placeholder="e.g., email, age, phone"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Operator</label>
                    <select
                      value={editingRule.conditions.operator}
                      onChange={(e) => setEditingRule((prev: any) => ({ 
                        ...prev, 
                        conditions: { ...prev.conditions, operator: e.target.value }
                      }))}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="regex">Regular Expression</option>
                      <option value="range">Range Check</option>
                      <option value="completeness">Completeness</option>
                      <option value="equals">Equals</option>
                      <option value="not_equals">Not Equals</option>
                      <option value="contains">Contains</option>
                      <option value="not_contains">Not Contains</option>
                    </select>
                  </div>
                </div>
                
                {editingRule.conditions.operator === 'regex' && (
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Regular Expression</label>
                    <input
                      type="text"
                      value={editingRule.conditions.value || ''}
                      onChange={(e) => setEditingRule((prev: any) => ({ 
                        ...prev, 
                        conditions: { ...prev.conditions, value: e.target.value }
                      }))}
                      placeholder="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
                
                {editingRule.conditions.operator === 'range' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Minimum Value</label>
                      <input
                        type="number"
                        value={editingRule.conditions.min_value || ''}
                        onChange={(e) => setEditingRule((prev: any) => ({ 
                          ...prev, 
                          conditions: { ...prev.conditions, min_value: parseFloat(e.target.value) || 0 }
                        }))}
                        placeholder="0"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-white text-sm font-medium mb-2">Maximum Value</label>
                      <input
                        type="number"
                        value={editingRule.conditions.max_value || ''}
                        onChange={(e) => setEditingRule((prev: any) => ({ 
                          ...prev, 
                          conditions: { ...prev.conditions, max_value: parseFloat(e.target.value) || 0 }
                        }))}
                        placeholder="100"
                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}
                
                {editingRule.conditions.operator === 'completeness' && (
                  <div>
                    <label className="block text-white text-sm font-medium mb-2">Threshold (%)</label>
                    <input
                      type="number"
                      value={editingRule.conditions.threshold || ''}
                      onChange={(e) => setEditingRule((prev: any) => ({ 
                        ...prev, 
                        conditions: { ...prev.conditions, threshold: parseFloat(e.target.value) || 0 }
                      }))}
                      placeholder="95"
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
                
                <div>
                  <label className="block text-white text-sm font-medium mb-2">Severity</label>
                  <select
                    value={editingRule.conditions.severity}
                    onChange={(e) => setEditingRule((prev: any) => ({ 
                      ...prev, 
                      conditions: { ...prev.conditions, severity: e.target.value }
                    }))}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="error">Error</option>
                    <option value="warning">Warning</option>
                    <option value="info">Info</option>
                  </select>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowEditRuleModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateRule}
                  disabled={!editingRule.name || !editingRule.conditions.field}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Rule
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* History Modal */}
      <AnimatePresence>
        {showHistoryModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowHistoryModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold gradient-text mb-6">Quality Check History</h3>
              
              <div className="space-y-4">
                {qualityResults.map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-white/5 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-4">
                        <div className="text-center">
                          <p className="text-blue-200 text-sm">{item.timestamp}</p>
                          <p className="text-white font-medium">{item.filename}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-white">{item.overall_score}%</p>
                          <p className="text-blue-200 text-sm">Score</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          item.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                          item.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {item.status}
                        </span>
                        <p className="text-blue-200 text-sm mt-1">Execution Time: {item.execution_time.toFixed(2)}s</p>
                      </div>
                    </div>
                    <div className="border-t border-white/10 pt-3">
                      <h4 className="text-lg font-bold text-white mb-2">Checks:</h4>
                      <div className="space-y-3">
                        {item.checks.map((check, checkIndex) => (
                          <div key={check.name} className="p-3 bg-white/5 rounded-lg">
                            <h5 className="text-lg font-bold text-white mb-1">{check.name}</h5>
                            <p className="text-blue-200 text-sm">Status: {check.status}</p>
                            <p className="text-blue-200 text-sm">Score: {(check.score * 100).toFixed(1)}%</p>
                            <h6 className="text-md font-medium text-white mt-2">Details:</h6>
                            <ul className="list-disc list-inside text-blue-300 text-sm">
                              {check.details.map((detail, detailIndex) => (
                                <li key={detail.metric}>
                                  {detail.metric}: {detail.value} (Threshold: {detail.threshold})
                                  <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                                    detail.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                                    detail.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-red-500/20 text-red-400'
                                  }`}>
                                    {detail.status}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                                             <p className="text-blue-300 text-sm mt-2">File processed successfully with {item.checks.length} quality checks.</p>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              <div className="mt-6 flex justify-center space-x-3">
                <button
                  onClick={() => {
                    alert('Exporting history to CSV...');
                  }}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Export CSV</span>
                </button>
                <button
                  onClick={() => setShowHistoryModal(false)}
                  className="btn-primary"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Dashboard Content Component
const DashboardContent: React.FC<{
  stats: DashboardStats;
  features: any[];
  qualityResults: QualityCheckResult[];
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  isUploading: boolean;
  uploadProgress: number;
}> = ({ stats, features, qualityResults, onFileUpload, isUploading, uploadProgress }) => {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Workspaces', value: stats.total_workspaces, icon: Users, color: 'from-blue-500 to-cyan-500' },
          { label: 'Active Tasks', value: stats.active_tasks, icon: Clock, color: 'from-green-500 to-emerald-500' },
          { label: 'Business Rules', value: stats.total_rules, icon: Shield, color: 'from-purple-500 to-pink-500' },
          { label: 'System Health', value: stats.system_health, icon: Activity, color: 'from-orange-500 to-red-500' }
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-6 card-hover"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 bg-gradient-to-r ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* File Upload Section */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8"
      >
        <div className="text-center">
          <h2 className="text-2xl font-bold gradient-text mb-4">Upload & Analyze Data</h2>
          <p className="text-blue-200 mb-6">Drag and drop your CSV, JSON, or Excel files for quality analysis</p>
          
          <div className="border-2 border-dashed border-blue-400/30 rounded-lg p-8 hover:border-blue-400/50 transition-colors">
            <input
              type="file"
              onChange={onFileUpload}
              accept=".csv,.json,.xlsx,.xls"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="w-16 h-16 mx-auto text-blue-400 mb-4" />
              <p className="text-blue-200">Click to upload or drag and drop</p>
              <p className="text-blue-300 text-sm">CSV, JSON, Excel files supported</p>
            </label>
          </div>

          {isUploading && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6"
            >
              <div className="w-full bg-blue-900/50 rounded-full h-2">
                <motion.div 
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-blue-200 mt-2">Uploading... {uploadProgress}%</p>
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Quality Results */}
      {qualityResults.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <h3 className="text-xl font-bold gradient-text mb-4">Quality Check Results</h3>
          <div className="space-y-4">
                      {qualityResults.map((result, index) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 bg-white/5 rounded-lg"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {result.status === 'passed' && <CheckCircle className="w-5 h-5 text-green-400" />}
                  {result.status === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
                  {result.status === 'failed' && <XCircle className="w-5 h-5 text-red-400" />}
                  <span className="text-white font-medium">{result.filename}</span>
                </div>
                <div className="text-right">
                  <p className="text-blue-200">Overall Score: {(result.overall_score).toFixed(1)}%</p>
                  <p className="text-blue-300 text-sm">Execution Time: {result.execution_time.toFixed(2)}s</p>
                </div>
              </div>
              <div className="border-t border-white/10 pt-3">
                <h4 className="text-lg font-bold text-white mb-2">Quality Checks:</h4>
                <div className="space-y-3">
                  {result.checks.map((check, checkIndex) => (
                    <div key={check.name} className="p-3 bg-white/5 rounded-lg">
                      <h5 className="text-lg font-bold text-white mb-1">{check.name}</h5>
                      <p className="text-blue-200 text-sm">Status: {check.status}</p>
                      <p className="text-blue-200 text-sm">Score: {(check.score * 100).toFixed(1)}%</p>
                      <h6 className="text-md font-medium text-white mt-2">Details:</h6>
                      <ul className="list-disc list-inside text-blue-300 text-sm">
                        {check.details.map((detail, detailIndex) => (
                          <li key={detail.metric}>
                            {detail.metric}: {detail.value} (Threshold: {detail.threshold})
                            <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                              detail.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                              detail.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-red-500/20 text-red-400'
                            }`}>
                              {detail.status}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
                <p className="text-blue-300 text-sm mt-2">File processed successfully with {result.checks.length} quality checks.</p>
              </div>
            </motion.div>
          ))}
          </div>
        </motion.div>
      )}

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-6 card-hover"
          >
            <div className={`w-12 h-12 bg-gradient-to-r ${feature.color} rounded-lg flex items-center justify-center mb-4`}>
              <feature.icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">{feature.title}</h3>
            <p className="text-blue-200 text-sm">{feature.description}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Placeholder components for other tabs
const QualityChecksContent: React.FC<{ 
  qualityResults: QualityCheckResult[];
  onRunCheck: () => void;
  onConfigureRules: () => void;
  onViewHistory: () => void;
  isRunningCheck: boolean;
}> = ({ qualityResults, onRunCheck, onConfigureRules, onViewHistory, isRunningCheck }) => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Quality Checks</h2>
      <p className="text-blue-200 mb-6">Advanced quality check management and configuration.</p>
      
      {/* Status Indicator */}
      {isRunningCheck && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-500/20 border border-blue-400/30 rounded-lg p-4 mb-6"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-blue-400 rounded-full animate-pulse"></div>
              <span className="text-blue-200 font-medium">Running Quality Check...</span>
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
            <div className="text-right">
              <p className="text-blue-200 text-sm">Processing...</p>
              <p className="text-blue-300 text-xs">This may take a few minutes</p>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button 
          onClick={onRunCheck}
          className="btn-primary flex items-center justify-center space-x-2"
          disabled={isRunningCheck}
        >
          <CheckCircle className="w-5 h-5" />
          <span>{isRunningCheck ? 'Running...' : 'Run New Check'}</span>
        </button>
        <button 
          onClick={onConfigureRules}
          className="btn-secondary flex items-center justify-center space-x-2"
          disabled={isRunningCheck}
        >
          <Settings className="w-5 h-5" />
          <span>Configure Rules</span>
        </button>
        <button 
          onClick={onViewHistory}
          className="btn-secondary flex items-center justify-center space-x-2"
          disabled={isRunningCheck}
        >
          <TrendingUp className="w-5 h-5" />
          <span>View History</span>
        </button>
      </div>

      {/* Quality Check Results */}
      {qualityResults.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-white">Recent Results</h3>
          {qualityResults.map((result, index) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 bg-white/5 rounded-lg"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {result.status === 'passed' && <CheckCircle className="w-5 h-5 text-green-400" />}
                  {result.status === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
                  {result.status === 'failed' && <XCircle className="w-5 h-5 text-red-400" />}
                  <span className="text-white font-medium">{result.filename}</span>
                </div>
                <div className="text-right">
                  <p className="text-blue-200">Overall Score: {(result.overall_score).toFixed(1)}%</p>
                  <p className="text-blue-300 text-sm">Execution Time: {result.execution_time.toFixed(2)}s</p>
                </div>
              </div>
              <div className="border-t border-white/10 pt-3">
                <h4 className="text-lg font-bold text-white mb-2">Quality Checks:</h4>
                <div className="space-y-3">
                  {result.checks.map((check, checkIndex) => (
                    <div key={check.name} className="p-3 bg-white/5 rounded-lg">
                      <h5 className="text-lg font-bold text-white mb-1">{check.name}</h5>
                      <p className="text-blue-200 text-sm">Status: {check.status}</p>
                      <p className="text-blue-200 text-sm">Score: {(check.score * 100).toFixed(1)}%</p>
                      <h6 className="text-md font-medium text-white mt-2">Details:</h6>
                      <ul className="list-disc list-inside text-blue-300 text-sm">
                        {check.details.map((detail, detailIndex) => (
                          <li key={detail.metric}>
                            {detail.metric}: {detail.value} (Threshold: {detail.threshold})
                            <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                              detail.status === 'passed' ? 'bg-green-500/20 text-green-400' :
                              detail.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-red-500/20 text-red-400'
                            }`}>
                              {detail.status}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
                <p className="text-blue-300 text-sm mt-2">File processed successfully with {result.checks.length} quality checks.</p>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <CheckCircle className="w-16 h-16 mx-auto text-blue-400 mb-4" />
          <p className="text-blue-200">No quality checks run yet</p>
          <p className="text-blue-300 text-sm">Click "Run New Check" to get started</p>
        </div>
      )}
    </div>
  </div>
);

const WorkspacesContent: React.FC<{
  workspaces: any[];
  onCreateWorkspace: () => void;
  onDeleteWorkspace: (id: string) => void;
  onEditWorkspace: (workspace: any) => void;
  onAddMember: (workspace: any) => void;
  onManageProjects: (workspace: any) => void;
}> = ({ workspaces, onCreateWorkspace, onDeleteWorkspace, onEditWorkspace, onAddMember, onManageProjects }) => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Team Workspaces</h2>
      <p className="text-blue-200 mb-6">Collaborative workspaces for team data quality management.</p>
      
      {/* Create New Workspace Button */}
      <div className="mb-6">
        <button 
          onClick={onCreateWorkspace}
          className="btn-primary flex items-center space-x-2"
        >
          <Users className="w-5 h-5" />
          <span>Create New Workspace</span>
        </button>
      </div>

      {/* Existing Workspaces */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workspaces.map((workspace, index) => (
          <motion.div
            key={workspace.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-4 card-hover relative group"
          >
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
              <button
                onClick={() => onEditWorkspace(workspace)}
                className="text-blue-400 hover:text-blue-300 p-1"
                title="Edit workspace"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={() => onAddMember(workspace)}
                className="text-green-400 hover:text-green-300 p-1"
                title="Add member"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
              <button
                onClick={() => onManageProjects(workspace)}
                className="text-purple-400 hover:text-purple-300 p-1"
                title="Manage projects"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </button>
              <button
                onClick={() => onDeleteWorkspace(workspace.id)}
                className="text-red-400 hover:text-red-300 p-1"
                title="Delete workspace"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            <h4 className="text-lg font-bold text-white mb-2">{workspace.name}</h4>
            <p className="text-blue-200 text-sm mb-2">{workspace.team} Team</p>
            {workspace.description && (
              <p className="text-blue-300 text-sm mb-3">{workspace.description}</p>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-blue-300">{workspace.members} members</span>
              <span className="text-blue-300">{workspace.projects} projects</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  </div>
);

const SchedulerContent: React.FC<{
  scheduledTasks: any[];
  onCreateTask: () => void;
  onEditTask: (task: any) => void;
  onDeleteTask: (id: string) => void;
  onToggleStatus: (id: string) => void;
  onRunNow: (id: string) => void;
}> = ({ scheduledTasks, onCreateTask, onEditTask, onDeleteTask, onToggleStatus, onRunNow }) => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Task Scheduler</h2>
      <p className="text-blue-200 mb-6">Automated quality check scheduling and monitoring.</p>
      
      {/* Schedule New Task */}
      <div className="bg-white/5 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-bold text-white mb-4">Schedule New Task</h3>
        <button 
          onClick={onCreateTask}
          className="btn-primary flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Schedule New Task</span>
        </button>
      </div>

      {/* Scheduled Tasks */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-white">Scheduled Tasks</h3>
        {scheduledTasks.length === 0 ? (
          <div className="text-center py-8 text-blue-300">
            <svg className="w-16 h-16 mx-auto mb-4 text-blue-400/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>No scheduled tasks yet. Create your first task to get started!</p>
          </div>
        ) : (
          scheduledTasks.map((task, index) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="glass-card p-4 relative group"
            >
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <button
                  onClick={() => onEditTask(task)}
                  className="text-blue-400 hover:text-blue-300 p-1"
                  title="Edit task"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={() => onRunNow(task.id)}
                  className="text-green-400 hover:text-green-300 p-1"
                  title="Run now"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={() => onToggleStatus(task.id)}
                  className={`p-1 ${task.status === 'active' ? 'text-yellow-400 hover:text-yellow-300' : 'text-green-400 hover:text-green-300'}`}
                  title={task.status === 'active' ? 'Pause task' : 'Activate task'}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={task.status === 'active' ? 'M6 18L18 6M6 6l12 12' : 'M5 13l4 4L19 7'} />
                  </svg>
                </button>
                <button
                  onClick={() => onDeleteTask(task.id)}
                  className="text-red-400 hover:text-red-300 p-1"
                  title="Delete task"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-lg font-bold text-white">{task.name}</h4>
                  <p className="text-blue-200 text-sm">{task.description}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  task.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {task.status === 'active' ? 'Active' : 'Paused'}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-blue-300">Frequency</p>
                  <p className="text-white font-medium capitalize">{task.frequency}</p>
                </div>
                <div>
                  <p className="text-blue-300">Time</p>
                  <p className="text-white font-medium">{task.time}</p>
                </div>
                <div>
                  <p className="text-blue-300">Day</p>
                  <p className="text-white font-medium capitalize">{task.day}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 text-sm">
                <div>
                  <p className="text-blue-300">Workspace</p>
                  <p className="text-white font-medium">{task.workspace}</p>
                </div>
                <div>
                  <p className="text-blue-300">Project</p>
                  <p className="text-white font-medium">{task.project}</p>
                </div>
              </div>
              
              <div className="border-t border-white/10 mt-3 pt-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-blue-300">Last Run</p>
                    <p className="text-white font-medium">{task.lastRun}</p>
                  </div>
                  <div>
                    <p className="text-blue-300">Next Run</p>
                    <p className="text-white font-medium">{task.nextRun}</p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  </div>
);

const BusinessRulesContent: React.FC<{
  businessRules: any[];
  onCreateRule: () => void;
  onEditRule: (rule: any) => void;
  onDeleteRule: (id: string) => void;
  onToggleStatus: (id: string) => void;
  onTestRule: (rule: any) => void;
}> = ({ businessRules, onCreateRule, onEditRule, onDeleteRule, onToggleStatus, onTestRule }) => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Business Rules</h2>
      <p className="text-blue-200 mb-6">Custom validation rules and business logic management.</p>
      
      {/* Create New Rule */}
      <div className="bg-white/5 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-bold text-white mb-4">Create New Rule</h3>
        <button 
          onClick={onCreateRule}
          className="btn-primary flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Create New Rule</span>
        </button>
      </div>

      {/* Existing Rules */}
      <div className="space-y-4">
        {businessRules.length === 0 ? (
          <div className="text-center py-8 text-blue-300">
            <svg className="w-16 h-16 mx-auto mb-4 text-blue-400/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <p>No business rules yet. Create your first rule to get started!</p>
          </div>
        ) : (
          businessRules.map((rule, index) => (
            <motion.div
              key={rule.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="glass-card p-4 relative group"
            >
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <button
                  onClick={() => onEditRule(rule)}
                  className="text-blue-400 hover:text-blue-300 p-1"
                  title="Edit rule"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={() => onTestRule(rule)}
                  className="text-green-400 hover:text-green-300 p-1"
                  title="Test rule"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </button>
                <button
                  onClick={() => onToggleStatus(rule.id)}
                  className={`p-1 ${rule.status === 'active' ? 'text-yellow-400 hover:text-yellow-300' : 'text-green-400 hover:text-green-300'}`}
                  title={rule.status === 'active' ? 'Pause rule' : 'Activate rule'}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={rule.status === 'active' ? 'M6 18L18 6M6 6l12 12' : 'M5 13l4 4L19 7'} />
                  </svg>
                </button>
                <button
                  onClick={() => onDeleteRule(rule.id)}
                  className="text-red-400 hover:text-red-300 p-1"
                  title="Delete rule"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="text-lg font-bold text-white">{rule.name}</h4>
                  <p className="text-blue-200 text-sm mb-2 capitalize">{rule.type.replace('_', ' ')}</p>
                  <p className="text-blue-300 text-sm">{rule.description}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  rule.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {rule.status === 'active' ? 'Active' : 'Paused'}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-sm">
                <div>
                  <p className="text-blue-300">Field</p>
                  <p className="text-white font-medium">{rule.conditions.field}</p>
                </div>
                <div>
                  <p className="text-blue-300">Operator</p>
                  <p className="text-white font-medium capitalize">{rule.conditions.operator}</p>
                </div>
                <div>
                  <p className="text-blue-300">Severity</p>
                  <p className="text-white font-medium capitalize">{rule.conditions.severity}</p>
                </div>
              </div>
              
              <div className="border-t border-white/10 mt-3 pt-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-blue-300">Created</p>
                    <p className="text-white font-medium">{rule.created_at}</p>
                  </div>
                  <div>
                    <p className="text-blue-300">Updated</p>
                    <p className="text-white font-medium">{rule.updated_at}</p>
                  </div>
                  <div>
                    <p className="text-blue-300">Applied</p>
                    <p className="text-white font-medium">{rule.applied_count} times</p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  </div>
);

const AnalyticsContent: React.FC = () => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Analytics</h2>
      <p className="text-blue-200 mb-6">Advanced analytics and ML-based quality scoring.</p>
      
      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white/5 rounded-lg p-4 text-center">
          <TrendingUp className="w-12 h-12 mx-auto text-green-400 mb-2" />
          <p className="text-2xl font-bold text-white">87.3%</p>
          <p className="text-blue-200 text-sm">Overall Quality Score</p>
        </div>
        <div className="bg-white/5 rounded-lg p-4 text-center">
          <Activity className="w-12 h-12 mx-auto text-blue-400 mb-2" />
          <p className="text-2xl font-bold text-white">1,247</p>
          <p className="text-blue-200 text-sm">Checks This Month</p>
        </div>
        <div className="bg-white/5 rounded-lg p-4 text-center">
          <BarChart3 className="w-12 h-12 mx-auto text-purple-400 mb-2" />
          <p className="text-2xl font-bold text-white">+12.5%</p>
          <p className="text-blue-200 text-sm">Quality Improvement</p>
        </div>
      </div>

      {/* ML Insights */}
      <div className="bg-white/5 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">ML Insights</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div className="flex items-center space-x-3">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              <span className="text-white">Anomaly Detection</span>
            </div>
            <span className="text-green-400">98% Accuracy</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div className="flex items-center space-x-3">
              <Brain className="w-5 h-5 text-blue-400" />
              <span className="text-white">Pattern Recognition</span>
            </div>
            <span className="text-green-400">94% Accuracy</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-5 h-5 text-purple-400" />
              <span className="text-white">Predictive Scoring</span>
            </div>
            <span className="text-green-400">91% Accuracy</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const ConnectorsContent: React.FC = () => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Data Connectors</h2>
      <p className="text-blue-200 mb-6">Database and cloud storage connector management.</p>
      
      {/* Add New Connector */}
      <div className="bg-white/5 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-bold text-white mb-4">Add New Connector</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <select className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>Select Connector Type</option>
            <option>MySQL</option>
            <option>PostgreSQL</option>
            <option>MongoDB</option>
            <option>AWS S3</option>
            <option>Azure Blob</option>
          </select>
          <input 
            type="text" 
            placeholder="Connection Name" 
            className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="btn-primary">Add Connector</button>
      </div>

      {/* Existing Connectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { name: 'Production MySQL', type: 'MySQL', status: 'Connected', lastSync: '2 min ago' },
          { name: 'Analytics Warehouse', type: 'PostgreSQL', status: 'Connected', lastSync: '5 min ago' },
          { name: 'User Data Store', type: 'MongoDB', status: 'Connected', lastSync: '1 min ago' },
          { name: 'Backup Storage', type: 'AWS S3', status: 'Connected', lastSync: '10 min ago' },
          { name: 'Archive Storage', type: 'Azure Blob', status: 'Disconnected', lastSync: '2 hours ago' }
        ].map((connector, index) => (
          <motion.div
            key={connector.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-4 card-hover"
          >
            <div className="flex items-start justify-between mb-3">
              <h4 className="text-lg font-bold text-white">{connector.name}</h4>
              <span className={`px-2 py-1 text-xs rounded-full ${
                connector.status === 'Connected' 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {connector.status}
              </span>
            </div>
            <p className="text-blue-200 text-sm mb-2">{connector.type}</p>
            <p className="text-blue-300 text-sm">Last sync: {connector.lastSync}</p>
          </motion.div>
        ))}
      </div>
    </div>
  </div>
);

const SettingsContent: React.FC = () => (
  <div className="space-y-6">
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-4">Settings</h2>
      <p className="text-blue-200 mb-6">System configuration and user preferences.</p>
      
      {/* User Profile */}
      <div className="bg-white/5 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-bold text-white mb-4">User Profile</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <input 
            type="text" 
            placeholder="Full Name" 
            defaultValue="Admin User"
            className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input 
            type="email" 
            placeholder="Email" 
            defaultValue="admin@algorzen.com"
            className="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="btn-primary">Update Profile</button>
      </div>

      {/* System Settings */}
      <div className="bg-white/5 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-bold text-white mb-4">System Settings</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-white">Auto-save reports</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-white">Email notifications</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-white">Dark mode</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-white/5 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">About</h3>
        <div className="space-y-2 text-blue-200">
          <p><strong>Version:</strong> 1.0.0</p>
          <p><strong>Build:</strong> 2024.08.27</p>
          <p><strong>License:</strong> Enterprise</p>
        </div>
      </div>
    </div>
  </div>
);

const MonitoringContent: React.FC<{
  monitoringData: any;
  onAcknowledgeAlert: (id: string) => void;
  onRefreshMetrics: () => void;
  onTestIntegration: (name: string) => void;
}> = ({ monitoringData, onAcknowledgeAlert, onRefreshMetrics, onTestIntegration }) => (
  <div className="space-y-6">
    {/* System Health Overview */}
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold gradient-text">System Health</h2>
        <button
          onClick={onRefreshMetrics}
          className="btn-secondary flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh</span>
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* System Status */}
        <div className="bg-white/5 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-white">Status</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              monitoringData.systemHealth.status === 'healthy' 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-red-500/20 text-red-400'
            }`}>
              {monitoringData.systemHealth.status}
            </span>
          </div>
          <p className="text-3xl font-bold text-blue-400">{monitoringData.systemHealth.uptime}</p>
          <p className="text-blue-300 text-sm">Uptime</p>
        </div>

        {/* CPU Usage */}
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">CPU Usage</h3>
          <div className="relative">
            <p className="text-3xl font-bold text-blue-400">{monitoringData.systemHealth.cpu}%</p>
            <div className="w-full bg-white/10 rounded-full h-2 mt-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${monitoringData.systemHealth.cpu}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Memory Usage</h3>
          <div className="relative">
            <p className="text-3xl font-bold text-blue-400">{monitoringData.systemHealth.memory}%</p>
            <div className="w-full bg-white/10 rounded-full h-2 mt-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${monitoringData.systemHealth.memory}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Disk Usage */}
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Disk Usage</h3>
          <div className="relative">
            <p className="text-3xl font-bold text-blue-400">{monitoringData.systemHealth.disk}%</p>
            <div className="w-full bg-white/10 rounded-full h-2 mt-2">
              <div 
                className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${monitoringData.systemHealth.disk}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 text-sm text-blue-300">
        Last updated: {new Date(monitoringData.systemHealth.lastCheck).toLocaleString()}
      </div>
    </div>

    {/* Quality Metrics */}
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-6">Quality Metrics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Success Rate</h3>
          <p className="text-3xl font-bold text-green-400">{monitoringData.qualityMetrics.successRate}%</p>
          <p className="text-blue-300 text-sm">Overall Quality Score</p>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Total Checks</h3>
          <p className="text-3xl font-bold text-blue-400">{monitoringData.qualityMetrics.totalChecks}</p>
          <p className="text-blue-300 text-sm">All Time</p>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Last Hour</h3>
          <p className="text-3xl font-bold text-cyan-400">{monitoringData.qualityMetrics.lastHourChecks}</p>
          <p className="text-blue-300 text-sm">Checks Executed</p>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Failed Checks</h3>
          <p className="text-3xl font-bold text-red-400">{monitoringData.qualityMetrics.failedChecks}</p>
          <p className="text-blue-300 text-sm">Require Attention</p>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Response Time</h3>
          <p className="text-3xl font-bold text-yellow-400">{monitoringData.qualityMetrics.avgResponseTime}s</p>
          <p className="text-blue-300 text-sm">Average</p>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Passed Checks</h3>
          <p className="text-3xl font-bold text-green-400">{monitoringData.qualityMetrics.passedChecks}</p>
          <p className="text-blue-300 text-sm">Successful</p>
        </div>
      </div>
    </div>

    {/* Alerts & Notifications */}
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-6">Alerts & Notifications</h2>
      
      <div className="space-y-4">
        {monitoringData.alerts.map((alert: any) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`p-4 rounded-lg border-l-4 ${
              alert.type === 'error' ? 'bg-red-500/10 border-red-500' :
              alert.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500' :
              'bg-blue-500/10 border-blue-500'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    alert.type === 'error' ? 'bg-red-500/20 text-red-400' :
                    alert.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    alert.type === 'error' ? 'bg-red-500/20 text-red-400' :
                    alert.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {alert.type.toUpperCase()}
                  </span>
                </div>
                <p className="text-white font-medium">{alert.message}</p>
                <p className="text-blue-300 text-sm mt-1">
                  {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
              {!alert.acknowledged && (
                <button
                  onClick={() => onAcknowledgeAlert(alert.id)}
                  className="btn-secondary text-sm px-3 py-1"
                >
                  Acknowledge
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>

    {/* Monitoring Integrations */}
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-6">Monitoring Integrations</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(monitoringData.integrations).map(([name, integration]: [string, any]) => (
          <motion.div
            key={name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/5 rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  integration.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <h3 className="text-lg font-semibold text-white capitalize">{name}</h3>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                integration.status === 'connected' 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {integration.status}
              </span>
            </div>
            
            <div className="space-y-2 text-sm">
              <p className="text-blue-300">
                <span className="text-white">URL:</span> {integration.url}
              </p>
              <p className="text-blue-300">
                <span className="text-white">Last Sync:</span> {
                  integration.lastSync 
                    ? new Date(integration.lastSync).toLocaleString()
                    : 'Never'
                }
              </p>
            </div>
            
            <div className="flex space-x-2 mt-4">
              <button
                onClick={() => onTestIntegration(name)}
                disabled={integration.status !== 'connected'}
                className="btn-secondary text-sm px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Test Connection
              </button>
              <button className="btn-primary text-sm px-3 py-1">
                Configure
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>

    {/* Quick Actions */}
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold gradient-text mb-6">Quick Actions</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button className="btn-primary p-4 text-center">
          <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span>Generate Report</span>
        </button>
        
        <button className="btn-secondary p-4 text-center">
          <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span>View Logs</span>
        </button>
        
        <button className="btn-secondary p-4 text-center">
          <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Configure Alerts</span>
        </button>
      </div>
    </div>
  </div>
);

export default App;
