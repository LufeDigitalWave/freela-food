#!/usr/bin/env node

/**
 * Performance check script — bundle size + metrics
 * Roda após npm run build
 */

const fs = require('fs');
const path = require('path');

function getDirectorySize(dir) {
  let size = 0;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      size += getDirectorySize(filePath);
    } else {
      size += stat.size;
    }
  }
  return size;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

console.log('\n╭─ PERFORMANCE CHECK ────────────────────────────────╮');

const projectDir = path.resolve(__dirname, '..');
const nextDir = path.join(projectDir, '.next');
const staticDir = path.join(nextDir, 'static');
const chunksDir = path.join(staticDir, 'chunks');

if (fs.existsSync(staticDir)) {
  const nextSize = getDirectorySize(nextDir);
  const staticSize = getDirectorySize(staticDir);

  console.log(`│\n│ .next/: ${formatBytes(nextSize)}`);
  console.log(`│ .next/static/: ${formatBytes(staticSize)}`);

  // Top chunks
  if (fs.existsSync(chunksDir)) {
    const chunks = fs.readdirSync(chunksDir)
      .filter(f => f.endsWith('.js'))
      .map(f => ({
        name: f,
        size: fs.statSync(path.join(chunksDir, f)).size
      }))
      .sort((a, b) => b.size - a.size)
      .slice(0, 5);

    console.log(`│\n│ Top 5 chunks:`);
    chunks.forEach((c, i) => {
      console.log(`│ ${i + 1}. ${c.name.substring(0, 30)}: ${formatBytes(c.size)}`);
    });
  }
}

// Metrics from performance-budget.json
const budgetPath = path.join(projectDir, 'performance-budget.json');
if (fs.existsSync(budgetPath)) {
  const budget = JSON.parse(fs.readFileSync(budgetPath, 'utf-8'));
  console.log(`│\n│ Performance Budget Targets:`);
  if (budget.thresholds) {
    console.log(`│ FCP: ${budget.thresholds.FCP}ms`);
    console.log(`│ LCP: ${budget.thresholds.LCP}ms`);
    console.log(`│ CLS: ${budget.thresholds.CLS}`);
  }
}

console.log(`│\n╰────────────────────────────────────────────────────╯\n`);

// Exit code 0 (no limits enforced yet; just informational)
process.exit(0);
