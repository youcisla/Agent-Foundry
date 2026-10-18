const GRAPH_STATS = {
  "node_count": 911,
  "edge_count": 1860,
  "skill_count": 39,
  "agent_count": 3,
  "community_count": 71,
  "god_nodes": [
    {
      "label": "Config",
      "degree": 51
    },
    {
      "label": "PolicyAction",
      "degree": 36
    },
    {
      "label": "ExecuteRequest",
      "degree": 34
    },
    {
      "label": "McpServer",
      "degree": 31
    },
    {
      "label": "execute()",
      "degree": 28
    },
    {
      "label": "PlanRequest",
      "degree": 28
    },
    {
      "label": "create_app()",
      "degree": 27
    },
    {
      "label": "build_index()",
      "degree": 25
    },
    {
      "label": "PlannerConfig",
      "degree": 24
    }
  ],
  "surprising": [
    {
      "source": "AttestTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "PolicyTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "AttestTests",
      "target": "Config",
      "relation": "uses"
    },
    {
      "source": "PolicyTests",
      "target": "Config",
      "relation": "uses"
    },
    {
      "source": "AttestTests",
      "target": "McpServer",
      "relation": "uses"
    }
  ]
};
