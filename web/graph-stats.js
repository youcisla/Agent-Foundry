const GRAPH_STATS = {
  "node_count": 287,
  "edge_count": 467,
  "skill_count": 30,
  "agent_count": 2,
  "community_count": 27,
  "god_nodes": [
    {
      "label": "create_app()",
      "degree": 15
    },
    {
      "label": "Config",
      "degree": 14
    },
    {
      "label": "run_loop()",
      "degree": 14
    },
    {
      "label": "build_index()",
      "degree": 12
    },
    {
      "label": "get_index_cached()",
      "degree": 12
    },
    {
      "label": "TokenEstimate",
      "degree": 12
    },
    {
      "label": "rank_skills()",
      "degree": 12
    },
    {
      "label": "SkillIndex",
      "degree": 11
    },
    {
      "label": "execute()",
      "degree": 10
    },
    {
      "label": "plan()",
      "degree": 10
    }
  ],
  "surprising": [
    {
      "source": "estimate_judge_cost()",
      "target": "TokenEstimate",
      "relation": "references"
    },
    {
      "source": "cmd_cost_report()",
      "target": "get_index_cached()",
      "relation": "calls"
    },
    {
      "source": "cmd_consult()",
      "target": "read_index()",
      "relation": "calls"
    },
    {
      "source": "_pick_skill()",
      "target": "Config",
      "relation": "references"
    },
    {
      "source": "run_loop()",
      "target": "Config",
      "relation": "references"
    }
  ]
};
