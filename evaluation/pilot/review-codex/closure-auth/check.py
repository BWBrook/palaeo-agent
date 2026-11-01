"""Read-only subscription status comparison; never print or save identity or tokens."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from evaluation.pilot.launch import verify_config_dir


def main():
    config = Path.home() / "palaeo-eval/claude-pilot-config"
    observations = []
    for mode in ("normal_home", "fresh_home"):
        with tempfile.TemporaryDirectory(prefix="pilot-auth-status-") as temporary:
            env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin",
                   "HOME": os.environ["HOME"] if mode == "normal_home" else temporary,
                   "USER": os.environ["USER"], "CLAUDE_CONFIG_DIR": str(config),
                   "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1",
                   "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
            result = subprocess.run([shutil.which("claude"), "auth", "status", "--json"],
                                    env=env, capture_output=True, text=True, timeout=30)
            status = json.loads(result.stdout or "{}")
            observations.append({"mode": mode, "exit_code": result.returncode,
                                 **{k: status.get(k) for k in
                                    ("loggedIn", "authMethod", "subscriptionType", "apiProvider")}})
    verify_config_dir(config)
    receipt = {"reviewed_commit": "2cbe7185d16093b0793e82ccb8f740a4b8df6354",
               "execution": "Native local process outside the nested tool sandbox, allowing Keychain access.",
               "config_dir": str(config), "configuration_hygiene": "passed",
               "observations": observations, "inference_calls": 0,
               "secrets_or_identity_retained": False,
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"configuration_hygiene": "passed", "observations": observations}))


if __name__ == "__main__":
    main()
