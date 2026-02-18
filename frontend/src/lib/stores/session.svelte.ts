/**
 * Session state store — tracks current screen, session data, and workflow state.
 * Uses Svelte 5 runes for reactivity.
 */

export type Screen = 'task' | 'interview' | 'drafts' | 'focus';
export type AppView = 'session' | 'styles' | 'style_editor';

export interface SessionSummary {
  id: number;
  task_type: string;
  topic: string;
  status: string;
  draft_count: number;
  max_round: number;
  created_at: string;
}

export interface ThoughtBlock {
  assessment: string;
  missing: string[];
  sufficient: boolean;
}

export interface SearchInfo {
  query: string;
  summary: string;
}

export interface ChatMessage {
  role: 'user' | 'ai' | 'thought' | 'status' | 'search';
  content: string;
  thought?: ThoughtBlock;
  search?: SearchInfo;
}

class SessionStore {
  screen = $state<Screen>('task');
  appView = $state<AppView>('session');
  currentSessionId = $state<number | null>(null);
  sessionList = $state<SessionSummary[]>([]);
  sessionsLoading = $state(false);
  taskType = $state('');
  topic = $state('');
  messages = $state<ChatMessage[]>([]);
  readyToDraft = $state(false);
  draftSummary = $state('');
  keyMaterial = $state<string[]>([]);

  startInterview(taskType: string, topic: string): void {
    this.taskType = taskType;
    this.topic = topic;
    this.messages = [];
    this.readyToDraft = false;
    this.screen = 'interview';
  }

  addMessage(msg: ChatMessage): ChatMessage {
    this.messages = [...this.messages, msg];
    // Return the reactive proxy (last element of the $state array)
    return this.messages[this.messages.length - 1];
  }

  setReadyToDraft(summary: string, keyMaterial: string[]): void {
    this.readyToDraft = true;
    this.draftSummary = summary;
    this.keyMaterial = keyMaterial;
  }

  goToDrafts(): void {
    this.screen = 'drafts';
  }

  goToFocus(): void {
    this.screen = 'focus';
  }

  reset(): void {
    this.screen = 'task';
    this.taskType = '';
    this.topic = '';
    this.messages = [];
    this.readyToDraft = false;
    this.draftSummary = '';
    this.keyMaterial = [];
    this.currentSessionId = null;
  }

  setAppView(view: AppView): void {
    this.appView = view;
  }

  async loadSessions(): Promise<void> {
    const { BASE_API_URL } = await import('$lib/config');
    this.sessionsLoading = true;
    try {
      const res = await fetch(`${BASE_API_URL}/api/sessions`);
      this.sessionList = await res.json();
    } catch {
      // Silently fail
    } finally {
      this.sessionsLoading = false;
    }
  }
}

export const session = new SessionStore();
