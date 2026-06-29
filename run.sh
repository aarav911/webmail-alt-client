#!/usr/bin/env bash

# ------------------------------------------------------------------
# Script Name: script_name.sh
# Description: A boilerplate Bash script with best practices.
# ------------------------------------------------------------------

# 1. Safety Flags
# ------------------------------------------------------------------
set -euo pipefail  # Exit on error, undefined vars, or pipe failures
IFS=$'\n\t'        # Safe internal field separator

# 2. Variables
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"
VERSION="1.0.0"

# 3. Helper Functions
# ------------------------------------------------------------------
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS] [ARGUMENTS]

Options:
    -h, --help      Show this help message
    -v, --version   Show version number
    -d, --debug     Enable debug mode

Examples:
    $SCRIPT_NAME -d input.txt
EOF
    exit 0
}

log_info() {
    echo "[INFO] $*"
}

log_error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# 4. Main Logic
# ------------------------------------------------------------------
main() {
    local debug=false

    # Parse Arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                ;;
            -v|--version)
                echo "$SCRIPT_NAME version $VERSION"
                exit 0
                ;;
            -d|--debug)
                debug=true
                shift
                ;;
            *)
                # Handle positional arguments here
                log_info "Processing argument: $1"
                shift
                ;;
        esac
    done

    if [[ "$debug" == true ]]; then
        set -x # Enable command tracing
        log_info "Debug mode enabled"
    fi

    log_info "Script started successfully from: $SCRIPT_DIR"
    
    # --- Your Code Here ---
    cd dist
    ./Webmail
    # ----------------------

    log_info "Script finished."
}

# 5. Entry Point
# ------------------------------------------------------------------
main "$@"   