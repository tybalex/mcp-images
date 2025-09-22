#!/usr/bin/env python3

import sys
import json
import subprocess
import re
from packaging import version


def parse_image_name(image_name):
    """Parse Docker image name to extract registry, repository, and current tag"""
    if ':' not in image_name:
        raise Exception("Image name must include a tag (e.g., nginx:1.21)")

    image_part, current_tag = image_name.rsplit(':', 1)

    # Determine registry and repository
    if image_part.startswith('ghcr.io/'):
        registry = 'ghcr'
        repository = image_part
    elif image_part.startswith('docker.io/'):
        registry = 'dockerhub'
        repository = image_part
    elif '/' in image_part and '.' in image_part.split('/')[0]:
        # Custom registry
        registry = 'custom'
        repository = image_part
    else:
        # Docker Hub without explicit registry
        registry = 'dockerhub'
        if '/' not in image_part:
            # Official image, add library/ prefix
            repository = f'library/{image_part}'
        else:
            repository = image_part

    return registry, repository, current_tag


def run_crane_ls(repository):
    """Use crane ls to list tags for a repository"""
    try:
        result = subprocess.run(
            ['crane', 'ls', repository],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if 'not found' in stderr.lower() or '404' in stderr:
                raise Exception(f"Repository '{repository}' not found")
            elif 'unauthorized' in stderr.lower() or '401' in stderr:
                raise Exception(f"Unauthorized access to repository '{repository}'")
            else:
                raise Exception(f"crane ls failed: {stderr}")

        tags = result.stdout.strip().split('\n')
        return [tag for tag in tags if tag]  # Filter out empty strings

    except subprocess.TimeoutExpired:
        raise Exception("crane ls command timed out")
    except FileNotFoundError:
        raise Exception("crane command not found. Please install crane (go-containerregistry)")
    except Exception as e:
        if "crane ls failed:" in str(e):
            raise e
        else:
            raise Exception(f"Failed to run crane ls: {str(e)}")


def is_version_tag(tag):
    """Check if a tag looks like a version (semantic versioning or numeric)"""
    # Skip common non-version tags
    skip_tags = {
        'latest', 'stable', 'main', 'master', 'dev', 'devel', 'development',
        'test', 'testing', 'staging', 'prod', 'production', 'edge', 'nightly'
    }

    if tag.lower() in skip_tags:
        return False

    # Skip tags that end with common suffixes but aren't versions
    if re.match(r'^(latest|stable|main|master)-', tag, re.IGNORECASE):
        return False

    # Match patterns like: 1.21, v1.21.0, 1.21.0-alpine, 2.0.0-rc1
    version_patterns = [
        r'^v?\d+(\.\d+)*(-[\w\.-]+)?$',  # v1.21.0, 1.21, 1.21.0-alpine
        r'^\d+(\.\d+)*$',               # 1.21, 1.21.0
        r'^\d{4}-\d{2}-\d{2}$',         # 2024-01-15 (date format)
        r'^\d+$',                       # Simple numeric tags like 20, 21
    ]

    for pattern in version_patterns:
        if re.match(pattern, tag):
            return True
    return False


def normalize_version(tag):
    """Normalize version tag for comparison"""
    # Remove 'v' prefix if present
    if tag.startswith('v'):
        tag = tag[1:]

    # Handle date formats
    if re.match(r'^\d{4}-\d{2}-\d{2}$', tag):
        return tag  # Keep date format as is

    # Split on '-' to separate version from suffix (like -alpine)
    version_part = tag.split('-')[0]

    try:
        # Try to parse as version
        version.parse(version_part)
        return version_part
    except version.InvalidVersion:
        # If it's a simple number, treat as version
        if re.match(r'^\d+$', version_part):
            return version_part + '.0.0'  # Convert to semantic version
        return None


def find_latest_version(tags, current_tag):
    """Find the latest version from a list of tags"""
    version_tags = []

    for tag in tags:
        if is_version_tag(tag):
            normalized = normalize_version(tag)
            if normalized:
                version_tags.append((tag, normalized))

    if not version_tags:
        raise Exception("No version tags found in repository")

    # Sort by version
    try:
        def version_key(item):
            tag, norm = item
            # Handle date format specially
            if re.match(r'^\d{4}-\d{2}-\d{2}$', norm):
                return norm  # Date strings sort naturally
            return version.parse(norm)

        sorted_tags = sorted(version_tags, key=version_key, reverse=True)
        return sorted_tags[0][0]  # Return the original tag of the highest version
    except version.InvalidVersion as e:
        raise Exception(f"Invalid version format found: {str(e)}")


def compare_versions(v1, v2):
    """Compare two version strings"""
    try:
        norm_v1 = normalize_version(v1)
        norm_v2 = normalize_version(v2)

        if not norm_v1 or not norm_v2:
            raise Exception("Unable to normalize versions for comparison")

        # Handle date format comparison
        if re.match(r'^\d{4}-\d{2}-\d{2}$', norm_v1) and re.match(r'^\d{4}-\d{2}-\d{2}$', norm_v2):
            if norm_v1 > norm_v2:
                return 1
            elif norm_v1 < norm_v2:
                return -1
            else:
                return 0

        version1 = version.parse(norm_v1)
        version2 = version.parse(norm_v2)

        if version1 > version2:
            return 1
        elif version1 < version2:
            return -1
        else:
            return 0
    except version.InvalidVersion as e:
        raise Exception(f"Invalid version format: {str(e)}")


def check_version(image_name):
    """Check if a newer version is available for a Docker image"""
    try:
        registry, repository, current_tag = parse_image_name(image_name)

        # Use crane ls to get all tags
        tags = run_crane_ls(repository)

        if not tags:
            raise Exception("No tags found in repository")

        latest_tag = find_latest_version(tags, current_tag)

        comparison = compare_versions(latest_tag, current_tag)

        result = {
            "image": image_name,
            "repository": repository,
            "currentTag": current_tag,
            "latestTag": latest_tag,
            "hasNewerVersion": comparison > 0,
        }

        print(json.dumps(result, indent=2))

        if comparison > 0:
            sys.exit(0)  # Newer version available
        else:
            sys.exit(1)  # No newer version

    except Exception as error:
        registry, repository, current_tag = None, None, None
        try:
            registry, repository, current_tag = parse_image_name(image_name)
        except:
            pass

        error_result = {
            "image": image_name,
            "registry": registry,
            "repository": repository,
            "currentTag": current_tag,
            "error": str(error)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python check-docker-version.py <image:tag>", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python check-docker-version.py nginx:1.21", file=sys.stderr)
        print("  python check-docker-version.py ghcr.io/owner/repo:v1.0.0", file=sys.stderr)
        print("  python check-docker-version.py docker.io/library/postgres:13.0", file=sys.stderr)
        print("", file=sys.stderr)
        print("Note: This script requires 'crane' to be installed.", file=sys.stderr)
        print("Install with: go install github.com/google/go-containerregistry/cmd/crane@latest", file=sys.stderr)
        sys.exit(1)

    image_name = sys.argv[1]
    check_version(image_name)


if __name__ == "__main__":
    main()
