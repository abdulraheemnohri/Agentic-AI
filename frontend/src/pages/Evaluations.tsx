import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, MetricCard } from '../components';

interface Evaluation {
  evaluation_id: string;
  task_id: string;
  run_id?: string;
  overall_status: string;
  overall_score: number;
  confidence: number;
  summary: string;
  checks: { [key: string]: boolean };
  created_at: string;
  human_review?: {
    score: number;
    label: string;
    notes: string;
  };
}

interface EvaluationStats {
  total: number;
  passed: number;
  failed: number;
  average_score: number;
  average_confidence: number;
}

const EvaluationsPage: React.FC = () => {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [filteredEvaluations, setFilteredEvaluations] = useState<Evaluation[]>([]);
  const [stats, setStats] = useState<EvaluationStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    status: '',
    task_id: '',
    min_score: 0,
    max_score: 1,
    min_confidence: 0,
    max_confidence: 1,
  });

  // Fetch evaluations
  useEffect(() => {
    const fetchEvaluations = async () => {
      try {
        // Fetch all tasks first to get evaluations
        const tasksRes = await fetch('http://127.0.0.1:8000/api/tasks');
        if (!tasksRes.ok) {
          throw new Error('Failed to fetch tasks');
        }
        const tasksData = await tasksRes.json();

        // Collect all evaluations from tasks
        const allEvaluations: Evaluation[] = [];
        for (const task of tasksData) {
          if (task.evaluation) {
            allEvaluations.push({
              evaluation_id: `eval_${task.id}_${task.updated_at}`,
              task_id: task.id,
              run_id: task.run_id,
              ...task.evaluation,
              created_at: task.updated_at,
            });
          }
        }

        setEvaluations(allEvaluations);
        setFilteredEvaluations(allEvaluations);

        // Calculate stats
        const passed = allEvaluations.filter((e) => e.overall_status === 'passed').length;
        const failed = allEvaluations.filter((e) => e.overall_status === 'failed').length;
        const avgScore = allEvaluations.reduce((sum, e) => sum + e.overall_score, 0) / allEvaluations.length || 0;
        const avgConfidence = allEvaluations.reduce((sum, e) => sum + e.confidence, 0) / allEvaluations.length || 0;

        setStats({
          total: allEvaluations.length,
          passed,
          failed,
          average_score: avgScore,
          average_confidence: avgConfidence,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchEvaluations();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = [...evaluations];

    if (filters.status) {
      filtered = filtered.filter((e) => e.overall_status === filters.status);
    }

    if (filters.task_id) {
      filtered = filtered.filter((e) => e.task_id.includes(filters.task_id));
    }

    if (filters.min_score > 0) {
      filtered = filtered.filter((e) => e.overall_score >= filters.min_score);
    }

    if (filters.max_score < 1) {
      filtered = filtered.filter((e) => e.overall_score <= filters.max_score);
    }

    if (filters.min_confidence > 0) {
      filtered = filtered.filter((e) => e.confidence >= filters.min_confidence);
    }

    if (filters.max_confidence < 1) {
      filtered = filtered.filter((e) => e.confidence <= filters.max_confidence);
    }

    setFilteredEvaluations(filtered);
  }, [filters, evaluations]);

  // Export evaluations as JSON
  const exportEvaluations = () => {
    const dataStr = JSON.stringify(filteredEvaluations, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'evaluations.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="page evaluations-page">
        <h1>Evaluations</h1>
        <p>Loading evaluations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page evaluations-page">
        <h1>Evaluations</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page evaluations-page">
      <h1>Evaluations</h1>
      <p>
        Evaluation history and scores for all agent runs.
        Evaluations are performed after verification to assess the quality of the agent's work.
      </p>

      {/* Evaluation Stats */}
      <GlassCard title="Evaluation Stats">
        <div className="evaluation-stats-grid">
          <MetricCard
            title="Total Evaluations"
            value={stats?.total || 0}
            subtitle="All evaluations"
          />
          <MetricCard
            title="Passed"
            value={stats?.passed || 0}
            subtitle="Evaluations with PASSED status"
          />
          <MetricCard
            title="Failed"
            value={stats?.failed || 0}
            subtitle="Evaluations with FAILED status"
          />
          <MetricCard
            title="Avg Score"
            value={(stats?.average_score || 0).toFixed(2)}
            subtitle="Average evaluation score (0-1)"
          />
          <MetricCard
            title="Avg Confidence"
            value={(stats?.average_confidence || 0).toFixed(2)}
            subtitle="Average confidence score (0-1)"
          />
        </div>
      </GlassCard>

      {/* Filters */}
      <GlassCard title="Filters">
        <div className="evaluation-filters">
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Task ID:</label>
            <input
              type="text"
              placeholder="e.g., task_12345678"
              value={filters.task_id}
              onChange={(e) => setFilters({ ...filters, task_id: e.target.value })}
            />
          </div>
          <div className="filter-group">
            <label>Min Score (0-1):</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.min_score}
              onChange={(e) => setFilters({ ...filters, min_score: Number(e.target.value) })}
            />
          </div>
          <div className="filter-group">
            <label>Max Score (0-1):</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.max_score}
              onChange={(e) => setFilters({ ...filters, max_score: Number(e.target.value) })}
            />
          </div>
          <div className="filter-group">
            <label>Min Confidence (0-1):</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.min_confidence}
              onChange={(e) => setFilters({ ...filters, min_confidence: Number(e.target.value) })}
            />
          </div>
          <div className="filter-group">
            <label>Max Confidence (0-1):</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.max_confidence}
              onChange={(e) => setFilters({ ...filters, max_confidence: Number(e.target.value) })}
            />
          </div>
          <div className="filter-actions">
            <button className="ghost" onClick={() => setFilters({
              status: '',
              task_id: '',
              min_score: 0,
              max_score: 1,
              min_confidence: 0,
              max_confidence: 1,
            })}>
              Clear Filters
            </button>
            <button onClick={exportEvaluations}>Export JSON</button>
          </div>
        </div>
      </GlassCard>

      {/* Evaluations List */}
      <GlassCard title="Evaluations">
        <div className="evaluations-list">
          {filteredEvaluations.length ? (
            filteredEvaluations.map((evaluation) => (
              <div key={evaluation.evaluation_id} className="evaluation-card">
                <div className="evaluation-header">
                  <StatusBadge status={getStatusColor(evaluation.overall_status)}>
                    {evaluation.overall_status}
                  </StatusBadge>
                  <span className="evaluation-score">
                    Score: {(evaluation.overall_score * 100).toFixed(1)}%
                  </span>
                  <span className="evaluation-confidence">
                    Confidence: {(evaluation.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="evaluation-summary">
                  <p>{evaluation.summary}</p>
                </div>
                <div className="evaluation-checks">
                  <strong>Checks:</strong>
                  <div className="checks-grid">
                    {Object.entries(evaluation.checks || {}).map(([check, passed]) => (
                      <div key={check} className="check-item">
                        <span>{check}:</span>
                        <StatusBadge status={passed ? 'success' : 'danger'}>
                          {passed ? '✓' : '✗'}
                        </StatusBadge>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="evaluation-meta">
                  <small>
                    Task: {evaluation.task_id.slice(0, 8)} | 
                    Created: {new Date(evaluation.created_at).toLocaleString()}
                  </small>
                </div>
                {evaluation.human_review && (
                  <div className="evaluation-human-review">
                    <strong>Human Review:</strong>
                    <div>
                      <strong>Score:</strong> {(evaluation.human_review.score * 100).toFixed(1)}%
                    </div>
                    <div>
                      <strong>Label:</strong> {evaluation.human_review.label}
                    </div>
                    <div>
                      <strong>Notes:</strong> {evaluation.human_review.notes}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <p>No evaluations match the filters.</p>
          )}
        </div>
      </GlassCard>

      {/* Evaluation Rules */}
      <GlassCard title="Evaluation Rules">
        <div className="evaluation-rules">
          <h3>📊 Evaluation Criteria:</h3>
          <ul>
            <li>
              <strong>Overall Status:</strong> PASSED or FAILED based on checks and thresholds.
            </li>
            <li>
              <strong>Overall Score:</strong> 0-1 score representing the quality of the agent's work.
            </li>
            <li>
              <strong>Confidence:</strong> 0-1 score representing the evaluator's confidence in the assessment.
            </li>
            <li>
              <strong>Checks:</strong> Individual checks (e.g., "goal_achieved", "no_errors") that contribute to the overall score.
            </li>
          </ul>

          <h3>🎯 Scoring:</h3>
          <ul>
            <li><strong>0.0 - 0.5:</strong> Poor (Agent failed to achieve the goal).</li>
            <li><strong>0.6 - 0.7:</strong> Fair (Agent partially achieved the goal).</li>
            <li><strong>0.8 - 0.9:</strong> Good (Agent achieved the goal with minor issues).</li>
            <li><strong>1.0:</strong> Excellent (Agent achieved the goal perfectly).</li>
          </ul>

          <h3>🔍 Human Review:</h3>
          <ul>
            <li>✓ Human reviews can <strong>override</strong> automatic evaluations.</li>
            <li>✓ Human reviews are <strong>stored with the evaluation</strong>.</li>
            <li>✓ Human reviews can include <strong>notes</strong> for future reference.</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

// Helper function
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'passed':
      return 'success';
    case 'failed':
      return 'danger';
    default:
      return 'info';
  }
}

export default EvaluationsPage;
