const GRAPH_STATS = {
  "node_count": 555,
  "edge_count": 898,
  "skill_count": 31,
  "agent_count": 3,
  "community_count": 54,
  "god_nodes": [
    {
      "label": "create_app()",
      "degree": 21
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
      "label": "files",
      "degree": 13
    },
    {
      "label": "instructions",
      "degree": 12
    },
    {
      "label": "get_index_cached()",
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
      "source": "_pick_skill()",
      "target": "Config",
      "relation": "references"
    }
  ]
};
