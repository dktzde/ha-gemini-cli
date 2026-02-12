import { writeFileSync, unlinkSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

let projectRoot: string | null = null;

export function findProjectRoot(): string {
  if (projectRoot) return projectRoot;

  let dir = resolve(process.cwd());
  while (dir !== '/') {
    if (existsSync(join(dir, '.claude'))) {
      projectRoot = dir;
      return dir;
    }
    dir = resolve(dir, '..');
  }

  // Fallback to cwd
  projectRoot = process.cwd();
  return projectRoot;
}

export function getProjectRoot(): string {
  return projectRoot ?? findProjectRoot();
}

export function writePortFile(port: number): void {
  const root = getProjectRoot();
  writeFileSync(join(root, '.hass-docs-port'), String(port), 'utf-8');
}

export function writePidFile(): void {
  const root = getProjectRoot();
  writeFileSync(join(root, '.hass-docs-pid'), String(process.pid), 'utf-8');
}

function removeFile(path: string): void {
  try {
    unlinkSync(path);
  } catch {
    // File may already be gone
  }
}

export function cleanup(): void {
  const root = getProjectRoot();
  removeFile(join(root, '.hass-docs-port'));
  removeFile(join(root, '.hass-docs-pid'));
  console.log('Cleaned up port and PID files.');
}

// Register shutdown handlers
process.on('SIGTERM', () => {
  cleanup();
  process.exit(0);
});

process.on('SIGINT', () => {
  cleanup();
  process.exit(0);
});
