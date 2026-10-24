const GRAPH_STATS = {
  "node_count": 1163,
  "edge_count": 2761,
  "skill_count": 41,
  "agent_count": 3,
  "community_count": 94,
  "god_nodes": [
    {
      "label": "create_app()",
      "degree": 52
    },
    {
      "label": "execute()",
      "degree": 50
    },
    {
      "label": "Config",
      "degree": 48
    },
    {
      "label": "init_db()",
      "degree": 43
    },
    {
      "label": "run_loop()",
      "degree": 40
    },
    {
      "label": "resume_loop()",
      "degree": 34
    },
    {
      "label": "ExecuteRequest",
      "degree": 30
    },
    {
      "label": "build_index()",
      "degree": 27
    }
  ],
  "surprising": [
    {
      "source": "DaemonTests",
      "target": "Config",
      "relation": "uses"
    },
    {
      "source": "LoopSessionTests",
      "target": "Config",
      "relation": "uses"
    },
    {
      "source": "McpTests",
      "target": "Config",
      "relation": "uses"
    },
    {
      "source": "run_once()",
      "target": "execute()",
      "relation": "calls"
    },
    {
      "source": "InstinctV2Tests",
      "target": "PlanRequest",
      "relation": "uses"
    }
  ]
};
