import React, { ReactNode } from 'react';

// --- GlassCard: Translucent card with blurred background ---
interface GlassCardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`glass-card ${className}`}>
      {title && <h2 className="glass-card-title">{title}</h2>}
      <div className="glass-card-content">{children}</div>
    </div>
  );
};

// --- StatusBadge: Colored badge for statuses ---
interface StatusBadgeProps {
  status: 'success' | 'danger' | 'warning' | 'info' | 'error' | string;
  children: ReactNode;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, children, className = '' }) => {
  const statusClass = `status-badge status-${status}`;
  return (
    <span className={`${statusClass} ${className}`}>
      {children}
    </span>
  );
};

// --- HealthIndicator: Visual health indicator (dot) ---
interface HealthIndicatorProps {
  status: 'healthy' | 'unhealthy' | 'degraded' | string;
  className?: string;
}

export const HealthIndicator: React.FC<HealthIndicatorProps> = ({ status, className = '' }) => {
  const indicatorClass = `health-indicator health-${status}`;
  return (
    <span className={`${indicatorClass} ${className}`}>
      {status === 'healthy' ? '●' : status === 'unhealthy' ? '○' : '◐'}
    </span>
  );
};

// --- MetricCard: Card for displaying metrics ---
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, className = '' }) => {
  return (
    <div className={`metric-card ${className}`}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
    </div>
  );
};

// --- BackendCard: Card for backend status ---
interface BackendCardProps {
  title: string;
  status: 'running' | 'stopped' | 'degraded' | string;
  version: string;
  endpoint: string;
  className?: string;
}

export const BackendCard: React.FC<BackendCardProps> = ({ title, status, version, endpoint, className = '' }) => {
  return (
    <div className={`backend-card ${className}`}>
      <h3>{title}</h3>
      <div>
        <strong>Status:</strong> <StatusBadge status={status === 'running' ? 'success' : 'danger'}>{status}</StatusBadge>
      </div>
      <div>
        <strong>Version:</strong> {version}
      </div>
      <div>
        <strong>Endpoint:</strong> {endpoint}
      </div>
    </div>
  );
};

// --- ModelCard: Card for model information ---
interface ModelCardProps {
  name: string;
  provider: string;
  size: string;
  quantization: string;
  contextLength: number;
  enabled: boolean;
  className?: string;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  name,
  provider,
  size,
  quantization,
  contextLength,
  enabled,
  className = '',
}) => {
  return (
    <div className={`model-card ${className}`}>
      <h3>{name}</h3>
      <div>
        <strong>Provider:</strong> {provider}
      </div>
      <div>
        <strong>Size:</strong> {size}
      </div>
      <div>
        <strong>Quantization:</strong> {quantization}
      </div>
      <div>
        <strong>Context Length:</strong> {contextLength}
      </div>
      <div>
        <strong>Enabled:</strong> <StatusBadge status={enabled ? 'success' : 'warning'}>{enabled ? 'YES' : 'NO'}</StatusBadge>
      </div>
    </div>
  );
};

// --- CouncilVote: Component for Council voting ---
interface CouncilVoteProps {
  reviewer: string;
  decision: 'ALLOW' | 'DENY' | 'ESCALATE' | string;
  confidence: number;
  reason: string;
  className?: string;
}

export const CouncilVote: React.FC<CouncilVoteProps> = ({
  reviewer,
  decision,
  confidence,
  reason,
  className = '',
}) => {
  return (
    <div className={`council-vote ${className}`}>
      <div className="vote-reviewer">{reviewer}</div>
      <div className="vote-decision">
        <StatusBadge status={decision === 'ALLOW' ? 'success' : decision === 'DENY' ? 'danger' : 'warning'}>
          {decision}
        </StatusBadge>
      </div>
      <div className="vote-confidence">{confidence * 100}%</div>
      <div className="vote-reason">{reason}</div>
    </div>
  );
};

// --- PermissionGate: Component for tool permission display ---
interface PermissionGateProps {
  tool: string;
  risk: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  policy: 'AUTO' | 'CONFIRM' | 'DENY' | string;
  enabled: boolean;
  className?: string;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  tool,
  risk,
  policy,
  enabled,
  className = '',
}) => {
  return (
    <div className={`permission-gate ${className}`}>
      <div className="permission-tool">{tool}</div>
      <div className="permission-risk">
        <StatusBadge status={risk === 'CRITICAL' ? 'danger' : risk === 'HIGH' ? 'warning' : 'info'}>
          {risk}
        </StatusBadge>
      </div>
      <div className="permission-policy">{policy}</div>
      <div className="permission-enabled">
        <StatusBadge status={enabled ? 'success' : 'warning'}>{enabled ? 'ENABLED' : 'DISABLED'}</StatusBadge>
      </div>
    </div>
  );
};

// --- EventStream: Component for live event streaming ---
interface EventStreamProps {
  events: Array<{
    timestamp: string;
    event_type: string;
    run_id?: string;
    task_id?: string;
    metadata?: any;
  }>;
  className?: string;
}

export const EventStream: React.FC<EventStreamProps> = ({ events, className = '' }) => {
  return (
    <div className={`event-stream ${className}`}>
      <h3>Live Events</h3>
      <div className="events-list">
        {events.map((event, index) => (
          <div key={index} className="event-item">
            <span className="event-timestamp">{new Date(event.timestamp).toLocaleTimeString()}</span>
            <span className="event-type">{event.event_type}</span>
            {event.run_id && <span className="event-run-id">Run: {event.run_id}</span>}
            {event.task_id && <span className="event-task-id">Task: {event.task_id}</span>}
          </div>
        ))}
      </div>
    </div>
  );
};

// --- TaskCard: Card for task information ---
interface TaskCardProps {
  taskId: string;
  goal: string;
  status: string;
  autonomy: number;
  className?: string;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  taskId,
  goal,
  status,
  autonomy,
  className = '',
}) => {
  return (
    <div className={`task-card ${className}`}>
      <h3>Task: {taskId}</h3>
      <div>
        <strong>Goal:</strong> {goal}
      </div>
      <div>
        <strong>Status:</strong> <StatusBadge status={status === 'completed' ? 'success' : status === 'failed' ? 'danger' : 'info'}>{status}</StatusBadge>
      </div>
      <div>
        <strong>Autonomy:</strong> {autonomy}
      </div>
    </div>
  );
};

// --- ConfirmDialog: Dialog for confirmation ---
interface ConfirmDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  isOpen: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  onConfirm,
  onCancel,
  isOpen,
}) => {
  if (!isOpen) return null;
  return (
    <div className="dialog-overlay">
      <div className="dialog">
        <h2>{title}</h2>
        <p>{message}</p>
        <div className="dialog-actions">
          <button onClick={onCancel}>Cancel</button>
          <button onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  );
};

// --- DangerDialog: Dialog for dangerous actions ---
interface DangerDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  isOpen: boolean;
}

export const DangerDialog: React.FC<DangerDialogProps> = ({
  title,
  message,
  onConfirm,
  onCancel,
  isOpen,
}) => {
  if (!isOpen) return null;
  return (
    <div className="dialog-overlay">
      <div className="dialog danger-dialog">
        <h2>
          <StatusBadge status="danger">⚠️ {title}</StatusBadge>
        </h2>
        <p>{message}</p>
        <div className="dialog-actions">
          <button onClick={onCancel}>Cancel</button>
          <button onClick={onConfirm} className="danger-button">
            Confirm (Dangerous)
          </button>
        </div>
      </div>
    </div>
  );
};

// --- Toast: Notification toast ---
interface ToastProps {
  message: string;
  status: 'success' | 'danger' | 'warning' | 'info';
  onClose: () => void;
  isOpen: boolean;
}

export const Toast: React.FC<ToastProps> = ({ message, status, onClose, isOpen }) => {
  if (!isOpen) return null;
  return (
    <div className={`toast toast-${status}`}>
      <span>{message}</span>
      <button onClick={onClose} className="toast-close">
        ×
      </button>
    </div>
  );
};
