const GRAPH_STATS = {
  "node_count": 766,
  "edge_count": 1394,
  "skill_count": 35,
  "agent_count": 3,
  "community_count": 75,
  "god_nodes": [
    {
      "label": "Config",
      "degree": 36
    },
    {
      "label": "create_app()",
      "degree": 26
    },
    {
      "label": "build_index()",
      "degree": 23
    },
    {
      "label": "PlanRequest",
      "degree": 21
    },
    {
      "label": "McpServer",
      "degree": 19
    },
    {
      "label": "rank_skills()",
      "degree": 19
    },
    {
      "label": "PlannerConfig",
      "degree": 18
    },
    {
      "label": "run_loop()",
      "degree": 18
    }
  ],
  "surprising": [
    {
      "source": "DaemonTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "EvalVerifyTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "IntegrityTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "LoopSessionTests",
      "target": "PlannerConfig",
      "relation": "uses"
    },
    {
      "source": "McpTests",
      "target": "PlannerConfig",
      "relation": "uses"
    }
  ]
};
