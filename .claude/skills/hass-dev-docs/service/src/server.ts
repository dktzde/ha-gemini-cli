import express from 'express';
import { join } from 'node:path';
import { initDb, getDb } from './db.js';
import { isReady, warmup } from './embeddings.js';
import { indexDocSet, isIndexing } from './indexer.js';
import { semanticSearch, keywordSearch } from './search.js';
import { getBacklinks, getOutgoingLinks } from './backlinks.js';
import { findProjectRoot, writePortFile, writePidFile, cleanup } from './lifecycle.js';

const app = express();
const startTime = Date.now();

app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    uptime: Math.round((Date.now() - startTime) / 1000),
    embedding_model_ready: isReady(),
    indexing_in_progress: isIndexing(),
  });
});

app.get('/search', async (req, res) => {
  try {
    const q = req.query.q as string;
    if (!q) {
      res.status(400).json({ error: 'Missing query parameter "q"' });
      return;
    }
    const limit = parseInt(req.query.limit as string) || 10;
    const docSet = req.query.doc_set as string | undefined;
    const results = await semanticSearch(q, limit, docSet);
    res.json({ results });
  } catch (err: any) {
    console.error('Search error:', err);
    res.status(500).json({ error: err.message });
  }
});

app.get('/search/keyword', async (req, res) => {
  try {
    const q = req.query.q as string;
    if (!q) {
      res.status(400).json({ error: 'Missing query parameter "q"' });
      return;
    }
    const limit = parseInt(req.query.limit as string) || 10;
    const docSet = req.query.doc_set as string | undefined;
    const results = await keywordSearch(q, limit, docSet);
    res.json({ results });
  } catch (err: any) {
    console.error('Keyword search error:', err);
    res.status(500).json({ error: err.message });
  }
});

app.get('/backlinks', (req, res) => {
  try {
    const file = req.query.file as string;
    if (!file) {
      res.status(400).json({ error: 'Missing query parameter "file"' });
      return;
    }
    const links = getBacklinks(file);
    res.json({ links });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/links', (req, res) => {
  try {
    const file = req.query.file as string;
    if (!file) {
      res.status(400).json({ error: 'Missing query parameter "file"' });
      return;
    }
    const links = getOutgoingLinks(file);
    res.json({ links });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/index', (req, res) => {
  const docSet = (req.query.doc_set as string) || 'hass-developer';
  const root = findProjectRoot();
  const docPath = join(root, 'docs', docSet);

  if (isIndexing()) {
    res.json({ status: 'already_indexing' });
    return;
  }

  // Fire-and-forget indexing
  indexDocSet(docPath, docSet).catch((err) => {
    console.error('Background indexing error:', err);
  });

  res.json({ status: 'indexing_started', doc_set: docSet });
});

app.get('/stats', (_req, res) => {
  try {
    const db = getDb();
    const fileCount = (db.prepare('SELECT COUNT(*) as count FROM files').get() as any).count;
    const chunkCount = (db.prepare('SELECT COUNT(*) as count FROM chunks').get() as any).count;
    const linkCount = (db.prepare('SELECT COUNT(*) as count FROM links').get() as any).count;
    res.json({
      total_files: fileCount,
      total_chunks: chunkCount,
      total_links: linkCount,
      indexing_in_progress: isIndexing(),
      embedding_model_ready: isReady(),
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Start the server
async function start() {
  const root = findProjectRoot();
  console.log(`Project root: ${root}`);

  // Initialize database
  initDb();

  // Start server on dynamic port
  const server = app.listen(0, () => {
    const addr = server.address();
    if (!addr || typeof addr === 'string') {
      console.error('Failed to get server address');
      process.exit(1);
    }

    const port = addr.port;
    console.log(`Docs search service listening on port ${port}`);

    // Write port and PID files
    writePortFile(port);
    writePidFile();

    // Start background tasks
    warmup().catch((err) => {
      console.error('Model warmup error:', err);
    });

    // Auto-index after model is ready
    const docPath = join(root, 'docs', 'hass-developer');
    warmup().then(() => {
      console.log('Starting initial indexing...');
      return indexDocSet(docPath, 'hass-developer');
    }).catch((err) => {
      console.error('Initial indexing error:', err);
    });
  });

  // Handle graceful shutdown
  const shutdown = () => {
    console.log('Shutting down...');
    server.close(() => {
      cleanup();
      process.exit(0);
    });
    // Force exit after 5s
    setTimeout(() => {
      cleanup();
      process.exit(1);
    }, 5000);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

start().catch((err) => {
  console.error('Fatal startup error:', err);
  process.exit(1);
});
