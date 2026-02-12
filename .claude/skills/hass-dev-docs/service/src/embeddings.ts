import { pipeline, env, type FeatureExtractionPipeline } from '@huggingface/transformers';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const MODELS_DIR = join(__dirname, '..', 'data', 'models');

// Cache models locally
env.cacheDir = MODELS_DIR;

const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';

let extractor: FeatureExtractionPipeline | null = null;
let loading = false;
let ready = false;

async function getExtractor(): Promise<FeatureExtractionPipeline> {
  if (extractor) return extractor;
  if (loading) {
    // Wait for ongoing load
    while (loading) {
      await new Promise(r => setTimeout(r, 100));
    }
    if (extractor) return extractor;
  }

  loading = true;
  try {
    console.log(`Loading embedding model ${MODEL_NAME}...`);
    extractor = await (pipeline as any)('feature-extraction', MODEL_NAME, {
      dtype: 'fp32',
    }) as FeatureExtractionPipeline;
    ready = true;
    console.log('Embedding model loaded successfully.');
    return extractor;
  } catch (err) {
    console.error('Failed to load embedding model:', err);
    throw err;
  } finally {
    loading = false;
  }
}

export async function embed(texts: string[]): Promise<Float32Array[]> {
  const ext = await getExtractor();
  const output = await ext(texts, { pooling: 'mean', normalize: true });
  const dims = 384;
  const results: Float32Array[] = [];

  for (let i = 0; i < texts.length; i++) {
    const start = i * dims;
    const slice = output.data.slice(start, start + dims);
    results.push(new Float32Array(slice));
  }

  return results;
}

export function isReady(): boolean {
  return ready;
}

// Pre-warm the model
export async function warmup(): Promise<void> {
  await getExtractor();
}
