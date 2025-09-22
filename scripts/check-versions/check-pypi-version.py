#!/usr/bin/env python3

import sys
import json
import urllib.request
import urllib.error
from packaging import version


def fetch_package_info(package_name):
    """Fetch package information from PyPI API"""
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Exception(f"Package '{package_name}' not found on PyPI")
        else:
            raise Exception(f"HTTP error {e.code}: {e.reason}")
    except Exception as e:
        raise Exception(f"Failed to fetch package information: {str(e)}")


def compare_versions(v1, v2):
    """Compare two version strings using packaging library"""
    try:
        version1 = version.parse(v1)
        version2 = version.parse(v2)

        if version1 > version2:
            return 1
        elif version1 < version2:
            return -1
        else:
            return 0
    except version.InvalidVersion as e:
        raise Exception(f"Invalid version format: {str(e)}")


def check_version(package_name, current_version):
    """Check if a newer version is available"""
    try:
        package_info = fetch_package_info(package_name)
        latest_version = package_info['info']['version']

        comparison = compare_versions(latest_version, current_version)

        result = {
            "package": package_name,
            "currentVersion": current_version,
            "latestVersion": latest_version,
            "hasNewerVersion": comparison > 0,
        }

        print(json.dumps(result, indent=2))

        if comparison > 0:
            sys.exit(0)  # Newer version available
        else:
            sys.exit(1)  # No newer version

    except Exception as error:
        error_result = {
            "package": package_name,
            "currentVersion": current_version,
            "error": str(error)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python check-pypi-version.py <package-name> <current-version>", file=sys.stderr)
        print("Example: python check-pypi-version.py requests 2.28.0", file=sys.stderr)
        sys.exit(1)

    package_name = sys.argv[1]
    current_version = sys.argv[2]

    check_version(package_name, current_version)


if __name__ == "__main__":
    main()
