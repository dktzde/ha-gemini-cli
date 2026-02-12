export interface FileRecord {
  id: number;
  file_path: string;
  doc_set: string;
  content_hash: string;
  title: string | null;
  last_indexed_at: string;
}

export interface Chunk {
  id: number;
  file_id: number;
  section_heading: string | null;
  chunk_text: string;
  position: number;
}

export interface Link {
  id: number;
  source_file: string;
  target_file: string;
  link_text: string | null;
  section: string | null;
}

export interface SearchResult {
  chunk_text: string;
  section_heading: string | null;
  file_path: string;
  title: string | null;
  score: number;
}

export interface IndexStats {
  total_files: number;
  total_chunks: number;
  total_links: number;
  indexing_in_progress: boolean;
  last_indexed_doc_set: string | null;
}

export interface DocSetConfig {
  name: string;
  base_path: string;
}
