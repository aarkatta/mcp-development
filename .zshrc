autoload -Uz compinit
compinit -u
export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"
export PATH=~/.npm-global/bin:$PATH

export WASMTIME_HOME="$HOME/.wasmtime"

export PATH="$WASMTIME_HOME/bin:$PATH"

. "$HOME/.local/bin/env"
eval "$(uv generate-shell-completion zsh)"

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/rameshkatta/Documents/AI/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/rameshkatta/Documents/AI/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/rameshkatta/Documents/AI/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/rameshkatta/Documents/AI/google-cloud-sdk/completion.zsh.inc'; fi
