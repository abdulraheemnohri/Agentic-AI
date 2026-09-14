import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface SecurityRules {
  system1_authority: boolean;
  system1_always_on: boolean;
  system2_authority: boolean;
  system2_loopback_only: boolean;
  remote_system2_fallback: boolean;
  execution_requires_council: boolean;
  execution_requires_tool_permission: boolean;
  critical_tools_blocked_by_default: boolean;
  unknown_actions_fail_closed: boolean;
}

interface SecurityStatus {
  system1_health: string;
  system2_health: string;
  council_status: string;
  tool_permission_status: string;
  recovery_status: string;
}

const SecurityPage: React.FC = () => {
  const [securityRules, setSecurityRules] = useState<SecurityRules | null>(null);
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch security rules and status
  useEffect(() => {
    const fetchSecurityData = async () => {
      try {
        // Fetch security rules from System 1
        const rulesRes = await fetch('http://127.0.0.1:8101/api/system1/security');
        if (!rulesRes.ok) {
          throw new Error('Failed to fetch security rules');
        }
        const rulesData = await rulesRes.json();
        setSecurityRules(rulesData);

        // Fetch security status (placeholder: use rules for now)
        setSecurityStatus({
          system1_health: 'HEALTHY',
          system2_health: 'HEALTHY',
          council_status: 'ACTIVE',
          tool_permission_status: 'ENFORCED',
          recovery_status: 'READY',
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchSecurityData();
  }, []);

  if (loading) {
    return (
      <div className="page security-page">
        <h1>Security</h1>
        <p>Loading security data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page security-page">
        <h1>Security</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page security-page">
      <h1>Security</h1>
      <p>
        System 1 enforces <StatusBadge status="success">strict security rules</StatusBadge>.
        System 2 operates under <StatusBadge status="info">loopback-only restrictions</StatusBadge>.
      </p>

      {/* Security Status */}
      <GlassCard title="Security Status">
        <div className="security-status-grid">
          <div className="security-status-item">
            <strong>System 1 Authority:</strong>
            <StatusBadge status={securityRules?.system1_authority ? 'success' : 'danger'}>{
              securityRules?.system1_authority ? 'ACTIVE' : 'INACTIVE'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>System 1 Always On:</strong>
            <StatusBadge status={securityRules?.system1_always_on ? 'success' : 'danger'}>{
              securityRules?.system1_always_on ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>System 2 Authority:</strong>
            <StatusBadge status={!securityRules?.system2_authority ? 'success' : 'danger'}>{
              !securityRules?.system2_authority ? 'NONE' : 'RISK!'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>System 2 Loopback Only:</strong>
            <StatusBadge status={securityRules?.system2_loopback_only ? 'success' : 'danger'}>{
              securityRules?.system2_loopback_only ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>Remote System 2 Fallback:</strong>
            <StatusBadge status={!securityRules?.remote_system2_fallback ? 'success' : 'danger'}>{
              !securityRules?.remote_system2_fallback ? 'DISABLED' : 'ENABLED (RISK!)'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>Execution Requires Council:</strong>
            <StatusBadge status={securityRules?.execution_requires_council ? 'success' : 'danger'}>{
              securityRules?.execution_requires_council ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>Execution Requires Tool Permission:</strong>
            <StatusBadge status={securityRules?.execution_requires_tool_permission ? 'success' : 'danger'}>{
              securityRules?.execution_requires_tool_permission ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>Critical Tools Blocked by Default:</strong>
            <StatusBadge status={securityRules?.critical_tools_blocked_by_default ? 'success' : 'danger'}>{
              securityRules?.critical_tools_blocked_by_default ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
          <div className="security-status-item">
            <strong>Unknown Actions Fail Closed:</strong>
            <StatusBadge status={securityRules?.unknown_actions_fail_closed ? 'success' : 'danger'}>{
              securityRules?.unknown_actions_fail_closed ? 'YES' : 'NO'
            }</StatusBadge>
          </div>
        </div>
      </GlassCard>

      {/* Security Rules */}
      <GlassCard title="Security Rules">
        <div className="security-rules">
          <h3>🔒 System 1 Authority Rules:</h3>
          <ol>
            <li>
              <strong>System 1 is always authoritative.</strong>
              <p>System 1 owns permissions, execution, verification, evaluation, and recovery. System 2 can only propose.</p>
            </li>
            <li>
              <strong>System 1 is always-on.</strong>
              <p>System 1 cannot be stopped by System 2 or the frontend. It runs independently on <code>127.0.0.1:8101</code>.</p>
            </li>
            <li>
              <strong>System 2 cannot modify System 1.</strong>
              <p>System 2 has no write access to System 1's configuration, providers, or policies.</p>
            </li>
            <li>
              <strong>System 2 cannot stop System 1.</strong>
              <p>System 1 has no <code>/stop</code> endpoint. It can only be stopped by killing the process.</p>
            </li>
            <li>
              <strong>System 2 cannot authorize execution.</strong>
              <p>All executions must be approved by System 1's Council and Tool Permission Gate.</p>
            </li>
            <li>
              <strong>System 2 cannot bypass the Council.</strong>
              <p>Every execution proposal must pass through System 1's Council for voting.</p>
            </li>
            <li>
              <strong>Tool permissions are mandatory.</strong>
              <p>No tool can execute without explicit <code>ALLOW</code> permission from System 1.</p>
            </li>
            <li>
              <strong>Critical tools are blocked by default.</strong>
              <p>Tools with <StatusBadge status="error">CRITICAL</StatusBadge> risk are denied unless explicitly allowed.</p>
            </li>
            <li>
              <strong>Unknown actions fail closed.</strong>
              <p>If System 1 encounters an unknown action, it defaults to <StatusBadge status="danger">DENY</StatusBadge>.</p>
            </li>
            <li>
              <strong>All security violations are audited.</strong>
              <p>Every attempt to bypass System 1 is logged in the audit trail.</p>
            </li>
          </ol>

          <h3>🔐 System 2 Restrictions:</h3>
          <ol>
            <li>
              <strong>System 2 is loopback-only.</strong>
              <p>System 2 can only connect to <code>127.0.0.1</code>, <code>localhost</code>, or <code>::1</code>.</p>
            </li>
            <li>
              <strong>System 2 has no authority.</strong>
              <p>System 2 can propose, reason, and generate plans, but it cannot authorize or execute.</p>
            </li>
            <li>
              <strong>System 2 is replaceable.</strong>
              <p>System 2 can be restarted, updated, or replaced without affecting System 1.</p>
            </li>
            <li>
              <strong>System 2 cannot use remote endpoints.</strong>
              <p>Public IPs, domains, and <code>https</code> endpoints are rejected.</p>
            </li>
          </ol>
        </div>
      </GlassCard>

      {/* Security Dashboard */}
      <GlassCard title="Security Dashboard">
        <div className="security-dashboard">
          <h3>✅ Enforced Security Measures:</h3>
          <ul>
            <li>
              <StatusBadge status="success">System 1 Authority</StatusBadge>
              <p>System 1 is the authoritative control plane. It cannot be bypassed.</p>
            </li>
            <li>
              <StatusBadge status="success">Always-On Protection</StatusBadge>
              <p>System 1 runs 24/7 and cannot be stopped by System 2 or the frontend.</p>
            </li>
            <li>
              <StatusBadge status="success">Council Required</StatusBadge>
              <p>All executions must be approved by System 1's Council.</p>
            </li>
            <li>
              <StatusBadge status="success">Tool Permission Required</StatusBadge>
              <p>No tool can execute without explicit permission from System 1.</p>
            </li>
            <li>
              <StatusBadge status="success">System 2 Loopback</StatusBadge>
              <p>System 2 is restricted to loopback endpoints only.</p>
            </li>
            <li>
              <StatusBadge status="success">Remote System 2 Fallback Disabled</StatusBadge>
              <p>System 2 cannot fall back to remote endpoints under any circumstances.</p>
            </li>
          </ul>

          <h3>⚠️ Security Warnings:</h3>
          <ul>
            {securityRules?.system2_authority && (
              <li>
                <StatusBadge status="danger">System 2 Has Authority</StatusBadge>
                <p><strong>CRITICAL:</strong> System 2 should never have authority. This is a security risk!</p>
              </li>
            )}
            {securityRules?.remote_system2_fallback && (
              <li>
                <StatusBadge status="danger">Remote System 2 Fallback Enabled</StatusBadge>
                <p><strong>CRITICAL:</strong> Remote fallback for System 2 is a security risk!</p>
              </li>
            )}
            {!securityRules?.execution_requires_council && (
              <li>
                <StatusBadge status="danger">Council Not Required</StatusBadge>
                <p><strong>CRITICAL:</strong> Executions should always require Council approval!</p>
              </li>
            )}
            {!securityRules?.execution_requires_tool_permission && (
              <li>
                <StatusBadge status="danger">Tool Permissions Not Required</StatusBadge>
                <p><strong>CRITICAL:</strong> Executions should always require tool permissions!</p>
              </li>
            )}
          </ul>
        </div>
      </GlassCard>

      {/* Security Best Practices */}
      <GlassCard title="Security Best Practices">
        <div className="security-best-practices">
          <h3>🔐 General:</h3>
          <ul>
            <li>Never expose System 1 to the public internet.</li>
            <li>Always run System 1 and System 2 on <code>127.0.0.1</code>.</li>
            <li>Use strong, unique passwords for all providers (OpenAI, Gemini, etc.).</li>
            <li>Rotate API keys and tokens regularly.</li>
            <li>Never commit secrets to GitHub (use <code>.env</code> and <code>.gitignore</code>).</li>
          </ul>

          <h3>🛡️ System 1:</h3>
          <ul>
            <li>Monitor System 1 health and uptime.</li>
            <li>Review Council decisions regularly.</li>
            <li>Audit all security violations.</li>
            <li>Keep System 1 updated with the latest security patches.</li>
          </ul>

          <h3>🧠 System 2:</h3>
          <ul>
            <li>Only use trusted local models (Ollama, LM Studio, llama.cpp).</li>
            <li>Never allow System 2 to connect to remote endpoints.</li>
            <li>Validate all System 2 proposals before execution.</li>
            <li>Monitor System 2 resource usage (CPU, memory).</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

export default SecurityPage;
