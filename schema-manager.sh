#!/bin/bash
# Schema management CLI tool for CommonGraph

set -e

BASE_URL="http://localhost:8000"
TOKEN_FILE="/tmp/commongraph_token"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "\n${BLUE}🔧 CommonGraph Schema Manager${NC}"
    echo "=================================="
}

function print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

function login() {
    echo -e "\n${BLUE}🔐 Admin Login${NC}"
    echo -n "Username: "
    read username
    echo -n "Password: "
    read -s password
    echo

    response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$username&password=$password")
    
    token=$(echo "$response" | jq -r '.access_token // empty')
    
    if [ -n "$token" ] && [ "$token" != "null" ]; then
        echo "$token" > "$TOKEN_FILE"
        print_status "Login successful"
        return 0
    else
        print_error "Login failed"
        echo "$response" | jq '.'
        return 1
    fi
}

function get_token() {
    if [ -f "$TOKEN_FILE" ]; then
        cat "$TOKEN_FILE"
    else
        echo ""
    fi
}

function check_status() {
    echo -e "\n${BLUE}📊 Schema Status${NC}"
    echo "----------------"
    
    response=$(curl -s "$BASE_URL/schema/status")
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo "$response" | jq '.'
        
        has_changes=$(echo "$response" | jq -r '.has_changes')
        changes_count=$(echo "$response" | jq -r '.changes')
        
        if [ "$has_changes" = "true" ]; then
            if [ "$changes_count" = "0" ] || [ -z "$changes_count" ]; then
                print_info "Changes detected, but you need admin access to see details"
            else
                print_warning "$changes_count schema changes detected"
            fi
        else
            print_status "No schema changes detected"
        fi
    else
        print_error "Invalid response from server:"
        echo "$response"
        echo ""
        print_info "Server might be down or returning an error"
    fi
}

function check_detailed_status() {
    token=$(get_token)
    if [ -z "$token" ]; then
        print_error "Please login first with: $0 login"
        return 1
    fi
    
    echo -e "\n${BLUE}📊 Detailed Schema Status${NC}"
    echo "-------------------------"
    
    response=$(curl -s "$BASE_URL/schema/status" \
        -H "Authorization: Bearer $token")
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo "$response" | jq '.'
        
        has_changes=$(echo "$response" | jq -r '.has_changes')
        changes=$(echo "$response" | jq -r '.changes | length')
        warnings=$(echo "$response" | jq -r '.warnings | length')
        
        if [ "$has_changes" = "true" ]; then
            print_warning "$changes changes detected"
            if [ "$warnings" -gt 0 ]; then
                print_warning "$warnings warnings found"
            fi
            echo -e "\nUse '$0 apply' to apply these changes"
        else
            print_status "No schema changes detected"
        fi
    else
        print_error "Invalid response from server:"
        echo "$response"
        echo ""
        print_info "Check if you're still logged in or if there's a server error"
    fi
}

function apply_changes() {
    token=$(get_token)
    if [ -z "$token" ]; then
        print_error "Please login first with: $0 login"
        return 1
    fi
    
    echo -e "\n${BLUE}🚀 Applying Schema Changes${NC}"
    echo "----------------------------"
    
    # First check what changes will be applied
    response=$(curl -s "$BASE_URL/schema/status" \
        -H "Authorization: Bearer $token")
    
    has_changes=$(echo "$response" | jq -r '.has_changes')
    if [ "$has_changes" != "true" ]; then
        print_info "No changes to apply"
        return 0
    fi
    
    changes_count=$(echo "$response" | jq -r '.changes | length')
    warnings_count=$(echo "$response" | jq -r '.warnings | length')
    
    echo "About to apply $changes_count changes"
    if [ "$warnings_count" -gt 0 ]; then
        print_warning "$warnings_count warnings detected"
        echo "Changes:"
        echo "$response" | jq -r '.changes[] | "  - \(.type): \(.node_type // .edge_type // .poll // "unknown")"'
        echo ""
        echo "Warnings:"
        echo "$response" | jq -r '.warnings[]' | sed 's/^/  - /'
        echo ""
        echo -n "Continue with warnings? (y/N): "
        read confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            print_info "Cancelled"
            return 0
        fi
        force="?force=true"
    else
        echo "Changes:"
        echo "$response" | jq -r '.changes[] | "  - \(.type): \(.node_type // .edge_type // .poll // "unknown")"'
        echo ""
        echo -n "Apply these changes? (y/N): "
        read confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            print_info "Cancelled"
            return 0
        fi
        force=""
    fi
    
    # Apply the changes
    apply_response=$(curl -s -X POST "$BASE_URL/schema/apply$force" \
        -H "Authorization: Bearer $token")
    
    success=$(echo "$apply_response" | jq -r '.success // false')
    if [ "$success" = "true" ]; then
        new_version=$(echo "$apply_response" | jq -r '.new_version')
        print_status "Schema updated to version $new_version"
    else
        print_error "Failed to apply changes"
        echo "$apply_response" | jq '.'
    fi
}

function show_history() {
    token=$(get_token)
    if [ -z "$token" ]; then
        print_error "Please login first with: $0 login"
        return 1
    fi
    
    echo -e "\n${BLUE}📚 Schema History${NC}"
    echo "------------------"
    
    curl -s "$BASE_URL/schema/history" \
        -H "Authorization: Bearer $token" | \
        jq -r '.[] | "\(.version) - \(.created_at) - Active: \(.is_active)"'
}

function show_migrations() {
    token=$(get_token)
    if [ -z "$token" ]; then
        print_error "Please login first with: $0 login"
        return 1
    fi
    
    echo -e "\n${BLUE}🔄 Migration History${NC}"
    echo "---------------------"
    
    curl -s "$BASE_URL/schema/migrations" \
        -H "Authorization: Bearer $token" | \
        jq -r '.[] | "\(.from_version) → \(.to_version) (\(.migration_type)) by \(.applied_by)"'
}

function show_help() {
    print_header
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  status    - Check schema status (anonymous)"
    echo "  detailed  - Check detailed schema status (admin)"
    echo "  login     - Login as admin user"
    echo "  apply     - Apply pending schema changes (admin)"
    echo "  history   - Show schema version history (admin)"
    echo "  migrations- Show migration history (admin)"
    echo "  help      - Show this help message"
    echo ""
    echo "Workflow:"
    echo "  1. Edit config.yaml"
    echo "  2. Run: $0 status"
    echo "  3. If changes detected: $0 login"
    echo "  4. Run: $0 detailed (to see change details)"
    echo "  5. Run: $0 apply (to apply changes)"
    echo ""
}

# Main script
case "${1:-help}" in
    status)
        print_header
        check_status
        ;;
    detailed)
        print_header
        check_detailed_status
        ;;
    login)
        print_header
        login
        ;;
    apply)
        print_header
        apply_changes
        ;;
    history)
        print_header
        show_history
        ;;
    migrations)
        print_header
        show_migrations
        ;;
    help|*)
        show_help
        ;;
esac
