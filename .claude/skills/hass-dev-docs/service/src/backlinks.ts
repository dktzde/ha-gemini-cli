import { getDb } from './db.js';
import type { Link } from './types.js';

export function getBacklinks(filePath: string): Link[] {
  const db = getDb();
  return db.prepare(`
    SELECT id, source_file, target_file, link_text, section
    FROM links
    WHERE target_file = ?
  `).all(filePath) as Link[];
}

export function getOutgoingLinks(filePath: string): Link[] {
  const db = getDb();
  return db.prepare(`
    SELECT id, source_file, target_file, link_text, section
    FROM links
    WHERE source_file = ?
  `).all(filePath) as Link[];
}
