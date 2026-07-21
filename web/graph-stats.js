const GRAPH_STATS = {
  "node_count": 499,
  "edge_count": 831,
  "skill_count": 30,
  "agent_count": 3,
  "community_count": 49,
  "god_nodes": [
    {
      "label": "create_app()",
      "degree": 20
    },
    {
      "label": "html",
      "degree": 20
    },
    {
      "label": "build_index()",
      "degree": 16
    },
    {
      "label": "useStore()",
      "degree": 16
    },
    {
      "label": "Config",
      "degree": 15
    },
    {
      "label": "run_loop()",
      "degree": 14
    },
    {
      "label": "rank_skills()",
      "degree": 14
    },
    {
      "label": "instructions",
      "degree": 12
    },
    {
      "label": "get_index_cached()",
      "degree": 12
    },
    {
      "label": "TokenEstimate",
      "degree": 12
    }
  ],
  "surprising": [
    {
      "source": "load_indexer()",
      "target": "SkillManifest",
      "relation": "indirect_call"
    },
    {
      "source": "load_indexer()",
      "target": "build_index()",
      "relation": "indirect_call"
    },
    {
      "source": "check_frontmatter()",
      "target": "build_index()",
      "relation": "calls"
    },
    {
      "source": "check_indexer()",
      "target": "build_index()",
      "relation": "calls"
    },
    {
      "source": "_ensure_daemon()",
      "target": "Config",
      "relation": "references"
    }
  ]
};
