const INSTALL_COMMANDS = {
  "core": "curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "coreProfile": "AF_PROFILE=core curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "fullProfile": "AF_PROFILE=full curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "minimalProfile": "AF_PROFILE=minimal curl -fsSL https://raw.githubusercontent.com/youcisla/Agent-Foundry/main/install.sh | bash",
  "gitClone": "git clone https://github.com/youcisla/Agent-Foundry.git ~/.agent-foundry && cd ~/.agent-foundry && pip install -e .",
  "claudeCode": "/plugin marketplace add youcisla/Agent-Foundry\n/plugin install agent-foundry",
  "npm": "npm i -g agent-foundry"
};
