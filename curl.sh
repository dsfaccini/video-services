#!/usr/bin/env bash
# API interaction script for video-services

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default API base URL
API_BASE="${API_BASE:-http://localhost:8000}"

# Helper functions
function print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function print_json() {
    if command -v jq &> /dev/null; then
        echo "$1" | jq .
    else
        echo "$1" | python -m json.tool 2>/dev/null || echo "$1"
    fi
}

# Check if API is running
function check_api() {
    print_header "Checking API health"
    
    if response=$(curl -s -f "${API_BASE}/health" 2>/dev/null); then
        print_success "API is healthy"
        print_json "$response"
        return 0
    else
        print_error "API is not responding at ${API_BASE}"
        return 1
    fi
}

# Get API info
function info() {
    print_header "Getting API information"
    
    if response=$(curl -s -f "${API_BASE}/" 2>/dev/null); then
        print_json "$response"
    else
        print_error "Failed to get API info"
        return 1
    fi
}

# Extract video URL from social media post
function extract_url() {
    local post_url="$1"
    
    print_header "Extracting video URL"
    echo "Post URL: $post_url"
    echo ""
    
    local payload
    payload=$(jq -n --arg url "$post_url" '{url: $url}')
    
    if response=$(curl -s -X POST "${API_BASE}/api/video/extract-url" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null); then
        
        if echo "$response" | jq -e .detail >/dev/null 2>&1; then
            print_error "API Error:"
            print_json "$response"
            return 1
        else
            print_success "Video URL extracted"
            print_json "$response"
        fi
    else
        print_error "Failed to extract video URL"
        return 1
    fi
}

# Clip video and save to file
function clip_video() {
    local video_url="$1"
    local start_time="$2"
    local end_time="$3"
    local output_file="${4:-clipped_video.mp4}"
    
    print_header "Clipping video"
    echo "Video URL: $video_url"
    echo "Start time: ${start_time}s"
    echo "End time: ${end_time}s"
    echo "Output file: $output_file"
    echo ""
    
    local payload
    payload=$(jq -n --arg url "$video_url" --arg start "$start_time" --arg end "$end_time" \
        '{url: $url, start_time: ($start | tonumber), end_time: ($end | tonumber)}')
    
    if curl -s -X POST "${API_BASE}/api/video/clip" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        -o "$output_file" 2>/dev/null; then
        
        if [[ -f "$output_file" && $(stat -c%s "$output_file" 2>/dev/null || stat -f%z "$output_file" 2>/dev/null) -gt 100 ]]; then
            print_success "Video clipped and saved to $output_file"
            local size
            size=$(ls -lh "$output_file" | awk '{print $5}')
            echo "File size: $size"
        else
            print_error "Clipping failed or resulted in empty file"
            # Try to read error response
            if [[ -f "$output_file" ]]; then
                local error_content
                error_content=$(cat "$output_file")
                if echo "$error_content" | jq . >/dev/null 2>&1; then
                    print_json "$error_content"
                fi
                rm -f "$output_file"
            fi
            return 1
        fi
    else
        print_error "Failed to clip video"
        return 1
    fi
}

# Test with sample URLs
function test_extract() {
    print_header "Testing video URL extraction with sample URLs"
    
    local test_urls=(
        "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/"
    )
    
    for url in "${test_urls[@]}"; do
        echo ""
        echo "Testing: $url"
        if extract_url "$url"; then
            print_success "Test passed"
        else
            print_warning "Test failed (might be expected for some platforms)"
        fi
        echo "---"
    done
}

# Full workflow test
function test_workflow() {
    print_header "Testing full workflow"
    
    local test_url="https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    echo "Step 1: Extract video URL"
    if response=$(curl -s -X POST "${API_BASE}/api/video/extract-url" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$test_url\"}" 2>/dev/null); then
        
        if video_url=$(echo "$response" | jq -r .video_url 2>/dev/null); then
            print_success "Extracted video URL"
            echo "Video URL: $video_url"
            
            echo ""
            echo "Step 2: Clip video (first 5 seconds)"
            if clip_video "$video_url" "0" "5" "test_clip.mp4"; then
                print_success "Full workflow completed successfully"
            else
                print_error "Clipping step failed"
                return 1
            fi
        else
            print_error "Failed to parse video URL from response"
            print_json "$response"
            return 1
        fi
    else
        print_error "Failed to extract video URL"
        return 1
    fi
}

# Set API base URL
function set_url() {
    local url="$1"
    export API_BASE="$url"
    print_success "API base URL set to: $API_BASE"
}

# Show help
function help() {
    echo "Video Services API Client"
    echo ""
    echo "Usage: ./curl.sh [command] [arguments]"
    echo ""
    echo "Commands:"
    echo "  check                        Check API health"
    echo "  info                         Get API information"
    echo "  extract-url <post_url>       Extract video URL from social media post"
    echo "  clip <video_url> <start> <end> [output_file]  Clip video between timestamps"
    echo "  test-extract                 Test extraction with sample URLs"
    echo "  test-workflow                Test full extract + clip workflow"
    echo "  set-url <base_url>           Set API base URL (default: http://localhost:8000)"
    echo "  help                         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./curl.sh check"
    echo "  ./curl.sh extract-url \"https://x.com/user/status/123\""
    echo "  ./curl.sh clip \"https://example.com/video.mp4\" 10 30 my_clip.mp4"
    echo "  ./curl.sh set-url \"https://api.example.com\""
    echo ""
    echo "Environment Variables:"
    echo "  API_BASE                     API base URL (default: http://localhost:8000)"
}

# Main script logic
if [ $# -eq 0 ]; then
    help
    exit 0
fi

# Parse command and execute
case "$1" in
    check)
        check_api
        ;;
    info)
        info
        ;;
    extract-url)
        if [ $# -lt 2 ]; then
            print_error "Usage: extract-url <post_url>"
            exit 1
        fi
        extract_url "$2"
        ;;
    clip)
        if [ $# -lt 4 ]; then
            print_error "Usage: clip <video_url> <start_time> <end_time> [output_file]"
            exit 1
        fi
        clip_video "$2" "$3" "$4" "${5:-clipped_video.mp4}"
        ;;
    test-extract)
        test_extract
        ;;
    test-workflow)
        test_workflow
        ;;
    set-url)
        if [ $# -lt 2 ]; then
            print_error "Usage: set-url <base_url>"
            exit 1
        fi
        set_url "$2"
        ;;
    help)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        help
        exit 1
        ;;
esac