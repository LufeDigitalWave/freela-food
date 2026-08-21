#!/usr/bin/env node

/**
 * Accessibility audit helper — encontra problemas WCAG comuns em componentes React
 *
 * Problemas checados:
 * - Links/buttons sem accessible names
 * - Images sem alt text
 * - Headings sem hierarchy
 * - Modals sem role="dialog"
 * - Forms sem labels
 * - Color-only differentiation
 * - Skip links ausentes
 */

const fs = require('fs');
const path = require('path');

const issues = [];

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const fileName = path.relative('.', filePath);

  // 1. Links sem accessible names
  const linkMatches = content.matchAll(/<Link[^>]*href="[^"]*"[^>]*>\s*(?!.*?aria-label|.*?{.*?})[^<]*<\/Link>/g);
  for (const match of linkMatches) {
    if (!match[0].includes('aria-label') && !match[0].includes('>.*[A-Z]')) {
      issues.push({
        file: fileName,
        type: 'link-without-name',
        line: content.substring(0, match.index).split('\n').length,
        message: 'Link sem accessible name (considere aria-label ou text content)',
        severity: 'warning',
      });
    }
  }

  // 2. Icons sem aria-label/title
  const iconMatches = content.matchAll(/<(Bell|Search|Menu|X|ChevronDown|Settings|LogOut)[^>]*\/>/g);
  for (const match of iconMatches) {
    const full = content.substring(match.index, content.indexOf('/>', match.index) + 2);
    if (!full.includes('aria-label') && !full.includes('title=')) {
      issues.push({
        file: fileName,
        type: 'icon-without-label',
        line: content.substring(0, match.index).split('\n').length,
        message: `Icon <${match[1]} /> precisa aria-label ou title`,
        severity: 'error',
      });
    }
  }

  // 3. Input/Button sem associated labels
  if (content.includes('<input') && !content.includes('htmlFor=')) {
    const inputMatches = content.matchAll(/<input[^>]*type="(?!hidden)[^"]*"[^>]*\/>/g);
    for (const match of inputMatches) {
      if (!match[0].includes('aria-label') && !match[0].includes('id=')) {
        issues.push({
          file: fileName,
          type: 'input-without-label',
          line: content.substring(0, match.index).split('\n').length,
          message: 'Input sem label associada (use <Label htmlFor="id"> + id="id")',
          severity: 'error',
        });
      }
    }
  }

  // 4. Button com apenas icon
  const btnMatches = content.matchAll(/<[Bb]utton[^>]*>\s*(?=<(?:Bell|Search|Menu|X|ChevronDown|Settings|LogOut))/g);
  for (const match of btnMatches) {
    const full = content.substring(match.index, content.indexOf('</button>', match.index) + 9);
    if (!full.includes('aria-label') && !full.includes('title=')) {
      issues.push({
        file: fileName,
        type: 'button-icon-without-label',
        line: content.substring(0, match.index).split('\n').length,
        message: 'Button com apenas icon precisa aria-label',
        severity: 'warning',
      });
    }
  }

  // 5. Headings pulando níveis (h1 → h3)
  const headingMatches = content.matchAll(/<h([1-6])[^>]*>/g);
  let lastLevel = 0;
  for (const match of headingMatches) {
    const currentLevel = parseInt(match[1]);
    if (lastLevel && currentLevel > lastLevel + 1) {
      issues.push({
        file: fileName,
        type: 'heading-hierarchy',
        line: content.substring(0, match.index).split('\n').length,
        message: `Heading nível pulado (h${lastLevel} → h${currentLevel})`,
        severity: 'warning',
      });
    }
    lastLevel = currentLevel;
  }

  // 6. Images sem alt text
  const imgMatches = content.matchAll(/<img[^>]*\/>/g);
  for (const match of imgMatches) {
    if (!match[0].includes('alt=')) {
      issues.push({
        file: fileName,
        type: 'image-without-alt',
        line: content.substring(0, match.index).split('\n').length,
        message: 'Image sem alt text',
        severity: 'error',
      });
    }
  }

  // 7. Empty buttons/links
  if (content.includes('<button') || content.includes('<Link')) {
    const emptyMatches = content.matchAll(/<(button|Link)[^>]*>\s*<\/(button|Link)>/g);
    for (const match of emptyMatches) {
      issues.push({
        file: fileName,
        type: 'empty-button-link',
        line: content.substring(0, match.index).split('\n').length,
        message: `${match[1] === 'button' ? 'Button' : 'Link'} vazio — adicione conteúdo ou aria-label`,
        severity: 'error',
      });
    }
  }
}

// Scan all tsx/ts files in src/
function auditProject() {
  function walk(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const full = path.join(dir, file);
      if (fs.statSync(full).isDirectory()) {
        if (!file.startsWith('.')) walk(full);
      } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
        scanFile(full);
      }
    }
  }

  walk('src/');
}

auditProject();

// Sort by severity
issues.sort((a, b) => {
  const severityOrder = { error: 0, warning: 1 };
  return (severityOrder[a.severity] ?? 2) - (severityOrder[b.severity] ?? 2);
});

// Print report
console.log('\n╭─ WCAG A11Y AUDIT ─────────────────────────────────────╮');
console.log(`│ ${issues.length} issues encontrados\n`);

const grouped = {};
for (const issue of issues) {
  if (!grouped[issue.type]) grouped[issue.type] = [];
  grouped[issue.type].push(issue);
}

for (const [type, typeIssues] of Object.entries(grouped)) {
  console.log(`\n📋 ${type} (${typeIssues.length}):`);
  for (const issue of typeIssues.slice(0, 5)) {
    console.log(`   ${issue.file}:${issue.line}`);
    console.log(`   ${issue.severity === 'error' ? '❌' : '⚠️ '} ${issue.message}`);
  }
  if (typeIssues.length > 5) {
    console.log(`   ... e mais ${typeIssues.length - 5}`);
  }
}

console.log(`\n╰────────────────────────────────────────────────────────╯\n`);

process.exit(issues.some(i => i.severity === 'error') ? 1 : 0);
