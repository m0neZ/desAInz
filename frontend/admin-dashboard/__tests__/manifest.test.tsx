import fs from 'fs';
import path from 'path';
import { metadata } from '../app/layout';

describe('PWA manifest', () => {
  it('metadata references manifest file', () => {
    expect(metadata.manifest).toBe('/manifest.json');
  });

  it('file exists in public directory', () => {
    const manifestPath = path.join(process.cwd(), 'public', 'manifest.json');
    expect(fs.existsSync(manifestPath)).toBe(true);
  });
});
