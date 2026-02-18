/**
 * Styles store — manages writing style profiles and their samples.
 * Uses Svelte 5 runes for reactivity.
 */

import { BASE_API_URL } from '$lib/config';

export interface WritingStyle {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface StyleSample {
  id: number;
  title: string;
  content: string;
  source_type: 'paste' | 'upload';
  word_count: number;
  created_at: string;
}

export interface StyleDetail extends WritingStyle {
  samples: StyleSample[];
}

class StylesStore {
  styles = $state<WritingStyle[]>([]);
  loading = $state(false);
  currentStyle = $state<StyleDetail | null>(null);
  currentStyleLoading = $state(false);

  async loadStyles(): Promise<void> {
    this.loading = true;
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles`);
      this.styles = await res.json();
    } catch {
      // Silently fail
    } finally {
      this.loading = false;
    }
  }

  async createStyle(name: string, description: string): Promise<WritingStyle | null> {
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      const style: WritingStyle = await res.json();
      this.styles = [style, ...this.styles];
      return style;
    } catch {
      return null;
    }
  }

  async loadStyle(id: number): Promise<void> {
    this.currentStyleLoading = true;
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles/${id}`);
      this.currentStyle = await res.json();
    } catch {
      // Silently fail
    } finally {
      this.currentStyleLoading = false;
    }
  }

  async updateStyle(id: number, name?: string, description?: string): Promise<void> {
    const body: Record<string, string> = {};
    if (name !== undefined) body.name = name;
    if (description !== undefined) body.description = description;
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const updated = await res.json();
      this.styles = this.styles.map((s) => (s.id === id ? { ...s, ...updated } : s));
      if (this.currentStyle?.id === id) {
        this.currentStyle = { ...this.currentStyle, ...updated };
      }
    } catch {
      // Silently fail
    }
  }

  async deleteStyle(id: number): Promise<void> {
    try {
      await fetch(`${BASE_API_URL}/api/styles/${id}`, { method: 'DELETE' });
      this.styles = this.styles.filter((s) => s.id !== id);
      if (this.currentStyle?.id === id) {
        this.currentStyle = null;
      }
    } catch {
      // Silently fail
    }
  }

  async addSample(styleId: number, title: string, content: string): Promise<void> {
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles/${styleId}/samples`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      if (res.ok && this.currentStyle?.id === styleId) {
        await this.loadStyle(styleId);
      }
    } catch {
      // Silently fail
    }
  }

  async uploadSample(styleId: number, file: File): Promise<void> {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${BASE_API_URL}/api/styles/${styleId}/samples/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok && this.currentStyle?.id === styleId) {
        await this.loadStyle(styleId);
      }
    } catch {
      // Silently fail
    }
  }

  async deleteSample(styleId: number, sampleId: number): Promise<void> {
    try {
      await fetch(`${BASE_API_URL}/api/styles/${styleId}/samples/${sampleId}`, {
        method: 'DELETE',
      });
      if (this.currentStyle?.id === styleId) {
        this.currentStyle = {
          ...this.currentStyle,
          samples: this.currentStyle.samples.filter((s) => s.id !== sampleId),
        };
      }
    } catch {
      // Silently fail
    }
  }

  clearCurrent(): void {
    this.currentStyle = null;
  }
}

export const styles = new StylesStore();
