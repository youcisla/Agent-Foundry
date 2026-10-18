const INSTALL_COMMANDS = {
  "core": "curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "coreProfile": "AF_PROFILE=core curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "fullProfile": "AF_PROFILE=full curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "minimalProfile": "AF_PROFILE=minimal curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "gitClone": "git clone https://github.com/youcisla/Agent-Foundry.git && cd Agent-Foundry && pip install -e . && node scripts/install.js --harness=claude-code",
  "claudeCode": "/plugin marketplace add youcisla/Agent-Foundry\n/plugin install agent-foundry",
  "npm": "npm install -g @youcisla/agent-foundry",
  "pypi": "pip install agent-foundry-runtime",
  "mcp": "uvx agent-foundry-runtime mcp",
  "mcpRegistry": "io.github.youcisla/agent-foundry"
};
