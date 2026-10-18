import { spawnSync } from "node:child_process";

const checks = [
  ["lint", ["run", "lint", "--", "--quiet"]],
  ["typecheck", ["run", "typecheck"]],
  ["build", ["run", "build"]],
];

for (const [name, args] of checks) {
  console.log(`\nponytail: running ${name}`);
  const result = spawnSync("npm", args, { stdio: "inherit" });
  if (result.status !== 0) {
    console.error(`\nponytail: ${name} failed`);
    process.exit(result.status ?? 1);
  }
}

console.log("\nponytail: all quality checks passed");
