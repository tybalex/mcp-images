#!/usr/bin/env node

const https = require("https");
const { execSync } = require("child_process");

function compareVersions(v1, v2) {
  const parts1 = v1.split(".").map(Number);
  const parts2 = v2.split(".").map(Number);

  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;

    if (part1 > part2) return 1;
    if (part1 < part2) return -1;
  }
  return 0;
}

function fetchPackageInfo(packageName) {
  return new Promise((resolve, reject) => {
    const url = `https://registry.npmjs.org/${packageName}`;

    https
      .get(url, (res) => {
        let data = "";

        res.on("data", (chunk) => {
          data += chunk;
        });

        res.on("end", () => {
          try {
            const packageInfo = JSON.parse(data);
            resolve(packageInfo);
          } catch (error) {
            reject(new Error("Failed to parse package information"));
          }
        });
      })
      .on("error", (error) => {
        reject(error);
      });
  });
}

async function checkVersion(packageName, currentVersion) {
  try {
    const packageInfo = await fetchPackageInfo(packageName);
    const latestVersion = packageInfo["dist-tags"].latest;

    const comparison = compareVersions(latestVersion, currentVersion);

    const result = {
      package: packageName,
      currentVersion: currentVersion,
      latestVersion: latestVersion,
      hasNewerVersion: comparison > 0,
    };

    console.log(JSON.stringify(result, null, 2));

    process.exit(0);
  } catch (error) {
    const errorResult = {
      package: packageName,
      currentVersion: currentVersion,
      error: error.message,
    };
    console.log(JSON.stringify(errorResult, null, 2));
    process.exit(1);
  }
}

function main() {
  const args = process.argv.slice(2);

  if (args.length !== 2) {
    console.error(
      "Usage: node check-npm-version.js <package-name> <current-version>",
    );
    console.error("Example: node check-npm-version.js react 18.0.0");
    process.exit(0);
  }

  const [packageName, currentVersion] = args;

  checkVersion(packageName, currentVersion);
}

if (require.main === module) {
  main();
}
