import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface CouncilVote {
  vote_id: string;
  reviewer: string;
  decision: 'ALLOW' | 'DENY' | 'ESCALATE';
  confidence: number;
  reason: string;
  timestamp: string;
}

interface CouncilStatus {
  mode: string;
  minimum_confidence: number;
  minimum_reviews: number;
  fail_closed_on_disagreement: boolean;
}

const CouncilPage: React.FC = () => {
  const [councilStatus, setCouncilStatus] = useState<CouncilStatus | null>(null);
  const [votes, setVotes] = useState<CouncilVote[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Council status and votes
  useEffect(() => {
    const fetchCouncilData = async () => {
      try {
        const [statusRes, votesRes] = await Promise.all([
          fetch('http://127.0.0.1:8101/api/system1/council'),
          fetch('http://127.0.0.1:8101/api/system1/council'),
        ]);
        if (!statusRes.ok || !votesRes.ok) {
          throw new Error('Failed to fetch Council data');
        }
        const statusData = await statusRes.json();
        const votesData = await votesRes.json();
        setCouncilStatus(statusData);
        setVotes(votesData.recent_votes || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchCouncilData();
  }, []);

  // Simulate a Council vote (for demo purposes)
  const handleVote = async (reviewer: string, decision: 'ALLOW' | 'DENY' | 'ESCALATE') => {
    try {
      const response = await fetch('http://127.0.0.1:8101/api/system1/council/vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer,
          decision,
          confidence: 0.9,
          reason: `Demo vote by ${reviewer}`,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to cast vote');
      }
      const result = await response.json();
      alert(`Vote cast! Decision: ${result.decision}, Allowed: ${result.allowed}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page council-page">
        <h1>System 1 Council</h1>
        <p>Loading Council data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page council-page">
        <h1>System 1 Council</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page council-page">
      <h1>System 1 Council</h1>
      <p>
        The Council reviews execution proposals and votes to <StatusBadge status="success">ALLOW</StatusBadge>, 
        <StatusBadge status="danger">DENY</StatusBadge>, or <StatusBadge status="warning">ESCALATE</StatusBadge>.
      </p>

      {/* Council Configuration */}
      <GlassCard title="Council Configuration">
        <div className="council-config">
          <div>
            <strong>Mode:</strong> {councilStatus?.mode || 'Consensus'}
          </div>
          <div>
            <strong>Minimum Confidence:</strong> {councilStatus?.minimum_confidence || 0.7}
          </div>
          <div>
            <strong>Minimum Reviews:</strong> {councilStatus?.minimum_reviews || 2}
          </div>
          <div>
            <strong>Fail Closed on Disagreement:</strong> {councilStatus?.fail_closed_on_disagreement ? 'Yes' : 'No'}
          </div>
        </div>
      </GlassCard>

      {/* Voting Interface */}
      <GlassCard title="Cast a Vote">
        <div className="voting-interface">
          <h3>Reviewers:</h3>
          <div className="reviewers">
            {['OpenAI', 'Gemini', 'Anthropic', 'Built-in Guard'].map((reviewer) => (
              <div key={reviewer} className="reviewer">
                <span>{reviewer}</span>
                <div className="vote-buttons">
                  <button onClick={() => handleVote(reviewer, 'ALLOW')}>ALLOW</button>
                  <button onClick={() => handleVote(reviewer, 'DENY')}>DENY</button>
                  <button onClick={() => handleVote(reviewer, 'ESCALATE')}>ESCALATE</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Recent Votes */}
      <GlassCard title="Recent Votes">
        {votes.length === 0 ? (
          <p>No votes cast yet.</p>
        ) : (
          <table className="votes-table">
            <thead>
              <tr>
                <th>Reviewer</th>
                <th>Decision</th>
                <th>Confidence</th>
                <th>Reason</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {votes.map((vote) => (
                <tr key={vote.vote_id}>
                  <td>{vote.reviewer}</td>
                  <td>
                    <StatusBadge status={vote.decision === 'ALLOW' ? 'success' : vote.decision === 'DENY' ? 'danger' : 'warning'}>
                      {vote.decision}
                    </StatusBadge>
                  </td>
                  <td>{(vote.confidence * 100).toFixed(1)}%</td>
                  <td>{vote.reason}</td>
                  <td>{new Date(vote.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </GlassCard>

      {/* Council Decision Summary */}
      <GlassCard title="Council Decision Summary">
        <div className="decision-summary">
          <p>
            Final decisions are made based on the Council mode:
          </p>
          <ul>
            <li><strong>Any:</strong> One ALLOW vote is sufficient.</li>
            <li><strong>All:</strong> All reviewers must ALLOW.</li>
            <li><strong>Consensus:</strong> Majority ALLOW votes win.</li>
          </ul>
          <p>
            <strong>Current Mode:</strong> {councilStatus?.mode || 'Consensus'}
          </p>
        </div>
      </GlassCard>
    </div>
  );
};

export default CouncilPage;
