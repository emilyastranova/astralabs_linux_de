# AstraLabs: show the system summary when a new terminal opens.
# Installed to ~/.bashrc.d/, which Fedora's default ~/.bashrc loads.

[[ $- == *i* ]] || return 0                          # interactive shells only
[[ -n "${ASTRALABS_FETCH_SHOWN:-}" ]] && return 0    # once per terminal, not in nested shells
export ASTRALABS_FETCH_SHOWN=1
[[ "${TERM_PROGRAM:-}" == vscode ]] && return 0      # keep editor terminals clean
command -v astralabs-fetch >/dev/null && command -v fastfetch >/dev/null && astralabs-fetch
