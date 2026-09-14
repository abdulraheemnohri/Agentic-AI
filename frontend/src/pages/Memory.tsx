import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, MetricCard } from '../components';

interface Memory {
  memory_id: string;
  content: string;
  kind: string;
  importance: number;
  metadata: any;
  created_at: string;
  updated_at: string;
}

interface MemoryStats {
  total: number;
  episodic: number;
  semantic: number;
  procedural: number;
  average_importance: number;
}

const MemoryPage: React.FC = () => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [kindFilter, setKindFilter] = useState<string>('');
  const [importanceThreshold, setImportanceThreshold] = useState<number>(0);
  const [newMemory, setNewMemory] = useState<Omit<Memory, 'memory_id' | 'created_at' | 'updated_at'>>({
    content: '',
    kind: 'episodic',
    importance: 0.5,
    metadata: {},
  });

  // Fetch memories
  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/memory?limit=100');
        if (!response.ok) {
          throw new Error('Failed to fetch memories');
        }
        const data = await response.json();
        setMemories(data.memories || []);
        setFilteredMemories(data.memories || []);

        // Calculate stats
        const episodic = data.memories.filter((m: Memory) => m.kind === 'episodic').length;
        const semantic = data.memories.filter((m: Memory) => m.kind === 'semantic').length;
        const procedural = data.memories.filter((m: Memory) => m.kind === 'procedural').length;
        const avgImportance = data.memories.reduce((sum: number, m: Memory) => sum + m.importance, 0) / data.memories.length || 0;

        setStats({
          total: data.memories.length,
          episodic,
          semantic,
          procedural,
          average_importance: avgImportance,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchMemories();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = [...memories];

    if (searchQuery) {
      filtered = filtered.filter((memory) =>
        memory.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (kindFilter) {
      filtered = filtered.filter((memory) => memory.kind === kindFilter);
    }

    if (importanceThreshold > 0) {
      filtered = filtered.filter((memory) => memory.importance >= importanceThreshold);
    }

    setFilteredMemories(filtered);
  }, [searchQuery, kindFilter, importanceThreshold, memories]);

  // Create a new memory
  const createMemory = async () => {
    if (!newMemory.content.trim()) {
      setError('Memory content cannot be empty');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMemory),
      });
      if (!response.ok) {
        throw new Error('Failed to create memory');
      }
      const result = await response.json();
      setNewMemory({
        content: '',
        kind: 'episodic',
        importance: 0.5,
        metadata: {},
      });
      // Refresh memories
      const memoriesRes = await fetch('http://127.0.0.1:8000/api/memory?limit=100');
      if (memoriesRes.ok) {
        const memoriesData = await memoriesRes.json();
        setMemories(memoriesData.memories || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Delete a memory
  const deleteMemory = async (memoryId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/memory/${memoryId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete memory');
      }
      // Refresh memories
      const memoriesRes = await fetch('http://127.0.0.1:8000/api/memory?limit=100');
      if (memoriesRes.ok) {
        const memoriesData = await memoriesRes.json();
        setMemories(memoriesData.memories || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page memory-page">
        <h1>Memory</h1>
        <p>Loading memories...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page memory-page">
        <h1>Memory</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page memory-page">
      <h1>Memory</h1>
      <p>
        Search and recall past experiences. Memories are stored in SQLite and used by the agent for learning.
      </p>

      {/* Memory Stats */}
      <GlassCard title="Memory Stats">
        <div className="memory-stats-grid">
          <MetricCard
            title="Total Memories"
            value={stats?.total || 0}
            subtitle="All stored memories"
          />
          <MetricCard
            title="Episodic"
            value={stats?.episodic || 0}
            subtitle="Event-based memories"
          />
          <MetricCard
            title="Semantic"
            value={stats?.semantic || 0}
            subtitle="Fact-based memories"
          />
          <MetricCard
            title="Procedural"
            value={stats?.procedural || 0}
            subtitle="Process-based memories"
          />
          <MetricCard
            title="Avg Importance"
            value={(stats?.average_importance || 0).toFixed(2)}
            subtitle="Average importance score"
          />
        </div>
      </GlassCard>

      {/* Memory Filters */}
      <GlassCard title="Filters">
        <div className="memory-filters">
          <div className="filter-group">
            <label>Search:</label>
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Kind:</label>
            <select
              value={kindFilter}
              onChange={(e) => setKindFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="episodic">Episodic</option>
              <option value="semantic">Semantic</option>
              <option value="procedural">Procedural</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Min Importance (0-1):</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={importanceThreshold}
              onChange={(e) => setImportanceThreshold(Number(e.target.value))}
            />
          </div>
          <div className="filter-actions">
            <button className="ghost" onClick={() => {
              setSearchQuery('');
              setKindFilter('');
              setImportanceThreshold(0);
            }}>
              Clear Filters
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Create Memory */}
      <GlassCard title="Create Memory">
        <div className="create-memory">
          <div className="form-group">
            <label>Content:</label>
            <textarea
              value={newMemory.content}
              onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
              placeholder="Enter memory content..."
              rows={3}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Kind:</label>
              <select
                value={newMemory.kind}
                onChange={(e) => setNewMemory({ ...newMemory, kind: e.target.value as any })}
              >
                <option value="episodic">Episodic</option>
                <option value="semantic">Semantic</option>
                <option value="procedural">Procedural</option>
              </select>
            </div>
            <div className="form-group">
              <label>Importance (0-1):</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={newMemory.importance}
                onChange={(e) => setNewMemory({ ...newMemory, importance: Number(e.target.value) })}
              />
            </div>
            <div className="form-group">
              <label>Metadata (JSON):</label>
              <input
                type="text"
                value={JSON.stringify(newMemory.metadata)}
                onChange={(e) => {
                  try {
                    setNewMemory({ ...newMemory, metadata: JSON.parse(e.target.value) });
                  } catch {
                    // Ignore invalid JSON
                  }
                }}
                placeholder="{}"
              />
            </div>
            <button onClick={createMemory}>Create Memory</button>
          </div>
        </div>
      </GlassCard>

      {/* Memories List */}
      <GlassCard title="Memories">
        <div className="memories-list">
          {filteredMemories.length ? (
            filteredMemories.map((memory) => (
              <div key={memory.memory_id} className="memory-card">
                <div className="memory-header">
                  <StatusBadge status={getKindColor(memory.kind)}>{memory.kind}</StatusBadge>
                  <span className="memory-importance">
                    Importance: {memory.importance.toFixed(2)}
                  </span>
                  <button onClick={() => deleteMemory(memory.memory_id)} className="danger">
                    Delete
                  </button>
                </div>
                <div className="memory-content">
                  <p>{memory.content}</p>
                </div>
                <div className="memory-meta">
                  <small>
                    Created: {new Date(memory.created_at).toLocaleString()} | 
                    Updated: {new Date(memory.updated_at).toLocaleString()}
                  </small>
                </div>
                {memory.metadata && Object.keys(memory.metadata).length > 0 && (
                  <div className="memory-metadata">
                    <details>
                      <summary>Metadata</summary>
                      <pre>{JSON.stringify(memory.metadata, null, 2)}</pre>
                    </details>
                  </div>
                )}
              </div>
            ))
          ) : (
            <p>No memories match the filters.</p>
          )}
        </div>
      </GlassCard>

      {/* Memory Rules */}
      <GlassCard title="Memory Rules">
        <div className="memory-rules">
          <h3>🧠 Memory Types:</h3>
          <ul>
            <li>
              <StatusBadge status="info">Episodic</StatusBadge>: Event-based memories (e.g., "I ran a task at 10:00 AM").
            </li>
            <li>
              <StatusBadge status="success">Semantic</StatusBadge>: Fact-based memories (e.g., "The capital of France is Paris").
            </li>
            <li>
              <StatusBadge status="warning">Procedural</StatusBadge>: Process-based memories (e.g., "To solve X, follow steps Y and Z").
            </li>
          </ul>

          <h3>📝 Memory Management:</h3>
          <ul>
            <li>✓ Memories are <strong>stored in SQLite</strong>.</li>
            <li>✓ Memories are <strong>searchable</strong> by content, kind, and importance.</li>
            <li>✓ Memories are <strong>used by the agent</strong> for learning and recall.</li>
            <li>✓ Memories can be <strong>manually created and deleted</strong>.</li>
          </ul>

          <h3>🎯 Importance:</h3>
          <ul>
            <li><strong>0.0 - 0.3:</strong> Low importance (rarely recalled).</li>
            <li><strong>0.4 - 0.6:</strong> Medium importance (sometimes recalled).</li>
            <li><strong>0.7 - 1.0:</strong> High importance (always recalled).</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

// Helper function
function getKindColor(kind: string): string {
  switch (kind.toLowerCase()) {
    case 'episodic':
      return 'info';
    case 'semantic':
      return 'success';
    case 'procedural':
      return 'warning';
    default:
      return 'neutral';
  }
}

export default MemoryPage;
